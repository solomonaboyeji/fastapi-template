import os
import dotenv

dotenv.load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "")  #
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Connection to a PostgreSQL database
DATABASE_USERNAME = os.getenv("DATABASE_USERNAME")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_SERVER = os.getenv("DATABASE_SERVER")
DATABASE_NAME = os.getenv("DATABASE_NAME")
DATABASE_PORT = os.getenv("DATABASE_PORT", "1433")
CONNECTION_PARAMS = {
    "dbname": DATABASE_NAME,
    "user": DATABASE_USERNAME,
    "password": DATABASE_PASSWORD,
    "host": DATABASE_SERVER,
    "port": DATABASE_PORT,
}
DB_CONN_STRING = f"dbname='{DATABASE_NAME}' user='{DATABASE_USERNAME}' host='{DATABASE_SERVER}' password='{DATABASE_PASSWORD}'"


# Email configurations
EMAIL_HOST = "smtp.example.com"
EMAIL_PORT = 587
EMAIL_ADDRESS = "your-email@example.com"
EMAIL_PASSWORD = "your-email-password"
EMAIL_FROM_NAME = "Your App Name"
MIN_DB_POOL_SIZE = 1
MAX_DB_POOL_SIZE = 10

TESTING = os.getenv("TESTING", "False")
