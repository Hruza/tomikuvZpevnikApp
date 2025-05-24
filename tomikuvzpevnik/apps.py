from django.apps import AppConfig
import locale
from django.db.backends.signals import connection_created


def czech_collation_function(str1, str2):
    # Ensure the locale is set for correct comparison.
    # On some systems, you might need to try 'cs_CZ.UTF-8' or similar.
    # It's good practice to try/except this in case the locale isn't installed.
    try:
        locale.setlocale(locale.LC_ALL, "cs_CZ.UTF-8")
    except locale.Error:
        # Fallback to a basic comparison or log a warning
        return (str1 > str2) - (str1 < str2)  # Pythonic equivalent of cmp

    return locale.strcoll(str1, str2)


def register_czech_collation(sender, connection, **kwargs):
    from django.db import connection

    # Only register for SQLite connections
    if connection.vendor == "sqlite":
        # Access the underlying sqlite3 connection object
        db_connection = connection.connection
        # Register your custom collation
        db_connection.create_collation("CZECH_NOCASE", czech_collation_function)


class TomikuvzpevnikConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tomikuvzpevnik"

    def ready(self):
        # Only apply this if the database engine is SQLite
        # Check if the current database connection is SQLite
        connection_created.connect(register_czech_collation)
