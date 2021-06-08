# import base_scenario
from base_scenario import blockchain, current_transactions, nodes
from blockchain_app.blockchain_model import set_node, submit_transaction, mine_block
from blockchain_app.utils import valid_chain
from show import show_block

for b in blockchain:
    show_block(b, blockchain)

input()
print(blockchain[1].transactions[2])
print(f"\thash id: {blockchain[1].transactions[2].hash_id}")
input()
print("blockchain[1].transactions[2].amount = 4")
blockchain[1].transactions[2].amount = 4
input()
print(blockchain[1].transactions[2])
print(f"\thash id: {blockchain[1].transactions[2].hash_id}")
input()
valid_chain(blockchain)

