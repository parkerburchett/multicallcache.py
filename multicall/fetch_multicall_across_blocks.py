import asyncio
import aiohttp


import pandas as pd
from web3 import Web3

from aiolimiter import AsyncLimiter


from multicall.call import Call, REVERTED_UNKNOWN_MESSAGE
from multicall.multicall import Multicall
from multicall.utils import flatten, time_function
from multicall.cache import save_data, get_data_from_disk


@time_function
def fetch_save_and_return(
    calls: list[Call], blocks: list[int], w3: Web3, max_calls_per_second: int = 10
) -> pd.DataFrame:
    # todo, calls, and blocks can be 0 make sure it works
    found_df, not_found_df = get_data_from_disk(calls, blocks)
    print(f"first attempt    {found_df.shape=}      {not_found_df.shape=} \n")
    blocks_left = [int(b) for b in not_found_df["block"].unique()]
    if len(blocks_left) > 0:
        print(
            f"Some data not found, making {len(blocks_left)} external calls at a rate of {max_calls_per_second} call /second \n"
        )
        asyncio.run(async_fetch_multicalls_across_blocks_and_save(calls, blocks, w3, max_calls_per_second))
        found_df, not_found_df = get_data_from_disk(calls, blocks)
        print(f"Second attempt    {found_df.shape=}      {not_found_df.shape=} \n")
        pass
    else:
        print("all data on disk, no external calls needed!!!")

    if not_found_df.shape[0] != 0:
        print(not_found_df.shape)
        print(not_found_df.head())
        raise ValueError("failed to save everything to disk")

    processed_block_wise_data_df = _raw_bytes_data_df_to_processed_block_wise_data_df(found_df, calls, blocks)
    return processed_block_wise_data_df


def simple_sequential_fetch_multicalls_across_blocks_and_save(calls: list[Call], blocks: list[int], w3: Web3) -> None:
    """make and save all the data from calls, blocks"""

    multicall = Multicall(calls)
    call_raw_data = []
    for block_id in blocks:
        data = multicall.make_external_calls_to_raw_data(w3, block_id)
        call_raw_data.extend(data)

    save_data(call_raw_data)


async def async_fetch_multicalls_across_blocks_and_save(
    calls: list[Call], blocks: list[int], w3: Web3, rate_limit_per_second: int
) -> None:

    multicall = Multicall(calls)
    rate_limiter = AsyncLimiter(rate_limit_per_second, time_period=1)  # 1 second
    timeout = aiohttp.ClientTimeout(total=10)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        tasks = [multicall.async_make_each_call_to_raw_call_data(w3, block, session, rate_limiter) for block in blocks]
        call_raw_data = await asyncio.gather(*tasks)
    call_raw_data = flatten(call_raw_data)
    save_data(call_raw_data)


@time_function
def _raw_bytes_data_df_to_processed_block_wise_data_df(
    raw_bytes_data_df: pd.DataFrame, calls: list[Call], blocks: list[int]
) -> pd.DataFrame:
    # pure function, no external calls, fast enough, todo test with 1m data points
    # dict of callid: raw_bytes_output
    call_id_to_raw_bytes_output = dict()

    for callId, success, response in zip(
        raw_bytes_data_df["callId"], raw_bytes_data_df["success"], raw_bytes_data_df["response"]
    ):
        call_id_to_raw_bytes_output[callId] = (success, response)

    callIds_to_call = dict()

    for call in calls:
        for block in blocks:
            callIds_to_call[call.to_id(block)] = (call, block)

    # label, handeling function, decoded value
    processed_outputs: dict[int, list[dict[str, any]]] = {}

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
