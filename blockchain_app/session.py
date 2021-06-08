from blockchain_model import BlockChain, Block, Transaction
from blockchain_model import Node, Peer


node_김상수 = Node()
김상수 = node_김상수.peer
김소연 = node_김상수.set_peer()
기슬기 = node_김상수.set_peer()
이효겸 = node_김상수.set_peer()

tx = 김상수.send_transaction(김소연.pubkey, 10)
node_김상수.mine_block()
김상수.send_transaction(이효겸.pubkey, 10)
김상수.send_transaction(김소연.pubkey, 10)
김상수.send_transaction(기슬기.pubkey, 10)
node_김상수.mine_block()
기슬기.send_transaction(김소연.pubkey, 6)
print(node_김상수.blockchain.chain)

# input()
node_문준우 = Node([node_김상수])
문준우 = node_문준우.peer
정한진 = node_문준우.set_peer()
박선호 = node_문준우.set_peer()

# 문준우.send_transaction(정한진.pubkey, 10)

# print('moon', node_문준우.blockchain.current_transactions)
# print('kim', node_김상수.blockchain.current_transactions)
# node_문준우.mine_block()

# node_문준우.consensus()