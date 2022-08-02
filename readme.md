# multicall.py

python interface for makerdao's [multicall](https://github.com/makerdao/multicall) and a port of [multicall.js](https://github.com/makerdao/multicall.js)

## installation

```
pip install multicall
```

## example

```python
from brownie import web3
from multicall import Call, Multicall

# assuming you are on kovan
MKR_TOKEN = '0xaaf64bfcc32d0f15873a02163e7e500671a4ffcd'
MKR_WHALE = '0xdb33dfd3d61308c33c63209845dad3e6bfb2c674'
MKR_FISH = '0x2dfcedcb401557354d0cf174876ab17bfd6f4efd'

def from_wei(value):
    return value / 1e18

multi = Multicall(
    web3.web,
    [
        Call(MKR_TOKEN, ['balanceOf(address)(uint256)', MKR_WHALE], [['whale', from_wei]]),
        Call(MKR_TOKEN, ['balanceOf(address)(uint256)', MKR_FISH], [['fish', from_wei]]),
        Call(MKR_TOKEN, 'totalSupply()(uint256)', [['supply', from_wei]]),
    ]
)

multi()  # {'whale': 566437.0921992733, 'fish': 7005.0, 'supply': 1000003.1220798912}

# seth-style calls
Call(MKR_TOKEN, ['balanceOf(address)(uint256)', MKR_WHALE], w3=web3.web)()
Call(MKR_TOKEN, 'balanceOf(address)(uint256)', w3=web3.web)(MKR_WHALE)
# return values processing
Call(MKR_TOKEN, 'totalSupply()(uint256)', [['supply', from_wei]], w3=web3.web)()
```

## api

### `Signature(signature)`

- `signature` is a seth-style function signature of `function_name(input,types)(output,types)`. it also supports structs which need to be broken down to basic parts, e.g. `(address,bytes)[]`.

use `encode_data(args)` with input args to get the calldata. use `decode_data(output)` with the output to decode the result.

### `Call(target, function, returns=None, gas_limit=None, w3=None)`

- `target` is the `to` address which is supplied to `eth_call`.
- `function` can be either seth-style signature of `method(input,types)(output,types)` or a list of `[signature, *args]`.
- `returns` is a list of `[name, handler]` for return values. if `returns` argument is omitted, you get a tuple, otherwise you get a dict. to skip processing of a value, pass `None` as a handler.
- `w3` is a `Web3` instance to be used for the `eth_call`. If `None`, `Call(...)()` will raise a `RuntimeError`.

use `Call(...)()` with predefined args or `Call(...)(args)` to reuse a prepared call with different args.

use `decode_output(output)` with to decode the output and process it with `returns` handlers.

### `Multicall(w3, calls, batch_size=500, block_id=None, retries=3, require_success=True, workers=min(24, multiprocessing.cpu_count()))`

- `w3` is a `Web3` instance to be used for the multicalls.
- `calls` is a list of `Call`s with prepared values.
- `batch_size` is the size of batches to give to the multicall contract.
- `retries` is the number of times to attempt a failed batch.
- `require_success` determines whether or not all calls must be successful.
- `workers` is the number of threads used by the multicall (and hence the number of concurrent connections).


use `Multicall(...)()` to get the result of a prepared multicall.

### Environment Variables

- MULTICALL_DEBUG: if set, sets logging level for all library loggers to logging.DEBUG
