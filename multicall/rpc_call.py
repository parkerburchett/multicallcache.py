import aiohttp
import asyncio

import json
from web3.providers import HTTPProvider
from aiolimiter import AsyncLimiter


async def async_rpc_eth_call(w3: HTTPProvider, rpc_args, session: aiohttp.ClientSession, rate_limiter: AsyncLimiter):
    async with rate_limiter:
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
        ) as response:
            response.raise_for_status()
            data = await response.json()
            return bytes.fromhex(data["result"][2:])


def sync_rpc_eth_call(w3: HTTPProvider, rpc_args):
    """Make a single rpc ETH call. Useful for testing"""
    return asyncio.run(_single_client_session_rpc_eth_call(w3, rpc_args))


async def _single_client_session_rpc_eth_call(w3: HTTPProvider, rpc_args):
    rate_limiter = AsyncLimiter(max_rate=1, time_period=1)  # 1 call/second

    async with aiohttp.ClientSession() as session:
        return await async_rpc_eth_call(w3, rpc_args, session, rate_limiter)
