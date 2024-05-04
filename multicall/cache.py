from multicall.call import Call
from multicall.multicall import CallRawData, Multicall
import sqlite3
import pandas as pd

CACHE_PATH = "cache_db.sqlite"  # move to .env file.


def save_data(data: list[CallRawData]):
    # Convert the CallRawData objects to the format required for the database
    format_to_cache = [c.convert_to_format_to_save_in_cache_db() for c in data]

    # Connect to the SQLite database
    conn = sqlite3.connect(CACHE_PATH)
    cursor = conn.cursor()

    # Bulk insert using executemany
    cursor.executemany(
        """
        INSERT INTO multicallCache (callId, success, single_function_return_data_bytes)
        VALUES (?, ?, ?)
        ON CONFLICT(callId) DO NOTHING;
        """,
        format_to_cache,
    )

    # Commit the changes and close the connection
    conn.commit()
    conn.close()


def fetch_and_print_all_data():
    # Connect to the SQLite database
    conn = sqlite3.connect(CACHE_PATH)
    cursor = conn.cursor()

    # Execute a query to fetch all records from multicallCache
    cursor.execute("SELECT * FROM multicallCache")

    # Fetch all rows from the cursor
    rows = cursor.fetchall()
    conn.close()
    records = [{"id": r[0], "success": bool(r[1]), "response_bytes": r[2]} for r in rows]
    df = pd.DataFrame.from_records(records)
    return df
