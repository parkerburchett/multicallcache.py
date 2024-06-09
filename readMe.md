## TODO
- Add pythonic data types to database in addition to (perhaps instead of?) the raw bytes response
- Cache.py and Call.py circular import issue
- Make sure the same variables have the same names across methods
- Move cache_path to environ variables
- Make an example notebook demoing behavior
- Make a package for pip
- Move Database creating script from jupyter to a .py file
- Add verbose doc strings to high level methods
- Make all functions designed for internal use prefixed by `_` consider double `__` prefix for helper methods only to be used within the file. 
- Delete all commented out code
- Make a short youtube video demoing why this is useful 
- Stretch goal: Add some basic sql querying functionality in example notebook
- Maybe some kind of lock that prevents writing to the DB without going through official means. 
- Add testing for other chains
- Add testing for blocks before multicall contracts where deployed. Currently calls fails before 12336033,
- Minimize RPC calls for finalized blocks, maybe query finalized block at import time, and only update if asked to?
- Add testing for caching behavior of `multicall.Call.__call__`. Make sure to delete cached data after testing.
- in .`__call__()` first try to read from disk.
***

## Done
- Don't fail on >5000 calls within the same Multicall in the same block.
- Make robust to RPC call timeouts and failures on the node provider's end




