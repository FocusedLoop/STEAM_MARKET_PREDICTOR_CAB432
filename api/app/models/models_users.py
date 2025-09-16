from app.db import get_connection

# Get user information and credentials
def model_get_user_by_username(username: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    row = cursor.fetchone()
    columns = [desc[0] for desc in cursor.description]
    conn.close()
    return dict(zip(columns, row)) if row else None

# Get user id from username
def model_get_user_id_by_username(username: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

# Get steam id from username
def model_get_steam_id_by_username(username: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT steam_id FROM users WHERE username = %s", (username,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

# Create a new user
def model_create_user(username: str, password: str, steam_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, password, steam_id) VALUES (%s, %s, %s)",
        (username, password, steam_id)
    )
    cursor.execute("SELECT LASTVAL()")
    user_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return {"user_id": user_id, "username": username, "steam_id": steam_id}

# Delete existing user
def model_delete_user(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return {"deleted": deleted}