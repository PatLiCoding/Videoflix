"""Serializers for user registration and password reset/confirmation."""
from rest_framework import serializers
from auth_app.models import User


class RegistrationSerializer(serializers.ModelSerializer):
    """Validate and create a new, inactive user account on registration."""
    confirmed_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'confirmed_password']

    def validate_confirmed_password(self, value):
        """Ensure the password confirmation matches the chosen password."""
        password = self.initial_data.get('password')
        if password and value and password != value:
            raise serializers.ValidationError('Passwords do not match')
        return value

    def validate_email(self, value):
        """Reject registration if the email is already in use."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already exists')
        return value

    def save(self, **kwargs):
        """Create a new, inactive user with a securely hashed password.

        Returns:
            User: The newly created (inactive) user instance.
        """
        password = self.validated_data['password']
        account = User(email=self.validated_data['email'], is_active=False)
        account.set_password(password)
        account.save()
        return account


class PasswordResetSerializer(serializers.Serializer):
    """Validate the email address used to request a password reset."""
    email = serializers.EmailField()

    def validate_email(self, value):
        """Ensure an account exists for the given email address."""
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                'No account found with this email')
        return value


class PasswordConfirmSerializer(serializers.Serializer):
    """Validate and apply a new password during password-reset confirmation."""
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate_confirm_password(self, value):
        """Ensure the new password and its confirmation match."""
        new_password = self.initial_data.get('new_password')
        if new_password and value and new_password != value:
            raise serializers.ValidationError('Passwords do not match')
        return value

    def save(self, **kwargs):
        """Set the new password on the given user.

        Args:
            **kwargs: Must include `user`, the User instance to update.

        Returns:
            User: The updated user instance.
        """
        pw = self.validated_data['new_password']
        account = kwargs['user']
        account.set_password(pw)
        account.save()
        return account
