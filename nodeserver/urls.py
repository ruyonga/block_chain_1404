from django.urls import path

from . import views

urlpatterns = [
 
    #ex: /api/create_transaction/
    path("new_transaction/", views.new_transaction, name="new_transaction"),
    #ex /api/chain/
    path("chain/", views.get_chain, name="get_chain"),
    #ex /api/mine/
    path("mine/", views.mine_unconfirmed_transactions, name="mine"),
    #ex /api/register_node/
    path("register_node/", views.register_new_peers, name="register_node"),
    #ex /api/register_with/
    path("register_with/", views.register_with_existing_node, name="register_with"),
    
    #ex /api/add_block
    path("add_block/", views.verify_and_add_block, name="add_block"),

    #ex /api/pending_txns
    path("pending_txns", views.get_pending_txns, name="pending_txns"),
    
]