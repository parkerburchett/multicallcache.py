from multicall.signature import Signature
from multicall.call import Call
from multicall.multicall import Multicall, _initialize_multiprocessing

# try to use forkserver/spawn
_initialize_multiprocessing()
