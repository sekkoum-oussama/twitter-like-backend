from django.urls import path, re_path
from dj_rest_auth.registration.views import RegisterView, VerifyEmailView
from dj_rest_auth.views import LoginView, LogoutView, PasswordChangeView
from dj_rest_auth.jwt_auth import get_refresh_view
from users.views import UserDetailView, UserTweetsView, userFollow, userUnfollow, getFollowers, getFollowing


urlpatterns = [
     path('register/', RegisterView.as_view()),
     path('login/', LoginView.as_view()),
     path('logout/', LogoutView.as_view()),

     path('password/change/', PasswordChangeView.as_view(),  name='rest_password_change'),

     path('account-confirm-email/<str:key>/',
               VerifyEmailView.as_view(), name='account_confirm_email'),

     path('follow/<str:username>/', userFollow, name='user-follow'),
     path('unfollow/<str:username>/', userUnfollow, name='user-unfollow'),
     path('<str:username>/', UserDetailView.as_view(), name='profile-detail'),
     path('<str:username>/tweets/', UserTweetsView.as_view(), name='user-tweets'),
     path('<str:username>/followers/', getFollowers, name='user-followers'),
     path('<str:username>/following/', getFollowing, name='user-following')
]