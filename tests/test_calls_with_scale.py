"""
test cases
- the rpc node fail because too many calls to fast (rate limiter should mostly prevent this)
- too many calls in a block (100k), timeout, or gas fails

"""

from helpers import to_str, weth
from multicall.call import Call
import pandas as pd
from multicall.constants import W3

from multicall.fetch_multicall_across_blocks import async_fetch_multicalls_across_blocks_and_save
import pytest


@pytest.mark.asyncio
async def test_break_up_many_calls_into_several_multicall():
    a_bunch_of_addresses = pd.read_csv("many_weth_transfers.csv")["to"].unique()[:100]
    # TODO consider putting the addresses in a parquet for speed
    calls = [Call(weth, "balanceOf(address)(uint256)", (a), a, to_str) for a in a_bunch_of_addresses]
    data = await async_fetch_multicalls_across_blocks_and_save(
        calls, [18_000_000], W3, 1, save=False, max_calls_per_rpc_call=30
    )
    assert (
        data[0].response
        == b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x11\xd3[\xec\x08\xe0\xd7\xbd"
    )
    assert data[0].call_id == b"\xce\x16\x99\x01\xb5\xd5&\x80BD,\xdb\xe07\xf7\xa2)yrp\x9fNS\x18\x8dS\x93\x9fU2\x13\x17"
    assert len(data) == 100
