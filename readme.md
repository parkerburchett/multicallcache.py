# multicallcache.py

Fork of https://github.com/Dedaub/multicall.py and https://github.com/banteg/multicall.py

## Primary Goal

- Read only function calls on finalized blocks are pure. For example, calling WETH.totalSupply() at block 15_000_000 will always return the same value. 

This is a wrapper around the Multicall series of contracts that maintains a local sqlite database that handles the caching and loading of historical EVM data. Speeds up and simplifies collecting and using EVM data. 


The end user only needs to specify the Calls and blocks. Then after collecting data once, instead of externally fetching it is read locally. 


State Id Columns:
1. Chain id
2. Block
3. Target Address
4. Function Signature
5. Function Args


Data Columns:
1. Response Success (bool)
2. Response Data (any data type)


Incidental goals:
- Refactor for clarity
- Simplify EVM data collection to a single method. 
- Add robustness for API failing. 
- Add more examples with complicated function signatures and return data types
- Stricter checks to not lose data in calls. (no duplicate names in calls)


DEV
- `pytest` to run the tests
- `black .`  to run the linter
- `ruff --fix` to run ruff