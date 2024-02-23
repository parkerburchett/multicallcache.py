import sqlite3
from multicall.call import Call


CACHE_PATH = "cache_db.sqlite" # move to .env file. 

def main():
    conn = sqlite3.connect(CACHE_PATH)
    cursor = conn.cursor()

    # Create the multicallCache table
    # Ensure callId is a primary key for quick lookups
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS multicallCache (
        callId TEXT PRIMARY KEY,
        success BOOLEAN,
        single_function_return_data_bytes BLOB
    )
    ''')

    conn.commit()

    cursor.execute('SELECT * FROM multicallCache WHERE callId = ?', ('exampleCallId',))
    conn.close()

        
if __name__ == '__main__':
    main()