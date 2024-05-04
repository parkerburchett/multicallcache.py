from multicall.call import Call
from multicall.multicall import CallRawData, Multicall
import sqlite3
import pandas as pd

CACHE_PATH = "cache_db.sqlite"  # move to .env file.


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


def fetch_all_data():
    # Connect to the SQLite database
    conn = sqlite3.connect(CACHE_PATH)
    df = pd.read_sql_query("SELECT * FROM multicallCache", conn)
    return df

