# test cases

# get some data, then verify we have it later, then remove it

# alternetly, make a testCachePath that you only make on testing



from multicall.multicall import Multicall
from multicall.cache import isCached
from multicall.call import Call
from helpers import weth_bal
from multicall.constants import W3
import pytest


def test_cached_something_successfully():

    print("asdfasdf")

    # make this calla nd assert that it is cached

    assert not isCached(weth_bal, 18_000_000)


    




