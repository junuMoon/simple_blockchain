import imp
import session
from blockchain_model import blockchain, current_transactions, node_transactions, nodes
from blockchain_model import get_node, set_node, mine_block, submit_transaction
from bottle import view, post, get
from bottle import template, request


@get('/')
@view('main')
def show_index(block_hash=None):
    blocks = blockchain
    if block_hash:
        block = [b for b in blocks if b.previous_hash==block_hash][0]
        transactions = block.transactions
    else:
        transactions = current_transactions
        
    return dict(block_hash=block_hash,
                blocks=blocks,
                transactions=transactions,
                )

# @post('/block/mine')
# def new_block():
#     miner = request.forms.get('miner')

# @post('/transaction/submit')
# def new_transaction():
#     sender = request.forms.get('sender')
#     recipient = request.forms.get('recipient')
#     amount = request.forms.get('amount')
#     submit_transaction(sender=sender, recipient=recipient, amount=amount)