from multicall.call import Call
from multicall.multicall import CallRawData, Multicall
from multicall.utils import time_function, flatten
import sqlite3
import pandas as pd
import random
import string
import multiprocessing
from multiprocessing import Pool
import pickle

CACHE_PATH = "cache_db.sqlite"  # TODO move to .env file.

# TODO saving data as pythonic as well for ease of sql querying after the fact

"""
Notes on speed,
My machine 16 cores, 64gb ram, Intel® Core™ i7-10700KF CPU @ 3.80GHz  16 

13 seconds to write 1M rows. Takes up 4.2G disk space. Agressive assumptions on bytes returned. each is assumed
to be 3000 long random bytes. in practice should be much much smaller

In practice a very long bit of data is len 194, in practice, almost all is len 40 for a single returned value

10M rows takes up 7.8gb with agressive response data size assumptions

30sec to read all 10m rows
"""

COLUMNS = [
    "callId",
    "target",
    "signature",
    "argumentsAsStr",
    "argumentsAsPickle",
    "block",
    "chainId",
    "success",
    "response",
]


def save_data(data: list[CallRawData]) -> None:
    # Convert the CallRawData objects to the format required for the database
    list_of_values_to_cache = [c.convert_to_format_to_save_in_cache_db() for c in data]

    with sqlite3.connect(CACHE_PATH) as conn:
        cursor = conn.cursor()

        # Bulk insert using executemany
        cursor.executemany(
            """
            INSERT INTO multicallCache (callId, target, signature, argumentsAsStr, argumentsAsPickle, block, chainId, success, response)
            VALUES (?, ?, ?, ?, ?, ?, ? , ?, ?)
            ON CONFLICT(callId) DO NOTHING;
            """,
            list_of_values_to_cache,
        )
        conn.commit()
    pass


@time_function
def get_data_from_disk(calls: list[Call], blocks: list[int]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Read from disk. Returns found_df and not_found_df
    """
    multicall = Multicall(calls)
    empty_df = pd.DataFrame.from_records(flatten([multicall.to_list_of_empty_records(block) for block in blocks]))
    call_ids = empty_df["callId"].to_list()

    with sqlite3.connect(CACHE_PATH) as conn:
        query = f"""
            SELECT * FROM multicallCache
            WHERE callId IN ({','.join('?' * len(call_ids))})
        """
        found_df = pd.read_sql_query(query, conn, params=call_ids)
        found_df.columns = COLUMNS

    call_ids_not_already_found = set(empty_df["callId"]).difference(found_df["callId"])
    not_found_df = empty_df[empty_df["callId"].isin(call_ids_not_already_found)]

    return found_df, not_found_df


def fetch_all_data():
    with sqlite3.connect(CACHE_PATH) as conn:
        return pd.read_sql_query("SELECT * FROM multicallCache", conn)


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
