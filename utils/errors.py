from loguru import logger
import psycopg2


class EmailException(Exception):
    pass


class PasswordResetException(Exception):
    pass


class InvalidMigrationScript(Exception):
    pass


class ResourceNotFoundException(Exception):
    pass


class DuplicateResourceException(Exception):
    pass


class BadReqeustException(Exception):
    pass


class DatabaseException(BadReqeustException):
    pass


import traceback

EMAIL_CONFIRMATION_ERROR_MESSAGE = "We are unable to send you a confirmation email at this moment, please request confirmation code at sign in."
EMAIL_PASSWORD_RESET_ERROR_MESSAGE = (
    "We are unable to send you a password reset email at this moment, please try again."
)


def log_database_error(
    db_error: Exception,
    default_msg="There has been a database connection problem.",
):
    # psycopg2.DatabaseError
    # DataError: problems with the processed data, like invalid data type conversions
    # IntegrityError: problems related to database integrity such as constraint violations etc
    #                 common ones include insert or update data that would violate a primary key or
    #                 unique constraint
    # InternalError:  errors considered internal to the database. These errors might indicate a problem within the database engine itself.
    # NotSupportedError: Features or operations not supported in the database engine. Example includes trying to use an unsupported SQL feature
    # OperationalError: represent errors that are related to the operation of the database, can include those like connection problems, timeout occurs etc
    # Programming Error: errors related to the use of the database API or SQL syntax, or an issue with SQL query itself or the way parameters are bound
    # TransactionRollbackError: Represents errors related to transaction rollbacks.
    # InterfaceError

    tb = traceback.extract_tb(db_error.__traceback__)

    frame = tb[0] if tb else None
    if frame:
        filename, line_num, func_name, source_code = frame
        logger.error(f"[FILE] {filename}\n[FUNCTION]: {func_name}\n[LINE]: {line_num}")

    if "duplicate" in str(db_error).lower():
        return DuplicateResourceException(default_msg)

    return DatabaseException(default_msg)
