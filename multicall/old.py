
# class Multicall:
#     def __init__(
#         self,
#         calls: List[Call],
#         batch_size: Optional[int] = None,
#         block_id: Optional[int] = None,
#         gas_limit: int = 550_000_000, # they should not have control over the gas limit, move to constanrts #2_147_483_648, # 1 << 31, # not sure how much this matters, # see the latency of this 1 call vs 100_000 total supply
#         retries: int = 3, # odd default, not sure why they picked this. 
#         require_success: bool = True,
#         _w3: Optional[Web3] = None,
#         max_conns: int = 20,
#         max_workers: int = min(12, multiprocessing.cpu_count() - 1),
#         # when the number of function calls to execute is above this threshold, multiprocessing is used
#         parallel_threshold: int = 1,
#         # timeout in seconds for a multicall batch
#         batch_timeout: int = 300,
#     ) -> None:
#         self.calls = calls
#         self.batch_size = ( ### update this as well since many of the calls are redundent
#             batch_size if batch_size is not None else -(-len(calls) // max_conns) # not sure why neg len calls
#         )
#         self.block_id = block_id
#         self.gas_limit = gas_limit
#         self.retries = retries
#         self.require_success = require_success
#         self.node_uri = _w3.provider.endpoint_uri if _w3 else None
#         self.max_workers = max_workers
#         self.parallel_threshold = parallel_threshold if max_workers > 1 else 1 << 31
#         self.max_conns = max_conns
#         self.chainid = chain_id(_w3)
#         # ugly
#         if require_success is True:
#             multicall_map = (
#                 MULTICALL_ADDRESSES
#                 if self.chainid in MULTICALL_ADDRESSES
#                 else MULTICALL2_ADDRESSES
#             )
#             self.multicall_sig = "aggregate((address,bytes)[])(uint256,bytes[])"
#         else:
#             multicall_map = MULTICALL2_ADDRESSES
#             self.multicall_sig = "tryBlockAndAggregate(bool,(address,bytes)[])(uint256,uint256,(bool,bytes)[])"
#         self.multicall_address = multicall_map[self.chainid]
#         self.batch_timeout = batch_timeout

#     def __repr__(self) -> str:
#         return f'Multicall {", ".join(set(map(lambda call: call.function, self.calls)))}, {len(self.calls)} calls'

#     def __call__(self) -> Dict[str, Any]:
#         if len(self.calls) == 0:
#             return {}

#         start = time()
#         response: Dict[str, Any]
#         with multiprocessing.Pool(processes=self.max_workers) as multiprocessing_pool:
#                 response = self.fetch_outputs(multiprocessing_pool)
#         logger.debug(f"Multicall took {time() - start}s")
#         print(f"Multicall took {time() - start}s")
#         return response

#     def encode_args(self, calls_batch: List[Call]) -> List[Dict]:
#         args = get_args(calls_batch, self.require_success)
#         calldata = f"0x{self.aggregate.signature.encode_data(args).hex()}"

#         args = [
#             {"to": self.aggregate.target, "data": calldata},
#             hex(self.block_id) if self.block_id is not None else "latest",
#         ]

#         if self.gas_limit:
#             args[0]["gas"] = f"0x{self.gas_limit:x}"

#         return args

#     def decode_outputs(self, calls_batch: List[Call], result: bytes):
#         if self.require_success is True:
#             _, outputs = Call.decode_output(
#                 result, self.aggregate.signature, self.aggregate.returns
#             )
#             outputs = unpack_aggregate_outputs(outputs)
#         else:
#             _, _, outputs = Call.decode_output(
#                 result, self.aggregate.signature, self.aggregate.returns
#             )

#         outputs = [
#             Call.decode_output(output, call.signature, call.returns, success)
#             for call, (success, output) in zip(calls_batch, outputs)
#         ]

#         return {name: result for output in outputs for name, result in output.items()}

#     async def rpc_eth_call(self, session: aiohttp.ClientSession, args) -> bytes | EthRPCError:
#         """Make the multicall with many calls in it"""
#         async with session.post(
#             self.node_uri,
#             headers={"Content-Type": "application/json"},
#             data=json.dumps(
#                 {
#                     "params": args,
#                     "method": "eth_call",
#                     "id": 1,
#                     "jsonrpc": "2.0",
#                 }
#             ),
#         ) as response:

#             assert response.status == 200, RuntimeError(f"Network Error: {response}")
#             data = await response.json()
#             if "error" in data:
#                 if "out of gas" in data["error"]["message"]:
#                     return EthRPCError.OUT_OF_GAS
#                 elif "execution reverted" in data["error"]["message"]:
#                     return EthRPCError.EXECUTION_REVERTED
#                 else:
#                     return EthRPCError.UNKNOWN
#             result = bytes.fromhex(data["result"][2:])
#             return result

#     async def rpc_aggregator(
#         self, args_list: List[List]
#     ) -> List[Union[EthRPCError, bytes]]:
#         """
#         Make multiple Multicalls for each batch in args_list

#         each rpc_eth_call returns a error or a
        
#         """

#         async with aiohttp.ClientSession(
#             connector=aiohttp.TCPConnector(limit=self.max_conns),
#             timeout=aiohttp.ClientTimeout(self.batch_timeout),
#         ) as session:
#             return await asyncio.gather(
#                 *[self.rpc_eth_call(session, args) for args in args_list]
#             )

#     def fetch_outputs_refactored(self, p: Optional[multiprocessing.Pool]) -> Dict[str, Any]:
#         calls = self.calls
#         outputs = {}

#         # desired behavior

#         # try all calls in 1 multicall

#         # if multicall fails because of EthRPCError.OUT_OF_GAS

#         # split into two chunks, add calls chunks to queue.

#         # add to calls, try again?

#         # do while calls > 0

#         for num_batches in range(1, self.retries):
#             # useful because if the the calls fails you can break it up into more chunks
#             batches = np.array_split(calls, num_batches)
#             encoded_args = list(
#                     p.imap(
#                         self.encode_args,
#                         batches,
#                         chunksize=-(-len(batches) // self.max_workers),
#                     )
#                 )
            
#             results = asyncio.run(self.rpc_aggregator(encoded_args)) # not sure type of results
#             if self.require_success and EthRPCError.EXECUTION_REVERTED in results:
#                 raise RuntimeError("Multicall with require_success=True failed.")

#             # find remaining calls 
#             # how big an issue is out of gas issues?

#             # make calls be all the calls in each of the batches that failed.
#             # I think the default behavior should be binary search on the batches. 
#             # get an intutition for the gas costs. that make it fail
#             # how many balanceOf make it fail? on Alchemy
#             calls = list(
#                 itertools.chain(
#                     *[
#                         batches[i]
#                         for i, x in enumerate(results)
#                         if x == EthRPCError.OUT_OF_GAS
#                     ]
#                 )
#             )

#             successes = [
#                 (batch, result)
#                 for batch, result in zip(batches, results)
#                 if not isinstance(result, EthRPCError)
#             ]
#             batches, results = zip(*successes) if len(successes) > 0 else ([], []) # added >0 for readablity

#             outputs.update(
#                     ChainMap(
#                     *p.starmap(
#                     self.decode_outputs,
#                     zip(batches, results),
#                     chunksize=-(-len(batches) // self.max_workers),
#                     )
#                 )
#             )

#         return outputs

#     @property
#     def aggregate(self) -> Call:
#         return Call(
#             self.multicall_address,
#             self.multicall_sig,
#             returns=None,
#             block_id=self.block_id,
#             _w3=Web3(HTTPProvider(self.node_uri)),
#             gas_limit=self.gas_limit,
#         )
