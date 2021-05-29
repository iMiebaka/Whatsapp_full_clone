from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views
from rest_framework.authtoken import views as api_auth_views

app_name = 'accounts'
urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path("login/", views.login, name="login"),
    path("logout/", views.logout_view, name="logout_view"),
    path("add-contact-create-group/<int:slider>", views.add_options, name="add_options"),
    path("add-contact/", views.add_contact, name="add_contact"),
    path("add-to-chat/", views.add_to_chat, name="add_to_chat"),
    path("create-group", views.create_group, name="create_group"),
    path('view-profile/', views.view_profile, name='view_profile'),
    path('ajax/check-status/', views.check_status, name='check_status'),
    path("activate/verify-account-sms/", views.verify_account_sms, name="verify_account_sms"),
]
