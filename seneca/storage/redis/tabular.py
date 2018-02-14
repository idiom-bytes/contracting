"""
Seneca's redis tabular provides a SQLesce interface with redis as the storage
backend.

TODOs:
Method chains to support:

* select('wallet_id').where(wallet_id=wallet_id).run())
* update(balance=old_balance + amount_to_add).where(wallet_id=wallet_id).run()
* insert(wallet_id=wallet_id, balance=0)

Redis notes:
* Use transactions
* Do Lua script generation
* Prevent eviction of stuff we need to always be available (figure which stuff we need)
* We need to restrict access between address spaces so contracts can't alter
  other contracts' dbs

"""
import redis
import json
#import seneca.state as st


class Column(object):
    def __init__(self, name, data_type, unique_and_indexed=False):
        # Do we have primary IDs
        # Do we default do an autogenerated if no uai, or else use uai as primary?
        self.name = name
        self.data_type = data_type.__name__ # TODO: do this properly
        self.uai = unique_and_indexed
    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__,
            sort_keys=True, indent=4)

    def __str__(self):
        return self.to_json()


class Table(object):
    def __init__(self, name, column_list):
        self.name = name
        self.column_names = [x.name for x in column_list]
        self.indexed_column_names = [x.name for x in column_list if x.uai]


    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__,
            sort_keys=True, indent=4)


    def create_in_db(self):
        # Create metadata
        # addr:__table:(table_name):__metadata: (json serialized table description)

        # Create indices with placeholder vals, not Redis deletes empty hashes
        # addr:__table:(table_name):__index:customer_id:{map customer_id:__id}
        # addr:__table:(table_name):__index:email_address:{map customer_id:__id}
        # addr:__table:(table_name):__rows:{map __id:json}
        pass

    def insert_row(self):
        # Add row
        # Add to all indices

        pass

    # NOTE: query constraints in 'where clause' need to be separated if the are or are not not indexed,
    # indexed ones result in redis queries to narrow the total.


    def __str__(self):
        return self.to_json()


def create_table(*args, **kwargs):
    t = Table(*args, **kwargs)
    # write to redis



    return t


if __name__ == '__main__':
    print('\n\nTesting Redis Tabular...')
    #Todo: replace this with Seneca state import value
    rt_state=lambda:None
    rt_state.call_chain = [lambda:None]
    rt_state.call_chain[0].public_key = b' \x01\xe9\x01\xa2,\xa9\x9bjmi\xabx\xd1\\\x83V\xa2\x7f\x16\x9a\xc1\x05\xc8[&\x80\xdf\xd2\xf1\xf1\xb7\xca\x80\xfa['

    # Todo: Create real connection method
    redis_db = redis.StrictRedis(host="localhost", port=6379, db=0)

    t = create_table('test_table', [
        Column('first_name', str),
        Column('last_name', str),
        Column('email_address', str, True),
        Column('customer_id', str, True),
        Column('account_balance', int),
        # Implicit ID
    ])

    print(t)

'''
What do we create?
table record with this info?
'''



primary_test_wallet = b' \x01\xe9\x01\xa2,\xa9\x9bjmi\xabx\xd1\\\x83V\xa2\x7f\x16\x9a\xc1\x05\xc8[&\x80\xdf\xd2\xf1\xf1\xb7\xca\x80\xfa['

# XXX: This is a very ugly hack to put off writing this lib until the basic parser/module loader is done.

class Stub(object):
    def __init__(self): # this method creates the class object.
        self.call_stack = []

    def __getattr__(self, name):
        self.call_stack.append(name)
        return self
    def __call__(self, *args, **kwargs):
        self.call_stack.append((args,kwargs))

        if self.call_stack == [
          'select', (('wallet_id',), {}),
          'where', ((), {'wallet_id': primary_test_wallet}),
          'run', ((), {})
        ]:
            return False
        elif self.call_stack == [
          'select', (('wallet_id',), {}),
          'where', ((), {'wallet_id': primary_test_wallet}),
          'run', ((), {}),
          'insert', ((),{'wallet_id': primary_test_wallet, 'balance': 0}),
          'select', (('wallet_id',), {}),
          'where', ((), {'wallet_id': primary_test_wallet}),
          'run', ((), {}),
          'select', (('balance',), {}),
          'where', ((), {'wallet_id': primary_test_wallet}),
          'run', ((), {})]:
            return [5]
        else:
            #print(self.call_stack)
            pass

        return self

stub = Stub()


def create_table(table_name, column_spec):
    return stub


def get_table(table_name):
    return stub


def column(*args, **kwargs):
    pass
