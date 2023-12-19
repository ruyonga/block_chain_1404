from django.urls import path

from . import views
app_name = "client"
urlpatterns = [
    # ex: /client/
    path("", views.index, name="index"),

    # ex: /client/create_transaction/
    path("create_transaction/", views.create_transaction,
         name="create_transaction"),

]
