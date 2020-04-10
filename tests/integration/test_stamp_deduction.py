from unittest import TestCase
from contracting.db.driver import ContractDriver
from contracting.execution.executor import Executor
from contracting.config import STAMPS_PER_TAU
from contracting.execution import runtime
import contracting


def submission_kwargs_for_file(f):
    # Get the file name only by splitting off directories
    split = f.split('/')
    split = split[-1]

    # Now split off the .s
    split = split.split('.')
    contract_name = split[0]

    with open(f) as file:
        contract_code = file.read()

    return {
        'name': contract_name,
        'code': contract_code,
    }


TEST_SUBMISSION_KWARGS = {
    'sender': 'stu',
    'contract_name': 'submission',
    'function_name': 'submit_contract'
}


class TestMetering(TestCase):
    def setUp(self):
        # Hard load the submission contract
        self.d = ContractDriver()
        self.d.flush()

        with open(contracting.__path__[0] + '/contracts/submission.s.py') as f:
            contract = f.read()

        self.d.set_contract(name='submission',
                            code=contract)
        self.d.commit()

        # Execute the currency contract with metering disabled
        self.e = Executor(driver=self.d)
        self.e.execute(**TEST_SUBMISSION_KWARGS,
                       kwargs=submission_kwargs_for_file('./test_contracts/currency.s.py'), metering=False)

    def tearDown(self):
        self.d.flush()

    def test_simple_execution_deducts_stamps(self):
        prior_balance = self.d.get('currency.balances:stu')

        output = self.e.execute('stu', 'currency', 'transfer', kwargs={'amount': 100, 'to': 'colin'})

        new_balance = self.d.get('currency.balances:stu')

        self.assertEqual(float(prior_balance - new_balance - 100), output['stamps_used'] / STAMPS_PER_TAU)

    def test_too_few_stamps_fails_and_deducts_properly(self):
        prior_balance = self.d.get('currency.balances:stu')

        small_amount_of_stamps = 1 * STAMPS_PER_TAU

        output = self.e.execute('stu', 'currency', 'transfer', kwargs={'amount': 100, 'to': 'colin'},
                                                stamps=small_amount_of_stamps)

        new_balance = self.d.get('currency.balances:stu')

        self.assertEqual(float(prior_balance - new_balance), output['stamps_used'] / STAMPS_PER_TAU)

    def test_adding_too_many_stamps_throws_error(self):
        prior_balance = self.d.get('currency.balances:stu')
        too_many_stamps = (prior_balance + 1000) * STAMPS_PER_TAU

        #too_many_stamps = 2147483648

        with self.assertRaises(AssertionError):
            output = self.e.execute('stu', 'currency', 'transfer', kwargs={'amount': 100, 'to': 'colin'},
                                                    stamps=too_many_stamps)

    def test_adding_all_stamps_with_infinate_loop_eats_all_balance(self):
        self.d.set('currency.balances:stu', 500)
        self.d.commit()

        prior_balance = self.d.get('currency.balances:stu')

        prior_balance *= STAMPS_PER_TAU

        output = self.e.execute(
            **TEST_SUBMISSION_KWARGS,
            kwargs=submission_kwargs_for_file('./test_contracts/inf_loop.s.py'),
            stamps=prior_balance,
            metering=True
        )

        new_balance = self.d.get('currency.balances:stu')

        print(new_balance)

        # Not all stamps will be deducted because it will blow up in the middle of execution
        self.assertTrue(new_balance < 0.01)

    def test_submitting_contract_succeeds_with_enough_stamps(self):
        prior_balance = self.d.get('currency.balances:stu')

        print(prior_balance)

        output = self.e.execute(**TEST_SUBMISSION_KWARGS,
                                                kwargs=submission_kwargs_for_file('./test_contracts/erc20_clone.s.py'),
                                                )
        print(output)

        new_balance = self.d.get('currency.balances:stu')

        print(new_balance)

        self.assertEqual(float(prior_balance - new_balance), output['stamps_used'] / STAMPS_PER_TAU)

    def test_non_smart_contract_uses_no_stamps(self):
        runtime.rt.set_up(stmps=100, meter=True)

        a = 123
        while a > 0:
            a -= 1

        runtime.rt.tracer.stop()

        stamps_used = runtime.rt.tracer.get_stamp_used()

        runtime.rt.tracer.reset()

        self.assertEqual(stamps_used, 0)

    def test_smart_contract_uses_stamps(self):
        runtime.rt.set_up(stmps=1000, meter=True)

        globals()['__contract__'] = True
        a = 123
        while a > 0:
            a -= 1

        runtime.rt.tracer.stop()

        stamps_used = runtime.rt.tracer.get_stamp_used()

        runtime.rt.tracer.reset()

        self.assertGreater(stamps_used, 0)
