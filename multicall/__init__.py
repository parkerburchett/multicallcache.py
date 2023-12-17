from multicall.signature import Signature
from multicall.call import Call
from multicall_theirs.multicall import Multicall, MulticallV2, Call, _initialize_multiprocessing

# try to use forkserver/spawn
_initialize_multiprocessing()
