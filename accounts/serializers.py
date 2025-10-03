from rest_framework import serializers
from .models import User , UserProfile
import random
from .utils import send_otp_via_email 
from django.contrib.auth import authenticate


def generate_otp():
    return str(random.randint(1000, 9999))
class UserRegistrationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,)

    class Meta:
        model = User
        fields = ['full_name', 'email', 'password', 'role']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        email = validated_data['email']
        
        user = User.objects.filter(email=email).first()

        if user:
            if user.is_active:
          
                raise serializers.ValidationError({'error': 'This email is already registered and verified.'})
            else:
                user.set_password(validated_data['password'])
                user.full_name = validated_data.get('full_name', user.full_name)
                
                new_otp = generate_otp()
                user.otp = new_otp
                user.save()
                
                send_otp_via_email(user.email, new_otp)
                return user
        else:
            new_user = User.objects.create_user(**validated_data)
            
            new_otp = generate_otp()
            new_user.otp = new_otp
            new_user.save()
            
            send_otp_via_email(new_user.email, new_otp)
            return new_user



class UnifiedVerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=4)
    purpose = serializers.ChoiceField(choices=["registration", "password_reset"])

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data.get('email'), password=data.get('password'))
        if not user or not user.is_active:
            raise serializers.ValidationError("Incorrect email or password, or account not verified.")
        data['user'] = user
        return data

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()




class UserProfileSerializer(serializers.ModelSerializer):

    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)

    class Meta:
        model = UserProfile
        fields = ['user_id', 'user_email', 'is_subscribed']


class UserSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['is_subscribed']