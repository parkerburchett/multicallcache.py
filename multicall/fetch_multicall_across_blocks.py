import asyncio
import aiohttp


import pandas as pd
from web3 import Web3

from multicall.call import Call, REVERTED_UNKNOWN_MESSAGE
from multicall.multicall import Multicall
from multicall.utils import flatten
from multicall.cache import save_data, get_data_from_disk
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

    return pd.DataFrame.from_records(responses)


# primary entry point
def fetch_save_and_return(calls: list[Call], blocks: list[int], w3: Web3) -> pd.DataFrame:
    _, not_found_df = get_data_from_disk(calls, blocks)
    blocks_left = list(not_found_df["block"].unique())
    simple_sequential_fetch_multicalls_across_blocks_and_save(calls, blocks_left, w3)

    raw_bytes_data_df, not_found_df = get_data_from_disk(calls, blocks)

    if not_found_df.shape[0] != 0:
        raise ValueError("failed to save everthing to disk")

    # dict of callid: raw_bytes_output
    call_id_to_raw_bytes_output = dict()

    for callId, response, success in zip(
        raw_bytes_data_df["callId"], raw_bytes_data_df["response"], raw_bytes_data_df["success"]
    ):
        call_id_to_raw_bytes_output[callId] = (success, response)  # tuple of (bool success, bytes response)

    callIds_to_call = dict()

    for call in calls:
        for block in blocks:
            callIds_to_call[call.to_id(block)] = (call, block)

    # label, handeling function, decoded value
    processed_outputs: dict[int : [dict[str, any]]] = dict()

    for callId, call_block in callIds_to_call.items():
        (call, block) = call_block
        (success, raw_bytes_output) = call_id_to_raw_bytes_output[callId]  # should never fail

        processed_response: dict[str, any] = call.decode_output(raw_bytes_output)

        if block in processed_outputs:
            processed_outputs[block].update(processed_response)
        else:
            processed_outputs[block] = processed_response

        # looks like
        # a list of dictionaries like
        # {'weth_balance_of': AAA, block: ZZZ}
        # and {'usdcDecimals': BBB, 'lastTimestampUpdate': CCC, block: ZZZ}

        # for many blocks:

        # {'weth_balance_of': EEE, block: YYY}
        # and {'usdcDecimals': BBB, 'lastTimestampUpdate': DDD, block: YYY}

        # we want a df that looks like
        # block, weth_balance_of, usdcDecimals, lastTimestampUpdate
        # ZZZ, AAA, BBB, CCC
        # YYY, EEE, BBB, DDD

    # at ths point  processed_outputs looks like

    # {
    #     XXX: {'weth_balance_of': AAA,  'usdcDecimals': BBB, 'lastTimestampUpdate': CCC},
    #     YYY: {'weth_balance_of': EEE,  'usdcDecimals': BBB, 'lastTimestampUpdate': DDD},
    # }

    # needs to be turned into a dataframe

    records = []
    for block, all_processed_data_for_block in processed_outputs.items():
        all_processed_data_for_block["block"] = block
        records.append(all_processed_data_for_block)

    processed_block_wise_data_df = pd.DataFrame.from_records(records)

    return processed_block_wise_data_df


def simple_sequential_fetch_multicalls_across_blocks_and_save(calls: list[Call], blocks: list[int], w3: Web3) -> None:
    """make and save all the responese from calls"""

    # make and save all of the data in calls and blocks
    multicall = Multicall(calls)
    call_raw_data = []
    for block_id in blocks:
        data = multicall.make_external_calls_to_raw_data(w3, block_id)
        call_raw_data.extend(data)

    save_data(call_raw_data)
    # at this point can be certain that it is all saved


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
