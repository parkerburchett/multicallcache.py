import pandas as pd
import pytest

from multicall.fetch_multicall_across_blocks import (
    fetch_save_and_return,
    async_fetch_multicalls_across_blocks,
    first_read_disk_then_fetch_others,
)


from test_constants import w3, weth_bal, usdc_bal, invalid_function, target_has_no_code, test_data_path, weth_bal2


# def test_simple_sequential_fetch_multicalls_across_blocks():
#     # reach out for all data single thread
#     found_df = simple_sequential_fetch_multicalls_across_blocks(calls, blocks, w3)
#     expected_df = pd.read_parquet(test_data_path / "simple_sequential_test_data.parquet")
#     assert expected_df.equals(found_df), "expected_df for sequential call does not match found_df"


# @pytest.mark.asyncio
# async def test_async_fetch_multicalls_across_blocks():
#     found_df = await async_fetch_multicalls_across_blocks(calls, blocks, w3, rate_limit_per_second=1)
#     expected_df = pd.read_parquet(test_data_path / "simple_sequential_test_data.parquet")
#     assert expected_df.equals(found_df), "expected_df for async call does not match found_df"


def test_fetch_save_and_return():
    calls = [weth_bal, usdc_bal, invalid_function, target_has_no_code]
    blocks = [i for i in range(18_000_000, 19_000_000, 10_000)]
    df = fetch_save_and_return([*calls, weth_bal2], blocks, w3)
    print(df.head())
    pass


test_fetch_save_and_return()