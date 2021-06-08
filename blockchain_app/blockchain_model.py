from exceptions import OverSpentError, InvalidHashError
from utils import custom_hash, encode_key, decode_key

from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from typing import ClassVar, DefaultDict, Deque, Dict, List, Optional

from datetime import datetime
from functools import reduce
import rsa
import uuid        
    
@dataclass(order=True)
class Transaction:
    recipient: str
    amount: int
    timestamp: datetime = field(default_factory=datetime.now, repr=True)
    signature: bytes = field(init=False, repr=False)
    is_spent: bool = field(default=False, repr=False)
    
    input_transactions: List['Transaction'] = field(default_factory=list, repr=False)
    
    @property
    def hash_id(self) -> None:
        return custom_hash(self)
        
    def __dict__(self, keys: Optional[List[str]] = ['timestamp', 'recipient', 'amount']) -> Dict:
        keys = keys
        d = asdict(self)
        res = {key: d[key] for key in d.keys() & keys}
        
        return res
    
    @property
    def balance(self) -> int:
        if not self.input_transactions:  # it means it's reward transaction
            return self.amount
        b = reduce(lambda x, y: x+y, [t.amount for t in self.input_transactions]) - self.amount
        return b
    
    @classmethod
    def balance_transaction(cls, transaction):
        balance_tx = Transaction(
            recipient = transaction.input_transactions[0].recipient,
            amount = transaction.balance,
            input_transactions = transaction.input_transactions
        )
        
        return balance_tx
    
    REWARD_UNITS: ClassVar[int] = 30
    
    @classmethod
    def reward_transcation(cls, block_miner: str):
        tx = Transaction(
                recipient=block_miner,
                amount=Transaction.REWARD_UNITS,
                )
        return tx
        
        
@dataclass(order=True)
class Block:
    previous_hash: str
    nonce: int
    miner: str
    timestamp: datetime = field(default_factory=datetime.now, repr=True)
    transactions: Deque[Transaction] = field(default_factory=deque, repr=True)
    
    def __repr__(self):
        msg = f"Block(previous_hash={self.previous_hash[:15]})"
        return msg
    
    def __dict__(self, keys: Optional[List[str]]) -> Dict:
        if not keys:
            keys = ['previous_hash', 'timestamp', 'miner', 'nonce', 'transactions']
        d = asdict(self)
        res = {key: d[key] for key in d.keys() & keys}
        
        return res
    
    MINE_DIFFICULTY: ClassVar[int] = 4
    FIRST_NONCE: ClassVar[int] = 100

    @classmethod
    def proof_of_work(cls, block):
        nonce = 0
        
        while True:
            _hash = custom_hash(block, nonce)
            if _hash[:Block.MINE_DIFFICULTY] == "0"*Block.MINE_DIFFICULTY:
                break
            else:
                nonce += 1
                
        return _hash, nonce
    

@dataclass(unsafe_hash=True)
class Peer:
    node: object = field(repr=False)
    pubkey: str = field(default='')
    
    NBITS: ClassVar[int] = 512
    
    def __post_init__(self) -> None:
        pk, self.privkey = rsa.newkeys(self.NBITS)
        self.pubkey = decode_key(pk)
        
    def sign_transaction(self, transaction: Transaction):
        signature = rsa.sign(str(transaction).encode(), self.privkey, 'SHA-256')
        transaction.signature = signature
        
    def send_transaction(self, recipient_address, amount):
        assert self.pubkey != recipient_address
        tx = Transaction(
            recipient=recipient_address,
            amount=amount
        )
        self.sign_transaction(tx)
        balance_tx = self.node.submit_transaction(self.pubkey, tx)
        if balance_tx:
            self.sign_transaction(balance_tx)
            self.node.submit_transaction(self.pubkey, balance_tx, is_balance=True)
        else:
            return "Invalid Transaction"
        return tx


@dataclass
class BlockChain:
    chain: Deque[Block] = field(default_factory=deque, repr=False)
    current_transactions:Deque[Transaction] = field(default_factory=deque, repr=False)
    peer_transactions: DefaultDict(Deque) = field(default_factory=lambda: defaultdict(deque), repr=False)
    
    def __repr__(self):
        if self.chain:
            return f"BlockChain(last_block=<{self.chain[0]}>)"
        else:
            return "BlockChain()"
    
    
@dataclass
class Node:
    nodes: List = field(default_factory=list, repr=False)
    peers: List[Peer] = field(default_factory=list, repr=False)
    uuid: str = field(default_factory=uuid.uuid4)
    
    def __post_init__(self):
        self.blockchain = BlockChain()
        self.peer = self.set_peer()
        # self.network = self.get_network
        # if self.network:
        if self.nodes:
            self.blockchain = self.get_chain_from_network()
        else:
            self.mine_block()
    
    def get_peer(self, address) -> Peer:
        # return self.peers.index()
        return [p for p in self.peers if p.pubkey==address][0]
    
    def set_peer(self) -> Peer:
        peer = Peer(node=self)
        self.peers.append(peer)
        return peer
    
    def mine_block(self):
        self.verify_chain(self.blockchain.chain)
    
        try:
            last_block = self.blockchain.chain[0]
        except IndexError:
            last_block = Block.FIRST_NONCE

        hash_id, nonce = Block.proof_of_work(last_block)
        new_block = Block(
            previous_hash=hash_id,
            nonce=nonce,
            miner=self.peer.pubkey
            )
        self.txs_to_block(new_block)
        self.blockchain.chain.appendleft(new_block)

        return new_block
    
    def txs_to_block(self, block: Block) -> None:
        reward_tx = Transaction.reward_transcation(block.miner)
        self.blockchain.peer_transactions[block.miner].appendleft(reward_tx)
        self.blockchain.current_transactions.appendleft(reward_tx)
        block.transactions = self.blockchain.current_transactions.copy()
        self.blockchain.current_transactions.clear()
    
    def submit_transaction(self, sender_address: str, new_tx: Transaction, is_balance=False):
        if is_balance:
            self.blockchain.current_transactions.appendleft(new_tx)
            self.blockchain.peer_transactions[sender_address].appendleft(new_tx)
            return True
        
        input_txs = [tx for tx in self.blockchain.peer_transactions[sender_address] if not tx.is_spent]
        new_tx.input_transactions = input_txs
        
        if new_tx.balance < 0:
            raise OverSpentError(sender=sender_address, amount=new_tx.balance)
            print("overspent")

        for tx in new_tx.input_transactions:
            tx.is_spent = True
            
        self.blockchain.current_transactions.appendleft(new_tx)
        self.blockchain.peer_transactions[new_tx.recipient].appendleft(new_tx)
        
        balance_tx = Transaction.balance_transaction(new_tx)
        return balance_tx
    
    @staticmethod
    def verify_transaction(sender_address: str, transaction: Transaction):
        try:
            sender_address = encode_key(sender_address)
            rsa.verify(str(transaction).encode(), transaction.signature, sender_address)
            return "The signature is valid"
        except rsa.VerificationError as e:
            print(e)
            print("Invalid signature!")
    
    @staticmethod
    def verify_block(block: Block, previous_block: Block):
        target_hash = custom_hash(previous_block, block.nonce)
        
        if block.previous_hash != target_hash:
            raise InvalidHashError(
                target_hash=target_hash,
                registered_hash=block.previous_hash)
            
    def verify_chain(self, bc: BlockChain):
        chain = bc.copy()
        while len(chain) > 1:
            last_block = chain[0]
            previous_block = chain[1]
            
            self.verify_block(last_block, previous_block)
            for tx in last_block.transactions:
                if tx.input_transactions:
                    sender_address = tx.input_transactions[0].recipient
                    self.verify_transaction(sender_address, tx) #TODO: verify transaction exception
                else:
                    pass
            chain.popleft()
            continue
        return "This chain is valid"
    
    def get_chain(self):
        pass
    
    def broadcast(self):
        pass
    
    def get_network(self):
        pass