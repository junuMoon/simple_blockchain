# from blockchain_app.exceptions import InvalidHashError
from functools import reduce
from hashlib import sha256
import rsa
import binascii

def custom_hash(*args) -> str:
    s = reduce(lambda x, y: str(x)+str(y), args)
    _hash = sha256(str(s).encode()).hexdigest()
    return _hash

def decode_key(key: rsa.key.PublicKey, key_format='DER') -> str:
    return binascii.hexlify(key.save_pkcs1(format=key_format)).decode()
    
def encode_key(decoded_key: str, key_format='DER') -> rsa.PublicKey:
    decoded_key:bytes = binascii.unhexlify(decoded_key.encode())
    return rsa.PublicKey.load_pkcs1(format=key_format, keyfile=decoded_key)

# def valid_chain(blockchain) -> bool:
#     chain = blockchain.copy()
#     valid = True
#     while len(chain) > 1:
#         last_block = chain[0]
#         previous_block = chain[1]
        
#         target_hash = custom_hash(previous_block, last_block.nonce)
#         if last_block.previous_hash != target_hash:
#             block_index = len(blockchain) - (blockchain.index(previous_block)+1)
#             raise InvalidHashError(
#                 target_hash=target_hash,
#                 registered_hash=last_block.previous_hash,
#                 block_index=block_index
#                 )
#         else:
#             chain.popleft()
#             continue
#     return "This chain is valid"