from blockchain_app.blockchain_model import set_node, submit_transaction, mine_block
from blockchain_app.blockchain_model import blockchain, current_transactions, nodes

set_node(name='kim')
set_node(name='junu')
set_node(name='emily')

mine_block('kim')
submit_transaction('kim', 'junu', 5)
submit_transaction('kim', 'emily', 10)
submit_transaction('junu', 'emily', 3)
mine_block('junu')
submit_transaction('junu', 'emily', 20)
mine_block('emily')
# submit_transaction('junu', 'stefania', 20)