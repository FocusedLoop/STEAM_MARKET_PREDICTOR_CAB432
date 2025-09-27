from app.db import get_connection

def model_get_or_create_user_profile(cognito_id: str, username: str):
    """
    Get or create a user profile by cognito_id.
    Returns the user dict if exists, or creates and returns new user.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM users WHERE cognito_id = %s", (cognito_id,))
        row = cursor.fetchone()
        
        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        else:
            cursor.execute(
                "INSERT INTO users (cognito_id, username) VALUES (%s, %s)",
                (cognito_id, username),
            )
            conn.commit()
            user_id = cursor.lastrowid
            return {"user_id": user_id, "cognito_id": cognito_id, "username": username}
    except Exception as e:
        conn.rollback()
        raise Exception(f"Database error in get_or_create: {e}")
    finally:
        cursor.close()
        conn.close()

def model_get_user_by_cognito_id(cognito_id: str):
    """
    Get user by cognito_id.
    Returns user dict or None.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM users WHERE cognito_id = %s", (cognito_id,))
        row = cursor.fetchone()
        
        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        return None
    except Exception as e:
        raise Exception(f"Database error in get_by_cognito_id: {e}")
    finally:
        cursor.close()
        conn.close()

def model_delete_user(user_id: int):
    """
    Delete user by user_id.
    Returns {"deleted": True} if successful, {"deleted": False} otherwise.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
        conn.commit()
        deleted = cursor.rowcount > 0
        return {"deleted": deleted}
    except Exception as e:
        conn.rollback()
        raise Exception(f"Database error in delete: {e}")
    finally:
        cursor.close()
        conn.close()