from django.urls import path

from . import views
app_name = "client"
urlpatterns = [
    # ex: /client/
    path("", views.index, name="index"),
    # ex: /client/create_transaction/
    path("create_transaction/", views.create_transaction,  name="create-transaction"),
     # ex: /api/create_transaction/
    path("new_transaction/", views.new_transaction, name="new-transaction"),
    # ex /api/chain/
    path("chain/", views.get_chain, name="get-chain"),
    # ex /api/mine/
    path("mine/", views.mine_unconfirmed_transactions, name="mine"),
    # ex /api/register_node/
    path("register_node/", views.register_new_peers, name="register-node"),
    # ex /api/register_with/
    path("register_with/", views.register_with_existing_node, name="register-with-existing-node"),

    # ex /api/add_block
    path("add_block/", views.verify_and_add_block, name="add-block"),
    # ex /api/pending_txns
    path("pending_txns", views.get_pending_txns, name="pending-txns"),
]
