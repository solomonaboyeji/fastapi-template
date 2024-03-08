import os
import re
import psycopg2

from core.config import DB_CONN_STRING
from utils.errors import InvalidMigrationScript


def validate_migration_scripts(directory):
    migration_files = [f for f in os.listdir(directory) if f.endswith(".sql")]
    migration_files.sort()

    previous_num = 0
    for filename in migration_files:
        num = int(re.findall(r"\d+", filename)[0])
        if num != previous_num + 1:
            raise InvalidMigrationScript(
                f"Invalid migration filename: {filename}. File name should be incremental start with {previous_num + 1}"
            )
            return False
        previous_num = num
    return True


def run_migrations(directory, db_conn_string):
    migration_files = [f for f in os.listdir(directory) if f.endswith(".sql")]
    migration_files.sort()

    conn = psycopg2.connect(db_conn_string)
    cur = conn.cursor()
    try:
        for filename in migration_files:
            with open(os.path.join(directory, filename), "r") as file:
                sql = file.read()
                if len(sql) == 0:
                    raise InvalidMigrationScript(f"{filename} should not be empty.")
                cur.execute(sql)
                conn.commit()
            print(f"Migration script {filename} executed successfully.")
    except Exception as e:
        print(f"Error executing migration script: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    migration_directory = "./migrations"
    validate_migration_scripts(migration_directory)
    run_migrations(migration_directory, DB_CONN_STRING)


if __name__ == "__main__":
    migration_directory = "path/to/migration/scripts"
