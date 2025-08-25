from app.db import get_connection

def model_save_model_index(user_id, group_id, item_id, data_hash, model_path, scaler_path, stats_path):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO model_index (user_id, group_id, item_id, data_hash, model_path, scaler_path, stats_path)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, group_id, item_id, data_hash, model_path, scaler_path, stats_path))
    conn.commit()
    model_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return {
        "id": model_id,
        "user_id": user_id,
        "group_id": group_id,
        "item_id": item_id,
        "data_hash": data_hash,
    }

def model_get_model_index(user_id, item_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM model_index
        WHERE user_id = ? AND item_id = ?
        ORDER BY created_at DESC LIMIT 1
    """, (user_id, item_id))
    row = cursor.fetchone()
    columns = [desc[0] for desc in cursor.description]
    cursor.close()
    conn.close()
    return dict(zip(columns, row)) if row else None

def model_get_groups_with_models(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT group_id FROM model_index
        WHERE user_id = ?
    """, (user_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [row[0] for row in rows]

def model_delete_model_group(user_id, group_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM model_index
        WHERE group_id = ? AND user_id = ?
    """, (group_id, user_id))
    conn.commit()
    deleted = cursor.rowcount > 0
    cursor.close()
    conn.close()
    return {"deleted": deleted}