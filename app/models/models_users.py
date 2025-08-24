from app.db import get_connection

# Get user information and credentials
def get_user_by_username(username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    columns = [desc[0] for desc in cursor.description]
    conn.close()
    return dict(zip(columns, row)) if row else None

# Get user id from username
def get_user_id_by_username(username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

# Get steam id from username
def get_steam_id_by_username(username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT steam_id FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

# Create a new user
def create_user(username, password, steam_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, password, steam_id) VALUES (?, ?, ?)",
        (username, password, steam_id)
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return {"user_id": user_id, "username": username, "steam_id": steam_id}

# Delete existing user
def delete_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return {"deleted": deleted}