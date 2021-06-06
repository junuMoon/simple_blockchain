from .utils import custom_hash, valid_chain

from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from typing import ClassVar, DefaultDict, Deque, Dict, List, Optional

from datetime import datetime
from functools import reduce
import rsa
        
    
@dataclass(order=True)
class Transaction:
    recipient: str
    amount: int
    timestamp: datetime = field(default_factory=datetime.now, repr=True)  # default_factory=datetime.now() -> 'datetime.datetime' object is not callable. 
    signature: bytes = field(init=False, repr=False)
    is_spent: bool = field(default=False, repr=False)
    
    input_transactions: List['Transaction'] = field(default_factory=list, repr=False)
    
    def __post_init__(self) -> None:
        self.hash_id = custom_hash(self)
        
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
        if b < 0:
            raise AttributeError("The required amount of coins exceed the balance")
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


@dataclass(unsafe_hash=True)
class Node:
    name: str
    
    def __post_init__(self) -> None:
        (self.pubkey, self.privkey) = rsa.newkeys(512)
        
    def sign_transaction(self, transaction: Transaction):
        signature = rsa.sign(str(transaction).encode(), self.privkey, 'SHA-256')
        transaction.signature = signature
        
        
@dataclass(order=True)
class Block:
    previous_hash: str
    nonce: int
    miner: str
    timestamp: datetime = field(default_factory=datetime.now, repr=True)
    transactions: Deque[Transaction] = field(default_factory=deque, repr=False)
    
    def __dict__(self, keys: Optional[List[str]] = ['previous_hash', 'timestamp', 'miner', 'nonce', 'transactions']) -> Dict:
        keys = keys
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
    

blockchain = deque()                            # type: Deque[Block]
current_transactions = deque()                  # type: Deque[Transaction]
node_transactions = defaultdict(deque)          # type: DefaultDict[Node, Deque[Transaction]]
nodes = set()                                   # type: set(Node)


def mine_block(miner: str) -> None:
    valid_chain(blockchain=blockchain)
    
    try:
        last_block = blockchain[0]
    except IndexError:
        last_block = Block.FIRST_NONCE

    hash_id, nonce = Block.proof_of_work(last_block)
    new_block = Block(
        previous_hash=hash_id,
        nonce=nonce,
        miner=miner             
        )
    _txs_to_block(miner, new_block)
    blockchain.appendleft(new_block)
    
def _txs_to_block(node_name: str, block: Block) -> None:
    reward_tx = Transaction.reward_transcation(node_name)
    node_transactions[node_name].appendleft(reward_tx)
    current_transactions.appendleft(reward_tx)
    block.transactions = current_transactions.copy()
    current_transactions.clear()

def submit_transaction(sender_address: str, recipient_address: str, amount: int) -> None:
    assert sender_address != recipient_address
    sender = get_node(sender_address)
    
    input_txs = list()
    for tx in node_transactions[sender_address]:
        if not tx.is_spent:
            tx.is_spent = True
            input_txs.append(tx)    
        
    new_tx = Transaction(
        recipient=recipient_address,
        amount=amount,
        input_transactions=input_txs
    )
    sender.sign_transaction(new_tx) 
    current_transactions.appendleft(new_tx)
    node_transactions[recipient_address].appendleft(new_tx)
    
    balance_tx = Transaction.balance_transaction(new_tx)
    sender.sign_transaction(balance_tx)
    current_transactions.appendleft(balance_tx)
    node_transactions[sender_address].appendleft(balance_tx)
    
def verify_transaction(sender_address, transaction: Transaction) -> None:
    try:
        sender = get_node(sender_address)
        rsa.verify(str(transaction).encode(), transaction.signature, sender.pubkey)
        print("The signature is valid")
    except rsa.VerificationError:
        print("Invalid signature!")

def set_node(name: str) -> None:        
    if any(list(filter(lambda x: x.name==name, nodes))):
        raise AttributeError("The name is already used by existing object")
            
    n = Node(name=name)
    nodes.add(n)

def get_node(name: str) -> None:
    node = [n for n in nodes if n.name == name]
    return node[0]
