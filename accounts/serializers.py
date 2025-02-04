# accounts/serializers.py
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, PrimaryAccount, Member

class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = [
            'id', 'name', 'email', 
            'relationship', 'access_level', 
            'active_status', 'joined_at'
        ]
        read_only_fields = ['joined_at']


class PrimaryAccountSerializer(serializers.ModelSerializer):
    members = MemberSerializer(many=True, required=False)
    
    class Meta:
        model = PrimaryAccount
        fields = [
            'id', 'name', 'phone', 'address',
            'is_active', 'created_at', 'members'
        ]
        read_only_fields = ['created_at']

class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)
    primary_account = PrimaryAccountSerializer(required=True)

    class Meta:
        model = User
        fields = [
            'email', 'password', 'password2',
            'phone', 'primary_account'
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )
        return attrs

    def create(self, validated_data):
        # Extract primary account data
        primary_account_data = validated_data.pop('primary_account')
        
        # Create user
        user = User.objects.create(
            email=validated_data['email'],
            phone=validated_data.get('phone')
        )
        user.set_password(validated_data['password'])
        user.save()

        # Create primary account
        primary_account = PrimaryAccount.objects.create(
            user=user,
            **primary_account_data
        )

        # Create initial admin member
        Member.objects.create(
            primary_account=primary_account,
            name=user.email,
            email=user.email,
            relationship='PRIMARY',
            access_level='ADMIN'
        )

        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False
    )

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = User.objects.filter(email=email).first()
            
            if user and user.check_password(password):
                if not user.is_active:
                    raise serializers.ValidationError(
                        "User account is disabled."
                    )
                attrs['user'] = user
                return attrs
            raise serializers.ValidationError(
                "Unable to log in with provided credentials."
            )
        raise serializers.ValidationError(
            "Must include 'email' and 'password'."
        )