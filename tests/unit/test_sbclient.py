from unittest import TestCase
from seneca.execution.executor import Executor
from seneca.db.cr.client import SubBlockClient
from seneca.db.driver import ContractDriver
from seneca.logger import get_logger
import asyncio, glob
from typing import List


class PayloadStub:
    def __init__(self, sender):
        self.sender = sender


class TransactionStub:
    def __init__(self, sender, contract_name, func_name, kwargs):
        self.payload = PayloadStub(sender)
        self.contract_name = contract_name
        self.func_name = func_name
        self.kwargs = kwargs


driver = ContractDriver(db=0)
MINT_WALLETS = {
    'anonymoose': 10000,
    'stu': 69,
    'birb': 8000,
    'ghu': 9000,
    'tj': 8000,
    'ethan': 8000
}


class TestSBClient(TestCase):

    def setUp(self):
        # Add submission contract
        self.author = 'unittest'
        with open('../../seneca/contracts/submission.s.py') as f:
            contract = f.read()

        driver.set_contract(name='submission',
                            code=contract,
                            author='sys')
        driver.commit()

        # Use executor submit
        e = Executor()
        contracts = glob.glob('./test_sys_contracts/*.py')
        for contract in contracts:
            name = contract.split('/')[-1]
            name = name.split('.')[0]

            with open(contract) as f:
                code = f.read()

            e.execute(sender=self.author, contract_name='submission', function_name='submit_contract',
                      kwargs={'name': name, 'code': code})

        num_clients = 2
        self.clients = []
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        for i in range(num_clients):
            self.clients.append(SubBlockClient(i, num_clients, self.loop))

    def tearDown(self):
        driver.flush()
        for client in self.clients:
            client.flush_all()

    def run_loop(self, period=1):
        async def run():
            await asyncio.sleep(period)

        self.loop.run_until_complete(run())

    def test_some_conflicts(self):
        def _assert_handler1(outputs: List[tuple]):
            self.log.important("handler1: {}".format(outputs))
            pass
            # self.assertEqual(results[0][0], 0)
            # self.assertEqual(results[0][1], 'Working')
            # self.assertEqual(results[1][0], 0)
            # self.assertEqual(results[1][1], 'AlsoWorking')

        def _assert_handler2(outputs: List[tuple]):
            self.log.important("handler2: {}".format(outputs))
            pass

        tx1 = TransactionStub(self.author, 'module_func', 'test_func', {'status': 'tx1_succ'})
        tx2 = TransactionStub(self.author, 'module_func', 'test_func', {'status': 'tx2_succ'})
        tx3 = TransactionStub(self.author, 'module_func', 'test_func', {'status': 'tx3_succ'})
        tx4 = TransactionStub(self.author, 'module_func_bad', 'test_func', {'status': 'tx4_succ'})


        input_hash1 = 'A' * 64
        input_hash2 = 'B' * 64

        self.clients[0].execute_sb(input_hash1, [tx1, tx2], _assert_handler1)
        self.clients[1].execute_sb(input_hash2, [tx3, tx4], _assert_handler2)

        self.run_loop(4)






