from django.urls import path
from .views import (
    UserRegistrationView,
    UnifiedVerifyOTPView,
    LoginView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    ChangePasswordView,
    LogoutView,

    UserProfileView ,
    UserSubscriptionUpdateView
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('verify-otp/', UnifiedVerifyOTPView.as_view(), name='verify-otp'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    path('password-reset/request/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),

    # Simple JWT's built-in URLs
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
  
 


    path('user-details/', UserProfileView.as_view(), name='user-profile'),
    path('update/', UserSubscriptionUpdateView.as_view(), name='user-subscription-update'),
]
