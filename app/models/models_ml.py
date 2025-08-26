from app.db import get_connection

# Set the has_model flag for a group
def set_group_has_model(conn, group_id, has_model):
    cursor = conn.cursor()
    cursor.execute("UPDATE groups SET has_model = ? WHERE id = ?", (int(has_model), group_id))
    conn.commit()

# Save a new model index into the database
def model_save_model_index(user_id, group_id, item_id, data_hash, model_path, scaler_path, stats_path):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO model_index (user_id, group_id, item_id, data_hash, model_path, scaler_path, stats_path)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, group_id, item_id, data_hash, model_path, scaler_path, stats_path))
    conn.commit()
    model_id = cursor.lastrowid
    set_group_has_model(conn, group_id, True)

    cursor.close()
    conn.close()
    return {
        "id": model_id,
        "user_id": user_id,
        "group_id": group_id,
        "item_id": item_id,
        "data_hash": data_hash,
    }

# Get the model index for a specific item
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

# Delete a model index for a specific item
# HACK USING DIFFERENT CHECK FOR DELETE METHOD SINCE FOREIGN KEYS PROHIBIT DETECTING ROW CHANGE
def model_delete_model_index(user_id, group_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM model_index WHERE group_id = %s AND user_id = %s
    """, (group_id, user_id))
    before_count = cursor.fetchone()[0]
    cursor.execute("""
        DELETE FROM model_index
        WHERE group_id = %s AND user_id = %s
    """, (group_id, user_id))
    conn.commit()
    cursor.execute("""
        SELECT COUNT(*) FROM model_index WHERE group_id = %s AND user_id = %s
    """, (group_id, user_id))
    after_count = cursor.fetchone()[0]
    deleted = before_count > after_count
    print("Rows before:", before_count, "Rows after:", after_count, "Deleted:", deleted)
    if deleted:
        set_group_has_model(conn, group_id, False)
    cursor.close()
    conn.close()
    return {"deleted": deleted}