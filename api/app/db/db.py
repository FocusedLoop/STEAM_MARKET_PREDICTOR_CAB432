import os, sys
import psycopg2
import time
from psycopg2 import sql

# TODO Add to paramter store and secrets manager
DB_HOST = "database-1-instance-1.ce2haupt2cta.ap-southeast-2.rds.amazonaws.com"
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_NAME = "cohort_2025"
DB_PORT = 5432
DB_SCHEMA = os.environ.get("DB_SCHEMA", DB_USER)

# Get a connection to the database, retry 10 times
def get_connection():
    for attempt in range(10):
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                port=DB_PORT,
                sslmode='require'  # Required for RDS
            )
            # Set schema for isolation
            cursor = conn.cursor()
            cursor.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(DB_SCHEMA)))
            conn.commit()
            cursor.close()
            return conn
        except psycopg2.Error as e:
            print(f"Attempt {attempt+1}/10: Error connecting to PostgreSQL: {e}")
            time.sleep(3)
    print("Failed to connect to PostgreSQL after 10 attempts. Exiting.")
    sys.exit(1)

# Create user table
def create_user_table(conn: psycopg2.extensions.connection):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id SERIAL PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            steam_id BIGINT,
            password VARCHAR(255) NOT NULL
        );
    """)
    conn.commit()

# Create groups table
def create_groups_table(conn: psycopg2.extensions.connection):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            id SERIAL PRIMARY KEY,
            group_name VARCHAR(255) NOT NULL,
            user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            has_model BOOLEAN NOT NULL DEFAULT FALSE
        );
    """)
    conn.commit()

# Create group items table
def create_group_items_table(conn: psycopg2.extensions.connection):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_items (
            id SERIAL PRIMARY KEY,
            group_id INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
            item_name VARCHAR(255) NOT NULL,
            item_json TEXT NOT NULL
        );
    """)
    conn.commit()

# Create model index table
def create_model_index_table(conn: psycopg2.extensions.connection):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS model_index (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            group_id INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
            item_id INTEGER NOT NULL,
            data_hash VARCHAR(32) NOT NULL,
            model_path VARCHAR(255) NOT NULL,
            scaler_path VARCHAR(255) NOT NULL,
            stats_path VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    
# Initialize the database and create the tables if they don't exist
def init_db():
    conn = get_connection()
    try:
        create_user_table(conn)
        create_groups_table(conn)
        create_group_items_table(conn)
        create_model_index_table(conn)
        print("Database initialized and tables ensured.")
    except Exception as e:
        print(f"DB init failed: {e}")
    finally:
        conn.close()

init_db()