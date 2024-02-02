from django.urls import path
from .views import RegisterView, LoginView, get_current_user, logout

urlpatterns = [
    path('register/', RegisterView.as_view(), name='user-register'),
    path('login/', LoginView.as_view(), name='user-login'),
    path('logout/', logout, name='user-logout'),
    path('current/', get_current_user, name='get-profile'),
]