from .execution.executor import Executor
from .ast.compiler import SenecaCompiler
import types
from functools import partial

class AbstractContract:
    def __init__(self, name, signer, environment, executor, funcs):
        self.name = name
        self.signer = signer
        self.environment = environment
        self.executor = executor

        # set up virtual functions
        for f in funcs:
            # unpack tuple packed in SenecaClient
            func, kwargs = f

            # set the kwargs to None. these will fail if they are not provided
            default_kwargs = {}
            for kwarg in kwargs:
                default_kwargs[kwarg] = None

            setattr(self, func, partial(self._abstract_function_call,
                                        signer=self.signer,
                                        contract=self.name,
                                        executor=self.executor,
                                        function=func,
                                        environment=self.environment,
                                        **default_kwargs))

    def _abstract_function_call(self, signer, executor, contract, environment, function, **kwargs):
        for k, v in kwargs.items():
            assert v is not None, 'Keyword "{}" not provided. Must not be None.'.format(k)

        status, result = executor.execute(sender=signer,
                                          contract_name=contract,
                                          function_name=function,
                                          kwargs=kwargs,
                                          environment=environment
                                          )

        if status == 1:
            raise result

        return result


class SenecaClient:
    def __init__(self, signer='sys', executor=Executor(), compiler=SenecaCompiler()):
        self.executor = executor
        self.raw_driver = self.executor.driver
        self.signer = signer
        self.compiler = compiler

    # Returns abstract contract which has partial methods mapped to each exported function.
    def get_contract(self, name):
        contract = self.raw_driver.get_contract(name)
        code = self.compiler.compile(contract, lint=False)

        codes = [cd for cd in code.co_consts if isinstance(cd, types.CodeType)]
        funcs = []
        for _c in codes:
            funcs.append((_c.co_name, _c.co_varnames))

        return AbstractContract(name=name,
                                signer=self.signer,
                                environment={},
                                executor=self.executor,
                                funcs=funcs)
