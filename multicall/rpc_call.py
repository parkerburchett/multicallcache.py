import aiohttp
import asyncio
import time

import json
from web3.providers import HTTPProvider
from aiolimiter import AsyncLimiter
import requests

RETRY_COUNT = 3  # Number of retries for the HTTP request


async def async_rpc_eth_call(w3: HTTPProvider, rpc_args, session: aiohttp.ClientSession, rate_limiter: AsyncLimiter):
    # Note not very robust to rate limiting problems
    # TODO make more robust
    async with rate_limiter:
        for attempt in range(RETRY_COUNT):
            try:
                async with session.post(
                    w3.provider.endpoint_uri,
                    headers={"content-type": "application/json"},
                    data=json.dumps(
                        {
                            "params": rpc_args,
                            "method": "eth_call",
                            "id": 1,
                            "jsonrpc": "2.0",
                        }
                    ),
                    timeout=20,  # consider making this a parameter
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return bytes.fromhex(data["result"][2:])
                    elif response.status == 413:
                        print("the payload is too large, you need to have less calls per multicall")
                        response.raise_for_status()

                    elif (response.status == 429) and (attempt < RETRY_COUNT - 1):
                        print(
                            f"429 error, waiting to retry, exceeded alchemy compute units /s {attempt=} with {rate_limiter.max_rate=} rpc calls / second"
                        )
                        await asyncio.sleep(2**attempt)
            except Exception as e:
                if attempt < RETRY_COUNT - 1:
                    print(str(e), type(e), attempt, "now sleeping")
                    await asyncio.sleep(2**attempt)
                else:
                    raise e

    raise ValueError("should never get here")


def sync_rpc_eth_call(w3, rpc_args):
    endpoint_uri = w3.provider.endpoint_uri  # Assuming this is accessible like this
    headers = {"content-type": "application/json"}
    data = json.dumps({"params": rpc_args, "method": "eth_call", "id": 1, "jsonrpc": "2.0"})

    for attempt in range(RETRY_COUNT):
        try:
            response = requests.post(endpoint_uri, headers=headers, data=data, timeout=10)
        except TimeoutError:
            continue
        if response.status_code == 200:
            data = response.json()
            return bytes.fromhex(data["result"][2:])
        elif response.status_code == 413:
            print("the payload is too large, you need to break up the calls")
            raise Exception("Payload too large")
        elif response.status_code == 429 and attempt < RETRY_COUNT - 1:
            print(f"429 error, waiting to retry, attempt {attempt}")
            time.sleep(2**attempt)  # Exponential backoff
        else:
            response.raise_for_status()
