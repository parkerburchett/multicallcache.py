import asyncio

import pandas as pd


from multicall.fetch_multicall_across_blocks import (
    simple_sequential_fetch_multicalls_across_blocks,
    async_fetch_multicalls_across_blocks,
)
from multicall.multicall import Multicall


from test_constants import w3, weth_bal, usdc_bal, invalid_function, target_has_no_code, test_data_path


calls = [weth_bal, usdc_bal, invalid_function, target_has_no_code]
blocks = [18_000_000, 18_001_000]



def simple_sequential_tests():
    found_df = simple_sequential_fetch_multicalls_across_blocks(calls, blocks, w3)
    expected_df = pd.read_parquet(test_data_path / "simple_sequential_test_data.parquet")
    assert expected_df.equals(found_df), "expected_df for sequential call does not match found_df"


async def simple_async_test():
    found_df = await async_fetch_multicalls_across_blocks(calls, blocks, w3, rate_limit_per_second=1)
    expected_df = pd.read_parquet(test_data_path / "simple_sequential_test_data.parquet")
    assert expected_df.equals(found_df), "expected_df for async call does not match found_df"

# if __name__ == "__main__":
#     # asyncio.run(simple_async_test()) is the correct way to run async functions in the main block
#     # asyncio.run(simple_async_test())
#     simple_sequential_tests()
#     pass
