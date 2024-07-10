import pandas as pd

from multicall.fetch_multicall_across_blocks import fetch_save_and_return
from multicall.constants import W3, TEST_CACHE_PATH
from helpers import weth_bal, usdc_bal, invalid_function, target_has_no_code, weth_bal2, refresh_testing_db


@refresh_testing_db
def test_fetch_save_and_return():
    """Make sure that it gets the same data twice, and it matches what was already fetched"""

    calls = [weth_bal, usdc_bal, invalid_function, target_has_no_code, weth_bal2]
    # include speed tests
    blocks = [18_000_000, 18_500_000, 19_000_000, 19_500_000]
    first_df = fetch_save_and_return(calls, blocks, W3, 10, cache=TEST_CACHE_PATH)
    second_df = fetch_save_and_return(calls, blocks, W3, 10, cache=TEST_CACHE_PATH)
    assert first_df.equals(second_df)
    local_df = pd.read_parquet("tests/test_data/test_fetch_save_and_return_data.parquet")
    assert first_df.equals(local_df)
