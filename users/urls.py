from django.urls import path
from . import views


urlpatterns = [
    path("create_user", views.add_user, name="add_user"),
    path("get_users", views.get_users, name="get_users"),
    path("delete_user/<int:pk>", views.delete_user, name="delete_user"),
    path("update_user/<int:pk>", views.update_user, name="update_user"),
    path("disable_user/<int:user_id>", views.disable_user, name="disable_user"),
    path("toggle_user/<int:user_id>", views.toggle_user, name="toggle_user"),
    path("change_password/<int:user_id>", views.change_password, name="change_password"),
]
