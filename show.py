from blockchain_app.blockchain_model import Block, Transaction, Node
from pprint import pprint

def show_block(block, blockchain):
    index = len(blockchain)-(blockchain.index(block)+1)
    print("---"*15)
    print(f"Block {index}")
    print(f"\tprevious_hash: {block.previous_hash[:40]}")
    print(f"\tnonce: {block.nonce}")
    print(f"\tminer: {block.miner}")
    print(f"\ttimestamp: {block.timestamp}")
    print(f"\ttranscations:")
    for tx in block.transactions:
        try:
            sender = tx.input_transactions[0].recipient
        except IndexError:
            sender = None
        print(f"\t\t{sender} -> {tx.recipient} / {tx.amount} coins")
    print("---"*15)
    print()
    print()
    
def show_transaction(transaction: Transaction):
    pass