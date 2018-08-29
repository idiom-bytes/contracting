'''
This module is a (mostly) redis-py compatible library.
* Unlike redis-py, the backend is configurable, it could write to a Redis, it
  could save the data locally.
* It generates resp command objects that are run by the backend
* It doesn't return values for incrby so incr, incrby, decr, and decrby are pure writes.
* Append doesn't return a string length; same reasoning as incrby.

Reference API: https://github.com/andymccurdy/redis-py/blob/master/redis/client.py
'''

from seneca.engine.storage.redisnap.commands import *
import seneca.engine.storage.redisnap.resp_types as resp_types

class Client:
    '''
    Implementation of the API provided by redis-py's StrictRedis
    '''

    def __init__(self, executer):
        self.execute_command = executer

    def exists(self, name):
        """
        Returns a boolean indicating whether key ``name`` exists
        >>> c.exists('foo')
        Exists('foo')
        """
        return self.execute_command(Exists(name))
    __contains__ = exists

    def type(self, name):
        """
        Returns the type of key ``name``
        >> c.purge()
        >> c.type('foo')
        b'none'
        """

        rtype = self.execute_command(Type(name))
        #resp_types.

        return rtype
        if isinstance(rtype, RScalar):
            return str.encode('string')
        elif isinstance(rtype, RHash):
            return str.encode('hash')
        else:
            raise NotImplementedError()


    def append_wo(self, key, value):
        """
        Appends the string ``value`` to the value at ``key``. If ``key``
        doesn't already exist, create it with a value of ``value``.
        Returns the new length of the value at ``key``.

        >> c.append('foo', 'bar')
        <RESP (Append) {'key': 'foo', 'value': 'bar'}>
        """
        return self.execute_command(Append(key, value))


    def get(self, name):
        """
        Return the value at key ``name``, or None if the key doesn't exist
        >> c.get('foo')
        <RESP (Get) {'key': 'foo'}>
        """
        # TODO: Decide how we want to handle non-existing keys in the commands api
        return self.execute_command(Get(name))

    def __getitem__(self, name):
        """
        Return the value at key ``name``, raises a KeyError if the key
        doesn't exist.

        >> try:
        ...     c['foo']
        ... except Exception as e:
        ...     print(e)
        <RESP (Get) {'key': 'foo'}>
        'foo'
        """
        value = self.get(name)
        if value is not None:
            return value
        raise KeyError(name)

    def set(self, name, value, ex=None, px=None, nx=False, xx=False):
        """
        >> c.set('foo', 'bar')
        <RESP (Set) {'key': <RESP ADDRESS (ScalarAddress) {'key': 'foo'}>, 'value': <RESP (RScalar) {'value': 'bar'}>}>

        >> s.set('foo', 'bar')

        Set the value at key ``name`` to ``value``
        ``ex`` sets an expire flag on key ``name`` for ``ex`` seconds.
        ``px`` sets an expire flag on key ``name`` for ``px`` milliseconds.
        ``nx`` if set to True, set the value at key ``name`` to ``value`` only
            if it does not exist.
        ``xx`` if set to True, set the value at key ``name`` to ``value`` only
            if it already exists.
        """
        assert ex is None, 'Cache expiration not supported'
        assert px is None, 'Cache expiration not supported'
        assert nx is False # TODO: Will add this later
        assert nx is False # TODO: Will add this later

        self.execute_command(Set(ScalarAddress(name), resp_types.make_rscalar(value)))


    def __setitem__(self, name, value):
        """
        >> c['foo'] = 'bar'
        """
        self.set(name, value)


    def incr_wo(self, name, amount=1):
        """
        Increments the value of ``key`` by ``amount``.  If no key exists,
        the value will be initialized as ``amount``
        >> c.incr('foo', 1)
        """
        self.execute_command(IncrBy(ScalarAddress(name), amount))


    def incrby_wo(self, name, amount=1):
        """
        Increments the value of ``key`` by ``amount``.  If no key exists,
        the value will be initialized as ``amount``
        >> s.incrby('foo', 1)
        """
        self.execute_command(IncrBy(ScalarAddress(name), amount))

    def decr_wo(self, name, amount=1):
        """
        Decrements the value of ``key`` by ``amount``.  If no key exists,
        the value will be initialized as 0 - ``amount``
        >> c.decr('foo', 1)
        """
        self.execute_command(IncrBy(ScalarAddress(name), 0 - amount))

    def hget(self, name, key):
        """
        >> c.hget('foo', 'bar')
        """
        return self.execute_command(HGet(RHashFieldAddress(name, key)))

    def hset_wo(self, name, key, value):
        """
        >> c.hset('foo', 'bar', 'baz')
        """
        self.execute_command(HSet(RHashFieldAddress(name, key), resp_types.make_rscalar(value)))


def run_tests(deps_provider):
    '''
    '''
    import seneca.engine.storage.redisnap.local_backend as lb

    c = Client(executer = print)
    s = Client(executer = lb.Executer())

    import doctest, sys
    return doctest.testmod(sys.modules[__name__], extraglobs={**locals()})
