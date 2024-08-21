from multicallcache.cache import isCached
from multicallcache.multicall import Multicall

from helpers import weth_bal, usdc_bal, refresh_testing_db, TEST_BLOCK
from multicallcache.constants import TEST_CACHE_PATH, W3


@refresh_testing_db
def test_Call__call__caches_only_finalized_blocks():
    assert not isCached(weth_bal, TEST_BLOCK, TEST_CACHE_PATH)
    weth_bal(TEST_BLOCK, TEST_CACHE_PATH)
    assert isCached(weth_bal, TEST_BLOCK, TEST_CACHE_PATH)

    latest_block = W3.eth.block_number
    assert not isCached(weth_bal, latest_block, TEST_CACHE_PATH)
    weth_bal(latest_block, TEST_CACHE_PATH)
    # should not cache because it is not finalized.
    # TODO: pretty sure there won't be timing problems here but not certain
    assert not isCached(weth_bal, latest_block, TEST_CACHE_PATH)


@refresh_testing_db
def test_Multicall__call__caches_only_finalized_blocks():
    assert not isCached(weth_bal, TEST_BLOCK, TEST_CACHE_PATH)
    assert not isCached(usdc_bal, TEST_BLOCK, TEST_CACHE_PATH)

    multi = Multicall([weth_bal, usdc_bal])
    multi(TEST_BLOCK, TEST_CACHE_PATH)
    assert isCached(weth_bal, TEST_BLOCK, TEST_CACHE_PATH)
    assert isCached(usdc_bal, TEST_BLOCK, TEST_CACHE_PATH)

    latest_block = W3.eth.block_number
    assert not isCached(weth_bal, latest_block, TEST_CACHE_PATH)
    assert not isCached(usdc_bal, latest_block, TEST_CACHE_PATH)

    multi(latest_block, TEST_CACHE_PATH)  # don't cache a call on the latest, non finalized block
    assert not isCached(weth_bal, latest_block, TEST_CACHE_PATH)
    assert not isCached(usdc_bal, latest_block, TEST_CACHE_PATH)
