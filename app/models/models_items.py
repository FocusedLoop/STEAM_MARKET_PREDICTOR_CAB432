from app.db import get_connection
import json

# Get all groups (with user info)
def model_get_all_groups():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM groups")
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    conn.close()
    return [dict(zip(columns, row)) for row in rows]

# Get all items in a group by group_id
def model_get_group_by_id(group_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM groups WHERE id = ?", (group_id,))
    row = cursor.fetchone()
    columns = [desc[0] for desc in cursor.description]
    conn.close()
    return dict(zip(columns, row)) if row else None

# Create a new group for a user
def model_create_group(user_id, group_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO groups (group_name, user_id) VALUES (?, ?)", (group_name, user_id))
    conn.commit()
    group_id = cursor.lastrowid
    conn.close()
    return {"id": group_id, "user_id": user_id, "group_name": group_name}

# Update an existing group's name (only if owned by user)
def model_update_group(user_id, group_id, group_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE groups SET group_name = ? WHERE id = ? AND user_id = ?",
        (group_name, group_id, user_id)
    )
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    return {"updated": updated}

# Remove an existing group (only if owned by user)
def model_remove_group(user_id, group_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM groups WHERE id = ? AND user_id = ?", (group_id, user_id))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return {"deleted": deleted}

# Add an item to an existing group (must be owned by user)
def model_add_item_to_group(user_id, group_id, item_name, item_json):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM groups WHERE id = ? AND user_id = ?", (group_id, user_id))
    if not cursor.fetchone():
        conn.close()
        return {"added": False}
    cursor.execute(
        "INSERT INTO group_items (group_id, item_name, item_json) VALUES (?, ?, ?)",
        (group_id, item_name, json.dumps(item_json))
    )
    conn.commit()
    added = cursor.rowcount > 0
    item_id = cursor.lastrowid
    conn.close()
    return {"added": added, "id": item_id}

# Remove an item from an existing group (must be owned by user)
def model_remove_item_from_group(user_id, group_id, item_name):
    conn = get_connection()
    cursor = conn.cursor()
    # Ensure group is owned by user
    cursor.execute("SELECT id FROM groups WHERE id = ? AND user_id = ?", (group_id, user_id))
    if not cursor.fetchone():
        conn.close()
        return {"removed": False}
    cursor.execute(
        "DELETE FROM group_items WHERE group_id = ? AND item_name = ?",
        (group_id, item_name)
    )
    conn.commit()
    removed = cursor.rowcount > 0
    conn.close()
    return {"removed": removed}

# Get all items in a group (must be owned by user)
def model_get_group_items(user_id, group_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT gi.* FROM group_items gi
        JOIN groups g ON gi.group_id = g.id
        WHERE g.user_id = ? AND gi.group_id = ?
    """, (user_id, group_id))
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    conn.close()
    items = [dict(zip(columns, row)) for row in rows]
    for item in items:
        try:
            item["item_json"] = json.loads(item["item_json"])
        except Exception:
            pass
    return items