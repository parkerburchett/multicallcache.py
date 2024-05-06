from multicall.call import Call
from multicall.multicall import CallRawData, Multicall
from multicall.utils import time_function
import sqlite3
import pandas as pd
import random
import string
import multiprocessing
from multiprocessing import Pool
import time


CACHE_PATH = "cache_db.sqlite"  # move to .env file.

"""
Notes on speed,
My machine 16 cores, 64gb ram, Intel® Core™ i7-10700KF CPU @ 3.80GHz  16 

13 seconds to write 1M rows. takes up 4.2G disk space. Agressive assumptions on bytes returned. each is assumed
to be 3000 long random bytes. in practice should be much much smaller


in practice a very long bit of data is len 194, in practice, almost all should only be len 40 for a single returned value

10M rows takes up 7.8gb with agressive response data size assumptions

TODO saving data as pythonic instead of bytes will reduce size by a lot. back of the napkin 50% of response in bytes

writing is very fast. and it does not grow quickly. 10m data points is a whole lot, more than I need for sure


30sec to read all 10m Rows

"""

COLUMNS = ["callId", "target", "signature", "arguments", "block", "chainID", "success", "response"]


def save_data(data: list[CallRawData]) -> None:
    # Convert the CallRawData objects to the format required for the database
    list_of_values_to_cache = [c.convert_to_format_to_save_in_cache_db() for c in data]

    # Connect to the SQLite database
    conn = sqlite3.connect(CACHE_PATH)
    cursor = conn.cursor()

    # Bulk insert using executemany
    cursor.executemany(
        """
        INSERT INTO multicallCache (callId, target, signature, arguments, block, chainID, success, response)
        VALUES (?, ?, ?, ?, ?, ?, ? , ?)
        ON CONFLICT(callId) DO NOTHING;
        """,
        list_of_values_to_cache,
    )

    # Commit the changes and close the connection
    conn.commit()
    conn.close()


@time_function
def get_data_by_call_ids(call_ids: list[str]) -> pd.DataFrame:
    # fails on 1_000_000+ call_ids
    conn = sqlite3.connect(CACHE_PATH)
    query = f"""
        SELECT * FROM multicallCache
        WHERE callId IN ({','.join('?' * len(call_ids))})
    """
    existing_df = pd.read_sql_query(query, conn, params=call_ids)
    existing_df.columns = COLUMNS
    conn.close()
    df_callIds = pd.DataFrame()
    df_callIds["callId"] = call_ids
    # df_final = existing_df.merge(df_callIds, on='callId', how='left') # not certain join is right
    df_final = df_callIds.merge(existing_df, on="callId", how="left")  # not certain join is right

    return df_final


@time_function
def get_data_by_call_ids_optimized(call_ids: list[str]) -> pd.DataFrame:
    # note tested, idk if needed
    conn = sqlite3.connect(CACHE_PATH)
    cursor = conn.cursor()

    # Create a temporary table
    cursor.execute("CREATE TEMP TABLE IF NOT EXISTS tempCallIds (callId TEXT PRIMARY KEY)")

    # Insert call IDs into the temporary table (in batches if necessary)
    for batch in (call_ids[i : i + 5000] for i in range(0, len(call_ids), 5000)):
        cursor.executemany("INSERT OR IGNORE INTO tempCallIds (callId) VALUES (?)", [(id,) for id in batch])

    # Perform a join to get the required data
    query = """
        SELECT m.* FROM multicallCache m
        JOIN tempCallIds t ON m.callId = t.callId
    """
    df = pd.read_sql_query(query, conn)

    # Drop the temporary table
    cursor.execute("DROP TABLE tempCallIds")

    conn.close()
    return df


# i think the path should be
# try get_data_by_call_ids
# if that fails
# do get_data_by_call_ids_optimized
# alternative is to array split in to 100k chunks get_data_by_call_ids
# is cleaner


def fetch_all_data():
    conn = sqlite3.connect(CACHE_PATH)
    df = pd.read_sql_query("SELECT * FROM multicallCache", conn)
    conn.close()
    return df


def generate_random_string(length: int) -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_row(_) -> tuple:
    call_id = generate_random_string(40)
    target = generate_random_string(42)
    signature = generate_random_string(100)
    arguments = generate_random_string(100)
    block = random.randint(1, 20_000_000)
    chain_id = random.randint(1, 100)
    success = random.choice([True, False])
    # simulates the random number of values retunred by a function call, back of the napkin
    # in practice I have found it is typically only a single value, but there are some functions that return many values
    bytes_response_length = 40
    num_responses = random.choice([1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 3, 5, 10, 100])
    response = bytes(generate_random_string(bytes_response_length * num_responses), "utf-8")  # the largest random bytes
    return (call_id, target, signature, arguments, block, chain_id, success, response)


def generate_random_data(n: int) -> list:
    print(multiprocessing.cpu_count())
    with Pool(processes=multiprocessing.cpu_count() - 1) as pool:
        data = pool.map(generate_row, range(n))
    print("made data")
    return data


def insert_random_rows(n: int) -> None:
    random_data = generate_random_data(n)
    from datetime import datetime

    start = datetime.now()
    conn = sqlite3.connect(CACHE_PATH)
    cursor = conn.cursor()

    cursor.executemany(
        """
        INSERT INTO multicallCache (callId, target, signature, arguments, block, chainID, success, response)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(callId) DO NOTHING;
        """,
        random_data,
    )

    conn.commit()
    conn.close()
    print("time to write", n, "rows", datetime.now() - start)
