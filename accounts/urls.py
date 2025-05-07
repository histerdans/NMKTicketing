from django.urls import path

from .views import register_page, login_page, logout_user, profile_page

app_name = 'accounts'
urlpatterns = [

    path('login/', login_page, name='login'),
    path('logout/', logout_user, name='logout'),
    path('register/', register_page, name='register'),
    path('ajax/<int:pk>', profile_page, name='url_profile'),
]
