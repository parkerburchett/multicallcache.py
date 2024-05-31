import sqlite3
import pandas as pd
from pathlib import Path
import os

from multicall.call import Call
from multicall.multicall import CallRawData, Multicall
from multicall.utils import time_function, flatten
from multicall.constants import CACHE_PATH


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


def get_one_value(call: Call, block: int, cache_path: Path) -> tuple[bool, bytes] | None:
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
        if result:
            return (result[0], result[1])  # success, rawBytes Response
        else:
            return None


@time_function
def get_data_from_disk(calls: list[Call], blocks: list[int], cache_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Read from disk. Returns found_df and not_found_df
    """
    multicall = Multicall(calls)
    empty_df = pd.DataFrame.from_records(flatten([multicall.to_list_of_empty_records(block) for block in blocks]))
    call_ids = empty_df["callId"].to_list()

    with sqlite3.connect(cache_path) as conn:
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


def create_db(db_path: Path):
    # TODO broken, still need to run notebook
    if os.path.exists(db_path):
        raise ValueError(f"cannot create a db at {db_path=} because it already exists")

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
    CREATE TABLE multicallCache (
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
        raise ValueError(f"Cannot remove a db at {db_path=} because it does not exist exists")


# # create the db if it does not exist, run on import, ugly move to a place that makes more sense
# if not os.path.exists(CACHE_PATH):
#     create_db(CACHE_PATH)
