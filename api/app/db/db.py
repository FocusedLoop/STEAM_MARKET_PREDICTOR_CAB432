import os, sys
import mariadb
import time

DB_HOST = os.environ.get("DB_HOST")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_NAME = os.environ.get("DB_NAME")
DB_PORT = int(os.environ.get("DB_PORT"))

# Get a connection to the database, retry 10 times as database may have not started yet
def get_connection():
    for attempt in range(10):
        try:
            conn = mariadb.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                port=DB_PORT
            )
            return conn
        except mariadb.Error as e:
            print(f"Attempt {attempt+1}/10: Error connecting to MariaDB Platform: {e}")
            time.sleep(3)
    print("Failed to connect to MariaDB after 10 attempts. Exiting.")
    sys.exit(1)

# Create user table
def create_user_table(conn: mariadb.Connection):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INT PRIMARY KEY AUTO_INCREMENT,
            username VARCHAR(255) UNIQUE NOT NULL,
            steam_id BIGINT,
            password VARCHAR(255) NOT NULL
        );
    """)
    conn.commit()

# Create group items table
def create_groups_table(conn: mariadb.Connection):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            id INT PRIMARY KEY AUTO_INCREMENT,
            group_name VARCHAR(255) NOT NULL,
            user_id INT NOT NULL,
            has_model BOOLEAN NOT NULL DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );
    """)
    conn.commit()

# Create items per group
def create_group_items_table(conn: mariadb.Connection):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_items (
            id INT PRIMARY KEY AUTO_INCREMENT,
            group_id INT NOT NULL,
            item_name VARCHAR(255) NOT NULL,
            item_json LONGTEXT NOT NULL,
            FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE
        );
    """)
    conn.commit()

# Create model index table
def create_model_index_table(conn: mariadb.Connection):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS model_index (
            id INT PRIMARY KEY AUTO_INCREMENT,
            user_id INT NOT NULL,
            group_id INT NOT NULL,
            item_id INT NOT NULL,
            data_hash VARCHAR(32) NOT NULL,
            model_path VARCHAR(255) NOT NULL,
            scaler_path VARCHAR(255) NOT NULL,
            stats_path VARCHAR(255) NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE
        );
    """)
    conn.commit()
    
# Initialize the database and create the tasks table if it doesn't exist
def init_db():
  conn = get_connection()
  try:
    #create_tasks_table(conn)
    create_user_table(conn)
    create_groups_table(conn)
    create_group_items_table(conn)
    create_model_index_table(conn)
    print("Database initialized and tasks table ensured.")
  except Exception as e:
    print(f"DB init failed: {e}")
  finally:
    conn.close()

init_db()