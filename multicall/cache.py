from sqlitedict import SqliteDict
from multicall import Call

CACHE_PATH = "cache_db.sqlite"
db = SqliteDict(CACHE_PATH)

### Schema
"""

bytes are pickle

columns:

targetAddress: address
signature: str
args: pickle
block_id: int
chain_id: int
state_identifer: pickle(target, signature, args, block_id, chain_id))  # this needs to be indexed

success: bool
response: pickle # can be error or None?

Columns: 
target_address: str
signature: str
args: bytes
block_id: int
state_identifer: bytes
success: bool
response: bytes

# I have a list of (state identifers)

make a single query to a sqllite db that gives all the rows of the exisintg


# execute many. 


"""


def call_to_db_id(call: Call) -> str:
    return call.target, call.signature.signature, call.args, call.block_id


def is_in_db(call_id: str) -> bool:
    # simple can do a faster one,
    return call_id in db


def add_to_db(call: Call, response: any) -> None:
    """Add the call -> response to the db"""

    if call.block_id is None:
        return

    unique_id = call_to_db_id(call)
    db[unique_id] = response
