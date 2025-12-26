import os
from dotenv import load_dotenv
from google.adk.models.lite_llm import LiteLlm
import pyodbc

load_dotenv()

llm_mini = LiteLlm(
    model=f"azure/{os.getenv('AZURE_DEPLOYMENT_GPT4O_MINI', os.getenv('AZURE_DEPLOYMENT_GPT4O'))}",
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_base=os.getenv("AZURE_OPEN_AI_BASE_URL"),
)

llm_advanced = LiteLlm(
    model=f"azure/{os.getenv('AZURE_DEPLOYMENT_GPT5_MINI')}",
    api_key=os.getenv("AZURE_COGNITIVE_API_KEY"),
    api_base=os.getenv("AZURE_COGNITIVE_ENDPOINT"),
)

llm = llm_advanced

# Database URI (if needed in other modules)
DB_URI = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@" \
    f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}?sslmode={os.getenv('DB_SSLMODE')}"

SQL_DB = {
    'user': 'root',
    'password': 'Emids123',
    'host': '127.0.0.1',  # or 'localhost'
}

# Get environment variables
# Default to the correct driver
sql_driver = os.getenv("SQL_DRIVER", "ODBC Driver 17 for SQL Server")
# 'your_server.database.windows.net'
sql_server_name = os.getenv("SQL_SERVER_NAME")
sql_database_name = os.getenv("SQL_DATABASE_NAME")  # 'clinical_reports'
sql_db_username = os.getenv("SQL_DB_USERNAME")  # 'your_username'
sql_db_password = os.getenv("SQL_DB_PASSWORD")  # 'your_password'

# Debug: Print values to check if they are set correctly
print(f"SQL_DRIVER: {sql_driver}")
print(f"SQL_SERVER_NAME: {sql_server_name}")
print(f"SQL_DATABASE_NAME: {sql_database_name}")
print(f"SQL_DB_USERNAME: {sql_db_username}")

# Ensure no environment variable is missing
if None in [sql_driver, sql_server_name, sql_database_name, sql_db_username, sql_db_password]:
    raise ValueError("One or more required environment variables are missing!")

# Build the correct connection string
connection_string = (
    f"DRIVER={sql_driver};"
    f"SERVER={sql_server_name};"
    f"DATABASE={sql_database_name};"
    f"UID={sql_db_username};"
    f"PWD={sql_db_password};"
    f"Encrypt=yes;"  # Enable encryption (for Azure SQL)
    f"TrustServerCertificate=no;"  # Ensure SSL verification
    f"Connection Timeout=30;"  # Prevent connection timeouts
)


try:
    sql_connection = pyodbc.connect(connection_string, timeout=30)
except Exception as e:
    raise ConnectionError(f"Failed to create SQL connection: {e}")
