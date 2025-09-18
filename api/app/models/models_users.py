from app.db import get_connection


def model_get_or_create_user_profile(cognito_id: str, username: str):
    conn = get_connection()

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE cognito_id = ?", (cognito_id,))

    row = cursor.fetchone()

    if row:
        columns = [desc[0] for desc in cursor.description]

        conn.close()

        return dict(zip(columns, row))
    else:
        cursor.execute(
            "INSERT INTO users (cognito_id, username) VALUES (?, ?)",
            (cognito_id, username),
        )
        conn.commit()

        user_id = cursor.lastrowid

        conn.close()
        return {"user_id": user_id, "cognito_id": cognito_id, "username": username}


def model_get_user_by_cognito_id(cognito_id: str):
    conn = get_connection()

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE cognito_id = ?", (cognito_id,))

    row = cursor.fetchone()
    columns = [desc[0] for desc in cursor.description]

    conn.close()

    return dict(zip(columns, row)) if row else None


def model_delete_user(user_id: int):
    conn = get_connection()

    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))

    conn.commit()

    deleted = cursor.rowcount > 0

    conn.close()

    return {"deleted": deleted}
