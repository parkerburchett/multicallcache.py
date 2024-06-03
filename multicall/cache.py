import sqlite3
import pandas as pd
from pathlib import Path
import os

from multicall.call import Call
from multicall.constants import CACHE_PATH
from multicall.multicall import CallRawData, Multicall
from multicall.utils import flatten, time_function

# from multicall.constants import CACHE_PATH


"""
Notes on speed,
My machine 16 cores, 64gb ram, Intel® Core™ i7-10700KF CPU @ 3.80GHz  16 

13 seconds to write 1M rows. Takes up 4.2G disk space. Agressive assumptions on bytes returned. each is assumed
to be 3000 long random bytes. in practice should be much much smaller

In practice a very long bit of data is len 194, in practice, almost all is len 40 for a single returned value

10M rows takes up 7.8gb with agressive response data size assumptions

30sec to read all 10m rows
"""

# TODO add logging
"""
log read x lines in y seconds from dbPath
log wrote x lines in y seconds to dbPath
log attempted to read X rows, found y rows and did not find z rows from dbPATH

"""


COLUMNS = [
    "callId",  # sha256(chainId, target, signature, arguements, block)
    "target",
    "signature",
    "argumentsAsStr",
    "argumentsAsPickle",
    "block",
    "chainId",
    "success",
    "response",
]


def return_cleaned_data_as_df(data: list[CallRawData]) -> pd.DataFrame:
    # list_of_values_to_cache = [c.convert_to_format_to_save_in_cache_db() for c in data]
    pass


def save_data(data: list[CallRawData], cache_path: Path) -> None:
    # Convert the CallRawData objects to the format required for the database
    list_of_values_to_cache = [c.convert_to_format_to_save_in_cache_db() for c in data]

    with sqlite3.connect(cache_path) as conn:
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


def delete_call(call: Call, block: int, cache_path: Path) -> bool:
    """Delete a single call entry based on callId and return True if the operation was successful, False otherwise."""

    call_id = call.to_id(block)

    with sqlite3.connect(cache_path) as conn:
        cursor = conn.cursor()

        # Execute the delete statement
        cursor.execute(
            """
            DELETE FROM multicallCache
            WHERE callId = ?
            """,
            (call_id,),
        )

        # Check if the row was deleted
        if cursor.rowcount > 0:
            conn.commit()  # Commit the changes if the row was deleted
            return True
        else:
            return False  # No row was deleted, possibly because it did not exist


def isCached(call: Call, block: int, cache_path: Path) -> bool:
    """return bool -> we have this"""

    call_id = call.to_id(block)

    with sqlite3.connect(cache_path) as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT success, response
            FROM multicallCache
            WHERE callId = ?
            """,
            (call_id,),
        )
        result = cursor.fetchone()
        if result:
            return True
        else:
            return False


def get_isCached_success_raw_bytes_output_for_a_single_call(
    call: Call, block: int, cache_path: Path
) -> tuple[bool, bytes] | None:
    """run one call and return success and block or None if the call is not indexed"""

    call_id = call.to_id(block)

    with sqlite3.connect(cache_path) as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT success, response
            FROM multicallCache
            WHERE callId = ?
            """,
            (call_id,),
        )
        result = cursor.fetchone()
        if result is not None:
            return (True, result[0], result[1])  # we have it, success, response
        else:
            return (False, None, None)  # we have it, success, response


@time_function
def get_data_from_disk(calls: list[Call], blocks: list[int], cache_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Read from disk in chunks to manage memory and performance. Returns found_df and not_found_df.
    """
    multicall = Multicall(calls)
    # todo, speed up with threading, can be slow at scale
    empty_df = pd.DataFrame.from_records(flatten([multicall.to_list_of_empty_records(block) for block in blocks]))
    call_ids = empty_df["callId"].to_list()

    chunk_size = 100_000
    found_dfs = []

    with sqlite3.connect(cache_path) as conn:
        for i in range(0, len(call_ids), chunk_size):
            # Prepare the SQL query with placeholders for current chunk
            current_ids = call_ids[i : i + chunk_size]
            placeholders = ",".join("?" for _ in current_ids)
            query = f"""
                SELECT * FROM multicallCache
                WHERE callId IN ({placeholders})
            """
            # Fetch data for the current chunk
            chunk_df = pd.read_sql_query(query, conn, params=current_ids)
            chunk_df.columns = COLUMNS
            found_dfs.append(chunk_df)

    # Concatenate all dataframes from each chunk
    found_df = pd.concat(found_dfs, ignore_index=True) if found_dfs else pd.DataFrame()

    # Determine which call_ids were not found in the cache
    call_ids_not_already_found = set(call_ids).difference(found_df["callId"])
    not_found_df = empty_df[empty_df["callId"].isin(call_ids_not_already_found)]

    return found_df, not_found_df


# def get_data_from_disk(calls: list[Call], blocks: list[int], cache_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
#     """
#     Read from disk. Returns found_df and not_found_df
#     """
#     multicall = Multicall(calls)
#     empty_df = pd.DataFrame.from_records(flatten([multicall.to_list_of_empty_records(block) for block in blocks]))
#     call_ids = empty_df["callId"].to_list()

#     with sqlite3.connect(cache_path) as conn:
#         query = f"""
#             SELECT * FROM multicallCache
#             WHERE callId IN ({','.join('?' * len(call_ids))})
#         """
#         found_df = pd.read_sql_query(query, conn, params=call_ids)
#         found_df.columns = COLUMNS

#     call_ids_not_already_found = set(empty_df["callId"]).difference(found_df["callId"])
#     not_found_df = empty_df[empty_df["callId"].isin(call_ids_not_already_found)]

#     return found_df, not_found_df

# @timeFunction
# def get_data_from_disk(calls, blocks, cache_path) -> tuple[pd.DataFrame, pd.DataFrame]:
#     """
#     Read from disk. Returns found_df and not_found_df by using a temporary table to handle large numbers of call_ids efficiently.
#     """
#     multicall = Multicall(calls)
#     empty_df = pd.DataFrame.from_records(flatten([multicall.to_list_of_empty_records(block) for block in blocks]))
#     call_ids = empty_df["callId"].to_list()

#     with sqlite3.connect(str(cache_path)) as conn:
#         # Create a temporary table to store call_ids
#         conn.execute("CREATE TEMP TABLE IF NOT EXISTS temp_call_ids (id BLOB)")
#         # Insert call_ids into the temporary table
#         conn.executemany("INSERT INTO temp_call_ids (id) VALUES (?)", ((id,) for id in call_ids))

#         # Select data joining the temporary table with the main cache table
#         query = """
#             SELECT mc.* FROM multicallCache mc
#             JOIN temp_call_ids tc ON mc.callId = tc.id
#         """
#         found_df = pd.read_sql_query(query, conn)
#         found_df.columns = COLUMNS  # Assuming COLUMNS is defined somewhere globally

#         # Cleanup the temporary table
#         conn.execute("DROP TABLE temp_call_ids")

#     # Determine which call_ids were not found in the cache
#     call_ids_not_already_found = set(call_ids).difference(found_df["callId"])
#     not_found_df = empty_df[empty_df["callId"].isin(call_ids_not_already_found)]

#     return found_df, not_found_df


def df_to_CallRawData(df: pd.DataFrame, calls: list[Call], blocks: list[int]) -> list[CallRawData]:

    callIds_to_call_and_block = dict()  # callId -> tuple(call, block)

    for call in calls:
        for block in blocks:
            call_id = call.to_id(block)
            callIds_to_call_and_block[call_id] = (call, block)

    call_id_to_success_and_response = df.set_index("callId")[["success", "response"]].apply(tuple, axis=1).to_dict()

    all_raw_call_data = []
    for call_id in df["callId"]:
        call, block = callIds_to_call_and_block[call_id]
        success, response = call_id_to_success_and_response[call_id]
        a_call_raw_data = CallRawData(call=call, block=block, success=success, response=response)
        all_raw_call_data.append(a_call_raw_data)

    return all_raw_call_data


def fetch_all_data(cache: Path = "default") -> pd.DataFrame:
    cache_path = CACHE_PATH if cache == "default" else cache
    with sqlite3.connect(cache_path) as conn:
        df = pd.read_sql_query("SELECT * FROM multicallCache LIMIT 1", conn)
    return df


def get_db_size(cache_path: Path) -> int:
    with sqlite3.connect(cache_path) as conn:
        # TODO not efficient
        df = pd.read_sql_query("SELECT * FROM multicallCache", conn)
        return len(df)


def create_db(db_path: Path):
    if os.path.exists(db_path):
        raise ValueError(f"cannot create a db at {db_path=} because it already exists")
    else:
        with open(db_path, "w") as fp:
            del fp
            pass

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
    CREATE TABLE IF NOT EXISTS multicallCache (
        callId BLOB PRIMARY KEY,
        target TEXT,
        signature TEXT,
        argumentsAsStr TEXT,
        argumentsAsPickle bytes,
        block INTEGER,
        chainId INTEGER,
        success BOOLEAN,
        response BLOB
    )
    """
        )
        conn.commit()


def delete_db(db_path: Path):
    if os.path.exists(db_path):
        os.remove(db_path)
    else:
        raise ValueError(f"Cannot remove a db at {db_path=} because it does not exist")
