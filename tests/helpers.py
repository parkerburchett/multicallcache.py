from pathlib import Path

import sqlite3
import random
import string
import multiprocessing
from multiprocessing import Pool
import pickle

from multicall.cache import create_db, delete_db
from multicall.constants import TEST_CACHE_PATH, CACHE_PATH, W3
from multicall.utils import time_function
from multicall.call import Call

test_data_path = Path(__file__).parent / "test_data"

uniswap_v3_usdc_weth_pool = "0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640"
weth = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
usdc = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
TEST_BLOCK = 18_000_000


def identity_function(x):
    return x


def refresh_testing_db(func):
    # makes a fresh db between tests
    def wrapper(*args, **kwargs):
        create_db(TEST_CACHE_PATH)
        try:
            result = func(*args, **kwargs)
            return result
        except KeyboardInterrupt:
            raise
        finally:
            delete_db(TEST_CACHE_PATH)

    return wrapper


def async_refresh_testing_db(func):
    # Makes a fresh database between tests
    async def wrapper(*args, **kwargs):
        create_db(TEST_CACHE_PATH)
        try:
            # Await the result of the async function
            result = await func(*args, **kwargs)
            return result
        except KeyboardInterrupt:
            # Properly pass on the KeyboardInterrupt for graceful shutdown
            raise
        finally:
            # Ensure the database is deleted even if there are errors
            delete_db(TEST_CACHE_PATH)

    return wrapper


def to_str(data: any) -> str:
    return str(data)


weth_bal = Call(
    weth,
    "balanceOf(address)(uint256)",
    (uniswap_v3_usdc_weth_pool),
    "weth_bal",
    to_str,
    W3,
)

weth_bal2 = Call(
    weth, "balanceOf(address)(uint256)", ("0x95222290DD7278Aa3Ddd389Cc1E1d165CC4BAfe5"), "weth_bal2", to_str, W3
)

usdc_bal = Call(usdc, "balanceOf(address)(uint256)", (uniswap_v3_usdc_weth_pool), "usdc_bal", to_str, W3)

invalid_function = Call(usdc, "functionDoesNotExist()(uint256)", (), "functionDoesNotExist", to_str, W3)

target_has_no_code = Call(
    "0x0000000000000000000000000000000000000000", "functionDoesNotExist()(uint256)", (), "notAContract", to_str, W3
)


# TODO move these elsewhere, to testing? maybe just remove
def _generate_random_string(length: int) -> str:
    """Helper function to make mock data"""
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def _generate_row(_) -> tuple:
    call_id = _generate_random_string(40)
    target = _generate_random_string(42)
    signature = _generate_random_string(100)
    arguments = (100, 50, _generate_random_string(40))
    argumentsAsString = str(arguments)
    argumentsAsPickle = pickle.dumps(arguments)
    block = random.randint(1, 20_000_000)
    chain_id = random.randint(1, 100)
    success = random.choice([True, False])
    # simulates the random number of values retunred by a function call, back of the napkin approximation
    # in practice I have found most function only a single value, but there are some functions that return many values
    bytes_response_length = 40
    num_responses = random.choice([1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 3, 5, 10, 100])
    response = bytes(
        _generate_random_string(bytes_response_length * num_responses), "utf-8"
    )  # the largest random bytes
    return (call_id, target, signature, argumentsAsString, argumentsAsPickle, block, chain_id, success, response)


def _generate_random_data(n: int) -> list:
    with Pool(processes=multiprocessing.cpu_count() - 1) as pool:
        return pool.map(_generate_row, range(n))


@time_function
def insert_random_rows(n: int) -> None:
    """Helper function to test read / write speeds for the sqllite database"""
    random_data = _generate_random_data(n)

    with sqlite3.connect(CACHE_PATH) as conn:
        cursor = conn.cursor()

        cursor.executemany(
            """
            INSERT INTO multicallCache (callId, target, signature, argumentsAsStr, argumentsAsPickle, block, chainID, success, response)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(callId) DO NOTHING;
            """,
            random_data,
        )

        conn.commit()
