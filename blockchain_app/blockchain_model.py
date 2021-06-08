from blockchain_app.exceptions import OverSpentError
from blockchain_app.utils import custom_hash, valid_chain

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
    transactions: Deque[Transaction] = field(default_factory=deque, repr=True)
    
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
    

blockchain = deque()                            # type: Deque[Block]
current_transactions = deque()                  # type: Deque[Transaction]
node_transactions = defaultdict(deque)          # type: DefaultDict[Node, Deque[Transaction]]
nodes = set()                                   # type: set(Node)


def mine_block(miner: str) -> Block:
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
    
    return new_block
    
def _txs_to_block(node_name: str, block: Block) -> None:
    reward_tx = Transaction.reward_transcation(node_name)
    node_transactions[node_name].appendleft(reward_tx)
    current_transactions.appendleft(reward_tx)
    block.transactions = current_transactions.copy()
    current_transactions.clear()

def submit_transaction(sender_address: str, recipient_address: str, amount: int) -> List[Transaction]:
    assert sender_address != recipient_address
    sender = get_node(sender_address)
    
    input_txs = [tx for tx in node_transactions[sender_address] if not tx.is_spent]
        
    new_tx = Transaction(
        recipient=recipient_address,
        amount=amount,
        input_transactions=input_txs
    )
    
    if new_tx.balance < 0:
        raise OverSpentError(sender=sender.name, amount=new_tx.balance)
    else:
        # submit new transaction
        for tx in new_tx.input_transactions:
            tx.is_spent = True
        sender.sign_transaction(new_tx) 
        current_transactions.appendleft(new_tx)
        node_transactions[recipient_address].appendleft(new_tx)
        
        # submit balance transaction of new transaction
        balance_tx = Transaction.balance_transaction(new_tx)
        sender.sign_transaction(balance_tx)
        current_transactions.appendleft(balance_tx)
        node_transactions[sender_address].appendleft(balance_tx)

    return [new_tx, balance_tx]
    
def verify_transaction(sender_address, transaction: Transaction) -> None:
    try:
        sender = get_node(sender_address)
        rsa.verify(str(transaction).encode(), transaction.signature, sender.pubkey)
        return "The signature is valid"
    except rsa.VerificationError as e:
        print(e)
        print("Invalid signature!")

def set_node(name: str) -> None:        
    if any(list(filter(lambda x: x.name==name, nodes))):
        raise AttributeError("The name is already used by existing node")
            
    n = Node(name=name)
    nodes.add(n)

def get_node(name: str) -> None:
    node = [n for n in nodes if n.name == name]
    return node[0]
