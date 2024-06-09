import asyncio
import aiohttp


import pandas as pd
from web3 import Web3
import numpy as np
from pathlib import Path
from aiolimiter import AsyncLimiter
import nest_asyncio


from multicall.call import Call
from multicall.multicall import Multicall
from multicall.utils import flatten, time_function
from multicall.cache import save_data, get_data_from_disk
from multicall.constants import CACHE_PATH

nest_asyncio.apply()


# there is testing to be done here on how to get the most juice out of alchemy
@time_function
def fetch_save_and_return(
    calls: list[Call],  # TODO, also might want to be able to pass it a multicall? maybe?
    blocks: list[int],
    w3: Web3,
    max_calls_per_second: int = 10,
    cache="default",
    max_calls_per_rpc_call: int = 300,
) -> pd.DataFrame:
    """
    Primary Entry Point

    Get all the data that already exists
    externally fetch  and sve all the data that is missing
    read entire saved data from disk and return it processed.
    """
    # TODO add some kind of progress bar
    # reading locally
    # progress bar
    if len(calls) == 0:
        raise ValueError("len(calls) cannot be 0")
    if len(blocks) == 0:
        raise ValueError("len(blocks) cannot be 0")

    cache_path = CACHE_PATH if cache == "default" else cache

    found_df, not_found_df = get_data_from_disk(calls, blocks, cache_path)
    print(f"{found_df.shape=}      {not_found_df.shape=} \n")
    blocks_left = [int(b) for b in not_found_df["block"].unique()]

    # TODO, currently fails in jupyter, can't use asycio.run inside of jupyter
    if len(blocks_left) > 0:
        # TODO fix timeout errors
        print(
            f"Some data not found, making {len(blocks_left)} external calls at a rate of {max_calls_per_second} call /second \n"
        )
        asyncio.run(
            async_fetch_multicalls_across_blocks_and_save(
                calls=calls,
                blocks=blocks,
                w3=w3,
                rate_limit_per_second=max_calls_per_second,
                cache_path=cache_path,
                save=True,
                max_calls_per_rpc_call=max_calls_per_rpc_call,
            )
        )
        found_df, not_found_df = get_data_from_disk(calls, blocks, cache_path)
        print(f"After fetching missing data {found_df.shape=}      {not_found_df.shape=} \n")
        pass
    else:
        print("all data on disk, no external calls needed!!!")

    if not_found_df.shape[0] != 0:
        print(not_found_df.shape)
        print(not_found_df.head())
        raise ValueError("failed to save everything to disk")

    processed_block_wise_data_df = _raw_bytes_data_df_to_processed_block_wise_data_df(found_df, calls, blocks)
    return processed_block_wise_data_df


def simple_sequential_fetch_multicalls_across_blocks_and_save(
    calls: list[Call], blocks: list[int], w3: Web3, cache_path: Path
) -> None:
    """make and save all the data from calls, blocks"""

    multicall = Multicall(calls)
    call_raw_data = []
    for block_id in blocks:
        data = multicall.make_external_calls_to_raw_data(w3, block_id)
        call_raw_data.extend(data)

    save_data(call_raw_data, cache_path)


async def async_fetch_multicalls_across_blocks_and_save(
    calls: list[Call],
    blocks: list[int],
    w3: Web3,
    rate_limit_per_second: int,
    cache_path: Path,
    save: bool = True,
    max_calls_per_rpc_call: int = 3_000,
):
    num_calls = len(calls)
    if num_calls < max_calls_per_rpc_call:
        # base case
        multicalls = [Multicall(calls)]
    else:
        chunks_of_calls = np.array_split(calls, (len(calls) // max_calls_per_rpc_call) + 1)
        multicalls = [Multicall(list(c)) for c in chunks_of_calls]

    rate_limiter = AsyncLimiter(rate_limit_per_second, time_period=1)
    timeout = aiohttp.ClientTimeout(total=10)
    tasks = []
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for multicall in multicalls:
            tasks.extend(
                [multicall.async_make_each_call_to_raw_call_data(w3, block, session, rate_limiter) for block in blocks]
            )

        call_raw_data = await asyncio.gather(*tasks)

    call_raw_data = flatten(call_raw_data)

    if save:
        save_data(call_raw_data, cache_path)
    else:
        return call_raw_data


# fast enough even at size
def _raw_bytes_data_df_to_processed_block_wise_data_df(
    raw_bytes_data_df: pd.DataFrame, calls: list[Call], blocks: list[int]
) -> pd.DataFrame:
    call_id_to_success_and_response = dict()

    for callId, success, response in zip(
        raw_bytes_data_df["callId"], raw_bytes_data_df["success"], raw_bytes_data_df["response"]
    ):
        call_id_to_success_and_response[callId] = (success, response)

    callIds_to_call_and_block = dict()

    for call in calls:
        for block in blocks:
            call_id = call.to_id(block)
            callIds_to_call_and_block[call_id] = (call, block)

    # label, handeling function, decoded value
    # TODO duplicate logic as in cache.py pick one and stick with it
    processed_outputs: dict[int, list[dict[str, any]]] = {}

    for callId, call_block in callIds_to_call_and_block.items():
        (call, block) = call_block
        (success, raw_bytes_output) = call_id_to_success_and_response[callId]  # should never fail

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
        # | Block ID | weth_balance_of      | usdcDecimals  | lastTimestampUpdate |
        # |----------|----------------------|---------------|---------------------|
        # | ZZZ      | AAA                  | BBB           | CCC                 |
        # | YYY      | EEE                  | BBB           | DDD                 |

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
