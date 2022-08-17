# Profiler

This is a memory and runtime profiler for `multicall.py`.

## Usage

It is recommended to use the profiler in a newly created virtual environment.

1. Create a `conf.json` file in this directory with the following format:

``` json
{
    "profile_memory": true,
    "profile_runtime": true,
    "networks": {
        "1": "https://mainnet.infura.io/v3/53b5",
        "250": "https://rpcapi-tracing.fantom.network"
    }
}
```

2. Run the following commands to install the profiler depedencies:


``` sh
# install multicall
pip install ..
pip install -r requirements.txt
```

3. Run the profiler with json input files as arguments:

``` sh
python bench.py multicall1.json multicall2.json
```

## Format of Multicall json files

The multicall json files given as input must be in the following format:

``` json
{
    "workers": 100,
    "require_success": true,
    "chain_id": 1,
    "calls": [
        [
            "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
            "totalSupply()(uint256)"
        ],
        [
            "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            "balanceOf(address)(uint256)",
            "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc"
        ]
    ]
}
```
