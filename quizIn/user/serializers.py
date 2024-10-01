from rest_framework import serializers
from .models import CustomUser
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    username = serializers.CharField(required=False, allow_blank=True)
    role = serializers.CharField(required=True)  # Add role field

    class Meta:
        model = CustomUser
        fields = ['id', 'msisdn', 'email', 'username', 'password', 'role']  # Include role in fields

    def create(self, validated_data):
        # Extract password and role from validated data
        password = validated_data.pop('password')  # Remove password from validated data
        role = validated_data.pop('role')  # Remove role from validated data

        # Create a new user instance
        user = CustomUser(
            msisdn=validated_data['msisdn'],
            email=validated_data.get('email'),
            username=validated_data.get('username'),
            role=role  # Set the role
        )
        user.set_password(password)  # Hash the password
        user.save()  # Save the user instance
        return user

    def update(self, instance, validated_data):
        # Update user attributes with validated data
        instance.email = validated_data.get('email', instance.email)
        instance.username = validated_data.get('username', instance.username)
        instance.role = validated_data.get('role', instance.role)  # Update the role if provided

        # Only set password if provided
        if 'password' in validated_data:
            instance.set_password(validated_data['password'])

        instance.save()  # Save the updated user instance
        return instance


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # Modify the login mechanism to use msisdn instead of username
        msisdn = attrs.get('msisdn')
        password = attrs.get('password')

        user = CustomUser.objects.filter(msisdn=msisdn).first()

        if user and user.check_password(password):
            data = super().validate(attrs)
            return data
        else:
            raise serializers.ValidationError("Incorrect MSISDN or password")


class UpdateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['msisdn', 'email', 'username', 'role']  # Include role field in update

    def update(self, instance, validated_data):
        instance.msisdn = validated_data.get('msisdn', instance.msisdn)
        instance.email = validated_data.get('email', instance.email)
        instance.username = validated_data.get('username', instance.username)
        instance.role = validated_data.get('role', instance.role)  # Update the role if provided
        instance.save()
        return instance
