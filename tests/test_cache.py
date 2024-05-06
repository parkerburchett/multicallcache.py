import os

from dotenv import load_dotenv
import pytest
from web3 import Web3
import web3
from multicall.call import Call
from multicall.cache import (
    save_data,
    fetch_all_data,
    insert_random_rows,
    get_data_by_call_ids,
    generate_random_data,
    get_data_by_call_ids_optimized,
)
from multicall.multicall import Multicall
import sqlite3
from datetime import datetime

from test_constants import weth_bal, usdc_bal

CACHE_PATH = "cache_db.sqlite"  # move to .env file.

load_dotenv()

BLOCK_TO_CHECK = 18_000_000
w3 = Web3(Web3.HTTPProvider(os.environ.get("ALCHEMY_URL")))

cbETH = "0xBe9895146f7AF43049ca1c1AE358B0541Ea49704"
cbETH_holder = "0xED1F7bb04D2BA2b6EbE087026F03C96Ea2c357A8"


def write_a_bunch_of_random_rows(n=10_000_000):
    print(n, "random rows to add")
    insert_random_rows(n)


def test_can_write():
    a_multicall = Multicall([weth_bal, usdc_bal])
    data = a_multicall.make_each_call_to_raw_call_data(w3, BLOCK_TO_CHECK)
    save_data(data)
    df = fetch_all_data()
    print(df.head())


def write_big():
    start = datetime.now()
    write_a_bunch_of_random_rows()
    print("total time", datetime.now() - start)

    print("start reading")
    df = fetch_all_data()
    print(df.shape)


# TODO add tests that callId works even for all kinds of calls


if __name__ == "__main__":
    # write_big()
    df = fetch_all_data()
    exist_callIds = list(df["callId"].sample(1_000_000).values)
    does_not_exist_callIds = [d[0] for d in generate_random_data(1_000_000)]

    # exists_df = get_data_by_call_ids_optimized(exist_callIds)
    # print(exists_df.head())
    # print(exists_df.shape)
    # not_exist_df = get_data_by_call_ids_optimized(does_not_exist_callIds)
    # print(not_exist_df.head())
    # print(not_exist_df.shape)

    both_df = get_data_by_call_ids_optimized([*exist_callIds, *does_not_exist_callIds])
    print(both_df.head())
    print(both_df.shape)

    pass
