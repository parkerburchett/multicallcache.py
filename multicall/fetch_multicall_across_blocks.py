import asyncio
import aiohttp


import pandas as pd
from web3 import Web3

from multicall.call import Call
from multicall.multicall import Multicall
from multicall.utils import flatten
from multicall.cache import get_data_by_call_ids, get_data_from_disk
from aiolimiter import AsyncLimiter


async def async_fetch_multicalls_across_blocks(
    calls: list[Call], blocks: list[int], w3: Web3, rate_limit_per_second: int
) -> pd.DataFrame:

    multicall = Multicall(calls)
    rate_limiter = AsyncLimiter(rate_limit_per_second, time_period=1)
    timeout = aiohttp.ClientTimeout(total=10)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        tasks = [multicall.async_call(w3, block, session, rate_limiter) for block in blocks]
        responses = await asyncio.gather(*tasks)
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


def _from_not_found_df_to_blocks_to_check(
    not_found_df: pd.DataFrame, all_calls: list[Call], all_blocks: list[int]
) -> list[int]:
    ## note edge case where in block 1 we want 10 calls but in block 2 we want 4 calls because we have the other six
    # ignoring for now because there are negligible costs from increasing the calls at one block from 1 to 100
    # via multicall. gas for viwe only calls is free

    multicall = Multicall(all_calls)
    blocks_to_check = []
    for block in all_blocks:
        call_ids = multicall.to_call_ids(block)
        if not_found_df["callId"].isin(call_ids).any():
            blocks_to_check.append(block)

    # TODO:consider also removing some calls that were already made?
    return blocks_to_check


def first_read_disk_then_fetch_others(calls: list[Call], blocks: list[int], w3: Web3) -> pd.DataFrame:
    existing_df, not_found_df = get_data_from_disk(calls, blocks)
    blocks_to_check = _from_not_found_df_to_blocks_to_check(not_found_df, calls, blocks)
    # newly_fetched_df = simple_sequential_fetch_multicalls_across_blocks(calls, blocks_to_check, w3) # wrong kind of call
    # returns the useable df not the df for the sql database
    # full_df = pd.concat([newly_fetched_df, existing_df])
    # todo add logging, found X results on disk in some seconds, 90% of results
    # fetched Z results onchain, 15% of results
    # 5% duplicate calls because not seperating out by call
    # return full_df  # no order guarantee
