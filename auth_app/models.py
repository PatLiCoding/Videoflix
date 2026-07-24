from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager


class UserManager(BaseUserManager):
    """Custom manager for the email-based User model.

    Replaces Django's default username-based user creation logic, since
    this project authenticates users via email instead of username.
    """

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user with the given email and password.

        Args:
            email (str): The user's email address (required).
            password (str): The user's raw password.
            **extra_fields: Additional fields to set on the user instance.

        Returns:
            User: The newly created user instance.

        Raises:
            ValueError: If no email address is provided.
        """
        if not email:
            raise ValueError("The email address must be provided.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser with the given email and password.

        Args:
            email (str): The superuser's email address.
            password (str): The superuser's raw password.
            **extra_fields: Additional fields, is_staff/is_superuser default
                to True.

        Returns:
            User: The newly created superuser instance.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Custom user model that authenticates via email instead of username.

    The `username` field is kept as an optional, unused column solely for
    compatibility with the project's entrypoint.sh superuser bootstrap
    script, which is a fixed project requirement and cannot be modified.
    """
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, blank=True, null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "User"
        ordering = ["email"]

    def __str__(self):
        """Return the user's email as their string representation."""
        return self.email
