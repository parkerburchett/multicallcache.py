# test cases

# get some data, then verify we have it later, then remove it

# alternetly, make a testCachePath that you only make on testing


from multicall.cache import isCached
from helpers import weth_bal


def test_cached_something_successfully():

    print("asdfasdf")

    # make this calla nd assert that it is cached

    assert not isCached(weth_bal, 18_000_000)
