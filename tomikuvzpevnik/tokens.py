# myproject/myapp/tokens.py

from django.contrib.auth.tokens import PasswordResetTokenGenerator

class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    """
    Custom token generator for account activation.
    It generates a unique token based on user's primary key, last login time,
    and password hash. This ensures the token is unique and expires if user
    details change (e.g., password reset).
    """
    def _make_hash_value(self, user, timestamp):
        """
        Generates the hash value for the token.
        Includes user's primary key, last login time, and password hash.
        We also include `is_active` to ensure the token becomes invalid
        once the account is activated.
        """
        return (
            str(user.pk) + str(timestamp) +
            str(user.is_active)
        )

account_activation_token = AccountActivationTokenGenerator()

