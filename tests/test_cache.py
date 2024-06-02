# test cases

# get some data, then verify we have it later, then remove it

# alternetly, make a testCachePath that you only make on testing


from multicall.cache import isCached
from helpers import weth_bal
from multicall.constants import TEST_CACHE_PATH

import pytest

def test_cached_something_successfully():
    assert True
    a = 10
    pass

    assert not isCached(weth_bal, 18_000_000, TEST_CACHE_PATH)
