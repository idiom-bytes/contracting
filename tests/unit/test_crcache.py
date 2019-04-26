import unittest
import sys
import glob
import time
from seneca.interpreter.module import DatabaseFinder
from seneca.db.cr.cache import CRCache, Macros
from seneca.execution.executor import Executor
from seneca.db.driver import ContractDriver
from seneca.db.cr.transaction_bag import TransactionBag

class PayloadStub():
    def __init__(self, sender):
        self.sender = sender

class TransactionStub():
    def __init__(self, sender, contract_name, func_name, kwargs):
        self.payload = PayloadStub(sender)
        self.contract_name = contract_name
        self.func_name = func_name
        self.kwargs = kwargs


driver = ContractDriver(db=0)
#unittest.TestLoader.sortTestMethodsUsing = None


class TestSingleCRCache(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        num_sbb = 1
        self.master_db = ContractDriver()
        executor = Executor()
        self.author = 'unittest'
        sys.meta_path.append(DatabaseFinder)
        driver.flush()
        contracts = glob.glob('./test_sys_contracts/*.py')
        for contract in contracts:
            name = contract.split('/')[-1]
            name = name.split('.')[0]

            with open(contract) as f:
                code = f.read()

            driver.set_contract(name=name, code=code, author=self.author)
            driver.commit()
        tx1 = TransactionStub(self.author, 'module_func', 'test_func', {'status': 'Working'})
        tx2 = TransactionStub(self.author, 'module_func', 'test_func', {'status': 'AlsoWorking'})
        self.bag = TransactionBag([tx1, tx2])
        self.cache = CRCache(idx=0, master_db=self.master_db, sbb_idx=0,
                             num_sbb=num_sbb, executor=executor)

    @classmethod
    def tearDownClass(self):
        self.cache.db.flush()
        self.master_db.flush()
        del self.cache
        sys.meta_path.remove(DatabaseFinder)
        driver.flush()

    def test_0_set_bag(self):
        self.cache.set_bag(self.bag)

        self.assertEqual(self.cache.state, 'BAG_SET')

    def test_1_execute(self):
        self.cache.execute()
        results = self.cache.get_results()

        self.assertEqual(results[0][0], 0)
        self.assertEqual(results[0][1], 'Working')
        self.assertEqual(results[1][0], 0)
        self.assertEqual(results[1][1], 'AlsoWorking')
        self.assertEqual(self.cache.state, 'EXECUTED')

        self.assertEqual(0, self.cache._check_macro_key(Macros.CONFLICT_RESOLUTION))
        self.assertEqual(0, self.cache._check_macro_key(Macros.RESET))
        self.assertEqual(1, self.cache._check_macro_key(Macros.EXECUTION))

    def test_2_cr(self):
        self.cache.sync_execution()
        self.assertEqual(self.cache.state, 'EXECUTED')

        self.cache.set_top_of_stack()
        self.cache.sync_execution()
        self.assertEqual(self.cache.state, 'COMMITTED')

    def test_3_merge_ready(self):
        self.cache.sync_merge_ready()
        self.assertEqual(self.cache.state, 'READY_TO_MERGE')

    def test_4_merged(self):
        self.cache.merge()
        self.assertEqual(self.cache.state, 'RESET')

    def test_5_clean(self):
        self.cache.sync_reset()
        self.assertEqual(self.cache.state, 'CLEAN')



if __name__ == "__main__":
    unittest.main()
