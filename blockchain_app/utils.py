from functools import reduce
from hashlib import sha256

def custom_hash(*args) -> str:
    s = reduce(lambda x, y: str(x)+str(y), args)
    _hash = sha256(str(s).encode()).hexdigest()
    return _hash

def valid_chain(blockchain) -> bool:
    chain = blockchain.copy()
    valid = True
    while len(chain) > 1:
        last_block = chain[0]
        previous_block = chain[1]
        
        target_hash = custom_hash(previous_block, last_block.nonce)
        if last_block.previous_hash != target_hash:
            raise AttributeError("Invalid Chain")
        else:
            chain.popleft()
            continue
    return True