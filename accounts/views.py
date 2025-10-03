from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
import random 
from .utils import send_otp_via_email
from .models import User , UserProfile
from .serializers import (
    UserRegistrationSerializer,

    UserProfileSerializer
)
import random
from datetime import datetime, timedelta
from django.utils import timezone

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }



import random
from django.core.mail import send_mail

def generate_otp():
    """Generates a 4-digit OTP as a string."""
    return str(random.randint(1000, 9999))

class UserRegistrationView(APIView):

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
       
        serializer = UserRegistrationSerializer(data=request.data)


        if serializer.is_valid():

            serializer.save()

            return Response({
                'message': 'Registration successful. Please check your email for the verification OTP.'
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, {"sorry "}, status=status.HTTP_400_BAD_REQUEST)






from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from .models import User
from .serializers import (
    UserRegistrationSerializer, UnifiedVerifyOTPSerializer, LoginSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    ChangePasswordSerializer, LogoutSerializer
)

from .utils import generate_otp, send_otp_via_email


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }





class UnifiedVerifyOTPView(APIView):
    def post(self, request):
        serializer = UnifiedVerifyOTPSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']
            purpose = serializer.validated_data['purpose']

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({'error': 'Invalid OTP or Email.'}, status=status.HTTP_400_BAD_REQUEST)

            if str(user.otp) == str(otp):
                if purpose == 'registration':
                    user.is_active = True
                    user.otp = None
                    user.save()
                    return Response({'msg': 'Email verified successfully. You can now log in.'}, status=status.HTTP_200_OK)
                elif purpose == 'password_reset':
                    return Response({'msg': 'OTP verified successfully. You can now set a new password.'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid OTP or Email.'}, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user = serializer.validated_data['user']
            tokens = get_tokens_for_user(user)
            return Response({
                "tokens": tokens,
                "user_info": {
                    "id": user.id,
                    "full_name": user.full_name,
                    "email": user.email,
                    "role": user.role, 
                    'is_subscribe': user.is_subscribed
                }
            }, status=status.HTTP_200_OK)

class PasswordResetRequestView(APIView):
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
                new_otp = generate_otp()
                user.otp = new_otp
                user.save()
                send_otp_via_email(user.email, new_otp)
            except User.DoesNotExist:
                pass
            return Response({'msg': 'If an account with this email exists, an OTP has been sent.'}, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            email, otp, password = (
                serializer.validated_data['email'],
                serializer.validated_data['otp'],
                serializer.validated_data['password']
            )
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({'error': 'Invalid email or OTP.'}, status=status.HTTP_400_BAD_REQUEST)

            if str(user.otp) == str(otp):
                user.set_password(password)
                user.otp = None
                user.save()
                return Response({'msg': 'Password has been reset successfully.'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid email or OTP.'}, status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user = request.user
            if not user.check_password(serializer.validated_data['old_password']):
                return Response({"error": "Incorrect old password."}, status=status.HTTP_400_BAD_REQUEST)
            
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({"msg": "Password changed successfully."}, status=status.HTTP_200_OK)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            try:
                refresh_token = serializer.validated_data["refresh"]
                token = RefreshToken(refresh_token)
                token.blacklist()
                return Response({"msg": "Logout successful."}, status=status.HTTP_205_RESET_CONTENT)
            except TokenError:
                return Response({"error": "Token is invalid or expired."}, status=status.HTTP_400_BAD_REQUEST)
# ---------------------------------------------------------------


class UserProfileView(APIView):
    
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
     
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            serializer = UserProfileSerializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, *args, **kwargs):
        try:

            profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            return Response({"error": "User profile not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    



from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .serializers import UserSubscriptionSerializer
from .models import User

class UserSubscriptionUpdateView(generics.UpdateAPIView):
    """
    Authenticated user-der nijeder 'is_subscribed' status update korar jonno
    ekta PATCH endpoint.
    """
    serializer_class = UserSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """
        Shudhu request-kari user-er object return korbe,
        jate onno karo profile update kora na jay.
        """
        return self.request.user

    def patch(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # is_subscribed status-er opor base kore role update kora hocche
        if user.is_subscribed:
            user.role = 'Premium'
        else:
            user.role = 'Free'
        user.save(update_fields=['role'])

        return Response({
            "message": "Subscription status updated successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def perform_update(self, serializer):
        serializer.save()