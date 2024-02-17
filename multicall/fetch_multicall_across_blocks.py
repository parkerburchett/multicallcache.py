import asyncio
import aiohttp


import pandas as pd
from web3 import Web3

from multicall.call import Call
from multicall.multicall import Multicall
from aiolimiter import AsyncLimiter

from multicall.rpc_call import async_rpc_eth_call


async def async_fetch_multicalls_across_blocks(
    calls: list[Call], blocks: list[int], w3: Web3, rate_limit_per_second: int
) -> pd.DataFrame:

    rate_limiter = AsyncLimiter(rate_limit_per_second, time_period=1)
    timeout = aiohttp.ClientTimeout(total=10)
    multicall = Multicall(calls)

    tasks = [
        await async_rpc_eth_call(
            w3,
        )
        for block in blocks
    ]

    async with aiohttp.ClientSession(timeout=timeout) as session:

        multicall = Multicall(calls)
        tasks = [await multicall.async_call(w3, block) for block in blocks]
        responses = asyncio.gather(*tasks)
        df = pd.DataFrame.from_records(responses)
        return df


def simple_sequential_fetch_multicalls_across_blocks(calls: list[Call], blocks: list[int], w3: Web3) -> pd.DataFrame:
    multicall = Multicall(calls)

    responses = []
    for block_id in blocks:
        mulitcall_response: dict[str, any] = multicall(w3, block_id)
        responses.append(mulitcall_response)

    df = pd.DataFrame.from_records(responses)
    return df
