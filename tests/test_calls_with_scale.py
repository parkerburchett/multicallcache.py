# """
# test cases
# - the rpc node fail because too many calls to fast (rate limiter should mostly prevent this)
# - too many calls in a block (100k), timeout, or gas fails

# """

# import pandas as pd
# from multicall.constants import TEST_CACHE_PATH, W3
# from helpers import to_str, weth, async_refresh_testing_db, TEST_BLOCK
# from multicall.fetch_multicall_across_blocks import async_fetch_multicalls_across_blocks_and_save
# from multicall.call import Call
# import pytest


# @async_refresh_testing_db
# @pytest.mark.asyncio
# async def test_break_up_many_calls_into_several_multicall():
#     # TODO make it so that you can run async tests, (maybe just use asycio.run)
#     assert 1 == 0
#     a_bunch_of_addresses = pd.read_csv("many_weth_transfers_more.csv")["to"].unique()[:100]
#     # TODO consider putting the addresses in a parquet for speed
#     calls = [Call(weth, "balanceOf(address)(uint256)", (a), a, to_str) for a in a_bunch_of_addresses]
#     data = await async_fetch_multicalls_across_blocks_and_save(
#         calls=calls,
#         blocks=[TEST_BLOCK],
#         w3=W3,
#         rate_limit_per_second=1,
#         save=False,
#         max_calls_per_rpc_call=30,
#         cache_path=TEST_CACHE_PATH,
#     )
#     assert (
#         data[0].response
#         == b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x11\xd3[\xec\x08\xe0\xd7\xbd"
#     )
#     assert data[0].call_id == b"\xce\x16\x99\x01\xb5\xd5&\x80BD,\xdb\xe07\xf7\xa2)yrp\x9fNS\x18\x8dS\x93\x9fU2\x13\x17"
#     assert len(data) == 100
