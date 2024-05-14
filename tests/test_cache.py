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
