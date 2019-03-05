from unittest import TestCase
import redis, unittest
from seneca.constants.config import MASTER_DB, REDIS_PORT
from seneca.libs.storage.datatypes import Hash
from seneca.libs.storage.table import Table, Property
from seneca.engine.interpreter.parser import Parser
from decimal import Decimal


class Executor:
    def __init__(self):
        self.driver = redis.StrictRedis(host='localhost', port=REDIS_PORT, db=MASTER_DB)
        self.driver.flushall()
        Parser.executor = self
        Parser.parser_scope = {
            'rt': {
                'contract': 'sample',
                'sender': 'falcon',
                'author': '__lamden_io__'
            }
        }


class TestDataTypes(TestCase):

    def setUp(self):
        self.contract_id = self.id().split('.')[-1]
        self.ex = Executor()
        Parser.parser_scope['rt']['contract'] = self.contract_id
        Table.schemas = {}
        print('#'*128)
        print('\t', self.contract_id)
        print('#'*128)

    def test_map(self):
        balances = Hash('balances')
        balances['hr'] = Hash('hr')
        self.assertEqual(repr(balances['hr']), 'Hash:__main__:balances:hr')

    def test_map_simple(self):
        balances = Hash('balances')
        balances['hr']['employees']['stu'] = 100
        self.assertEqual(balances['hr']['employees']['stu'], 100)

    def test_map_nested(self):
        balances = Hash('balances')
        hooter = Hash('hoot')
        hooter['res'] = 1234
        balances['hr'] = Hash('hr')
        balances['hr']['hey'] = hooter
        self.assertEqual(balances['hr']['hey']['res'], 1234)

    def test_map_nested_different_type(self):
        Coin = Table('Coin', {
            'name': Property(str, required=True),
            'purpose': str,
        })
        tau = Coin.add_row('tau', 'something')
        balances = Hash('balances')
        balances['hr']['hey'] = tau
        self.assertEqual(balances['hr']['hey'].schema, Coin.schema)
        self.assertEqual(balances['hr']['hey'].data, ['tau', 'something'])
        self.assertEqual(balances['hr']['hey'].name, 'tau')
        self.assertEqual(balances['hr']['hey'].purpose, 'something')

    def test_table_append(self):
        Coin = Table('Coin', {
            'name': Property(str, required=True),
            'purpose': str,
            'price': int
        })
        Coin.add_row('tau', purpose='anarchy net')
        Coin.add_row(purpose='anarchy net', name='stubucks', price=1)
        Coin.add_row('falcoin', 'anarchy net')

        self.assertEqual(Coin.count, 3)

    def test_table_indexed(self):
        Coin = Table('Coin', {
            'name': Property(str, required=True, indexed=True),
            'purpose': str,
            'price': int
        })
        Coin.add_row('faltau', purpose='anarchy net')
        Coin.add_row(purpose='anarchy net', name='stubucks', price=1)
        Coin.add_row('falcoin', 'anarchy net')

        self.assertEqual(Coin.find({'$property': 'name', '$exactly': 'faltau'}), [['faltau', 'anarchy net', 0.0]])
        self.assertEqual(sorted(Coin.find({'$property': 'name', '$matches': 'fal*'})), sorted([['faltau', 'anarchy net', 0.0], ['falcoin', 'anarchy net', 0.0]]))

    def test_table_with_table_as_type(self):
        Coin = Table('Coin', {
            'name': Property(str, required=True),
            'purpose': Property(str, default='anarchy net')
        })
        Company = Table('Company', {
            'name': str,
            'coin': Coin,
            'evaluation': int
        })
        tau = Coin.add_row('tau')
        lamden = Company.add_row('lamden', coin=tau, evaluation=0)
        self.assertEqual(repr(tau), 'Table:__main__:Coin')
        self.assertEqual(repr(lamden), 'Table:__main__:Company')

    def test_table_with_invalid_table_type(self):
        Coin = Table('Coin', {
            'name': Property(str, True),
            'purpose': Property(str, False, '')
        })
        Fake = Table('Fake', {
            'name': Property(str, True),
            'purpose': Property(str, False, '')
        })
        Company = Table('Company', {
            'name': Property(str),
            'coin': Property(Coin),
            'evaluation': Property(int)
        })
        fake_tau = Fake.add_row('tau', 'anarchy net')
        with self.assertRaises(AssertionError) as context:
            lamden = Company.add_row('lamden', coin=fake_tau, evaluation=0)

    def test_table_delete(self):
        Coin = Table('Coin', {
            'name': Property(str, required=True, indexed=True),
            'purpose': str,
            'price': int
        })
        Coin.add_row('faltau', purpose='anarchy net')
        Coin.add_row(purpose='anarchy net', name='stubucks', price=1)
        Coin.add_row('falcoin', 'anarchy net')
        Coin.delete_table()
        for item in self.ex.driver.keys():
            self.assertFalse(item.decode().startswith(Coin.key))

    def test_delete_row(self):
        Coin = Table('Coin', {
            'name': Property(str, required=True, indexed=True),
            'purpose': str,
            'price': int
        })
        Coin.add_row('faltau', purpose='anarchy net', price=6)
        Coin.add_row(purpose='anarchy net', name='stubucks', price=1)
        Coin.add_row('falcoin', 'anarchy net', price=5)
        Coin.add_row('falcore', 'anarchy net', price=4)
        Coin.add_row('falcone', 'anarchy net', price=41)
        Coin.delete({'$property': 'name', '$matches': 'falco*'})
        self.assertEqual(Coin.count, 2)

    def test_update_row(self):
        Coin = Table('Coin', {
            'name': Property(str, required=True, indexed=True),
            'purpose': str,
            'price': int
        })
        Coin.add_row('faltau', purpose='anarchy net', price=6)
        Coin.update({'$property': 'name', '$exactly': 'faltau'}, {
            'price': 12
        })
        self.assertEqual(Coin.find({'$property': 'name', '$exactly': 'faltau'}), [['faltau', 'anarchy net', 12]])

    # def test_table_with_sorted_column(self):
    #     Coin = Table('Coin', {
    #         'name': Property(str, primary_key=True),
    #         'purpose': str,
    #         'price': Property(int, sort=True)
    #     })
    #     Coin.add_row('faltau', purpose='anarchy net', price=6)
    #     Coin.add_row(purpose='anarchy net', name='stubucks', price=10)
    #     Coin.add_row('falcoin', 'anarchy net', price=100)


if __name__ == '__main__':
    unittest.main()
