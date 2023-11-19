from sqlitedict import SqliteDict
from multicall import Call

CACHE_PATH = 'cache_db.sqlite'
db = SqliteDict(CACHE_PATH)


def call_to_db_id(call: Call) -> str:
    return call.target, call.signature.signature, call.args, call.block_id


def is_in_db(call_id: str) -> bool:
    # is, maybe do set for faster lookup?
    return call_id in db


def add_to_db(call: Call, response: any) -> None:
    """Add the call -> response to the db """

    if call.block_id is None:
        return
    
    unique_id = call_to_db_id(call)
    db[unique_id] = response

