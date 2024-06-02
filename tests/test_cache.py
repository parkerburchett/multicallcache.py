# test cases

# get some data, then verify we have it later, then remove it

# alternetly, make a testCachePath that you only make on testing


from multicall.cache import isCached
from multicall.multicall import Multicall

from helpers import weth_bal, usdc_bal, refresh_db, TEST_BLOCK
from multicall.constants import TEST_CACHE_PATH, W3


@refresh_db
def test_Call__call__caches_only_finalized_blocks():
    assert not isCached(weth_bal, TEST_BLOCK, TEST_CACHE_PATH)
    weth_bal(W3, 18_000_000, TEST_CACHE_PATH)
    assert isCached(weth_bal, TEST_BLOCK, TEST_CACHE_PATH)

    latest_block = W3.eth.block_number
    assert not isCached(weth_bal, latest_block, TEST_CACHE_PATH)
    weth_bal(W3, latest_block, TEST_CACHE_PATH)
    # should not cache because it is not finalized.
    # pretty sure there won't be timing problems here but not certain when we roll over
    assert not isCached(weth_bal, latest_block, TEST_CACHE_PATH)


@refresh_db
def test_Multicall__call__caches_only_finalized_blocks():
    assert not isCached(weth_bal, TEST_BLOCK, TEST_CACHE_PATH)
    assert not isCached(usdc_bal, TEST_BLOCK, TEST_CACHE_PATH)

    multi = Multicall([weth_bal, usdc_bal])
    multi(W3, TEST_BLOCK, TEST_CACHE_PATH)
    assert isCached(weth_bal, TEST_BLOCK, TEST_CACHE_PATH)
    assert isCached(usdc_bal, TEST_BLOCK, TEST_CACHE_PATH)

    latest_block = W3.eth.block_number
    assert not isCached(weth_bal, latest_block, TEST_CACHE_PATH)
    assert not isCached(usdc_bal, latest_block, TEST_CACHE_PATH)

    multi(W3, latest_block, TEST_CACHE_PATH)
    assert not isCached(weth_bal, latest_block, TEST_CACHE_PATH)
    assert not isCached(usdc_bal, latest_block, TEST_CACHE_PATH)



test_Call__call__caches_only_finalized_blocks()
test_Multicall__call__caches_only_finalized_blocks()


pass