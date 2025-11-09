from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.item_list, name="item_list"),
    path("items/new/", views.item_create, name="item_create"),
    path("items/<int:pk>/", views.item_detail, name="item_detail"),
    path("items/<int:pk>/delete/", views.item_delete, name="item_delete"),
    path("items/<int:pk>/edit/", views.item_edit_inline, name="item_edit_inline"),
    path("items/<int:pk>/images/add/", views.item_image_add_hx, name="item_image_add_hx"),
    path("items/<int:pk>/images/<int:image_id>/cover/", views.item_image_set_cover_hx, name="item_image_set_cover_hx"),
    path("items/<int:pk>/images/<int:image_id>/delete/", views.item_image_delete_hx, name="item_image_delete_hx"),


    path("me/items/", views.my_items, name="my_items"),

    path("loans/", views.my_loans, name="my_loans"),
    path("loans/request/<int:item_id>/", views.loan_request, name="loan_request"),
    path("loans/<int:loan_id>/accept/", views.loan_accept, name="loan_accept"),
    path("loans/<int:loan_id>/decline/", views.loan_decline, name="loan_decline"),
    path("loans/<int:loan_id>/cancel/", views.loan_cancel, name="loan_cancel"),
    path("loans/<int:loan_id>/hand-over/", views.loan_hand_over, name="loan_hand_over"),
    path("loans/<int:loan_id>/return/", views.loan_mark_returned, name="loan_mark_returned"),

    path("register/", views.register, name="register"),

    path("me/profile/", views.profile_edit, name="profile_edit"),

    path("u/<str:username>/", views.profile_detail, name="profile_detail"),
    path("u/<str:username>/items/", views.owner_items, name="owner_items"),
]
