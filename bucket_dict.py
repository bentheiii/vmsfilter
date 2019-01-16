from typing import TypeVar, Generic, MutableMapping, Callable, Dict, Set

from random import randint, seed

K = TypeVar('K')
V = TypeVar('V')
CV = TypeVar('CV')


class BucketDict(MutableMapping[K, V], Generic[K, V, CV]):
    def __init__(self, cmp_key: Callable[[V], CV]):
        self.cmp_key: Callable[[V], CV] = cmp_key
        self.buckets: Dict[CV, Dict[K, V]] = {}

    def __contains__(self, item):
        return any(item in b for b in self.buckets.values())

    def __iter__(self):
        for b in self.buckets.values():
            yield from b

    def __len__(self):
        return sum(len(b) for b in self.buckets.values())

    def __setitem__(self, key, value):
        missing = object()
        for c, b in self.buckets.items():
            if b.pop(key, missing) is not missing:
                if not b:
                    del self.buckets[c]
                break
        self.buckets.setdefault(self.cmp_key(value), dict())[key] = value

    def __getitem__(self, item):
        missing = object()
        for sb in self.buckets.values():
            ret = sb.get(item, missing)
            if ret is not missing:
                return ret
        raise KeyError(item)

    def __delitem__(self, key):
        missing = object()
        for c, sb in self.buckets.items():
            ret = sb.pop(key, missing)
            if ret is not missing:
                if not sb:
                    del self.buckets[c]
                return
        raise KeyError(key)

    def highest(self)->V:
        max_key = max(self.buckets, default=None)
        if max_key is None:
            return None
        return next(iter(self.buckets[max_key].values()))

    def __str__(self):
        return str(self.buckets)


def test_bucket():
    seed_ = randint(0, 2 ** 31)
    seed(seed_)
    buckets = BucketDict(lambda a: a // 33)
    control = dict()

    def get_action():
        roll = randint(0, 2)
        key = randint(0, 100)
        value = randint(0, 100)
        if roll == 0:
            def ret(s):
                s[key] = value
        elif roll == 1:
            def ret(s):
                return s.get(key, None)
        elif roll == 2:
            def ret(s):
                return s.pop(key, None)
        else:
            assert False, roll
        return ret

    for _ in range(100_000):
        action = get_action()
        assert action(control) == action(buckets)
        assert control == buckets, str(_) + ', s: ' + str(seed_)
        c_max = max(control.values(), default=None)
        if c_max is None:
            assert buckets.highest() is None
        else:
            assert buckets.highest() // 33 == c_max // 33, f"{buckets.highest() // 10} vs {c_max // 10}"

    print(control)
    print(buckets)


if __name__ == '__main__':
    test_bucket()
