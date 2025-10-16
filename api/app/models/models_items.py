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
def model_get_group_by_id(group_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM groups WHERE id = %s", (group_id,))
    row = cursor.fetchone()
    columns = [desc[0] for desc in cursor.description]
    conn.close()
    return dict(zip(columns, row)) if row else None

# Create a new group for a user
def model_create_group(user_id: int, group_name: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO groups (group_name, user_id) VALUES (%s, %s)", (group_name, user_id))
    cursor.execute("SELECT LASTVAL()")  # Get the last inserted ID
    group_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return {"id": group_id, "user_id": user_id, "group_name": group_name}

# Update an existing group's name (only if owned by user)
def model_update_group(user_id: int, group_id: int, group_name: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE groups SET group_name = %s WHERE id = %s AND user_id = %s",
        (group_name, group_id, user_id)
    )
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    return {"updated": updated}

# Remove an existing group (only if owned by user)
def model_remove_group(user_id: int, group_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM groups WHERE id = %s AND user_id = %s", (group_id, user_id))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return {"deleted": deleted}

# Add an item to an existing group (must be owned by user)
def model_add_item_to_group(user_id: int, group_id: int, item_name: str, item_json: dict):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM groups WHERE id = %s AND user_id = %s", (group_id, user_id))
    if not cursor.fetchone():
        conn.close()
        return {"added": False}
    cursor.execute(
        "INSERT INTO group_items (group_id, item_name, item_json) VALUES (%s, %s, %s) RETURNING id",
        (group_id, item_name, json.dumps(item_json))
    )
    item_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return {"added": True, "id": item_id}

# Remove an item from an existing group (must be owned by user)
def model_remove_item_from_group(user_id: int, group_id: int, item_name: str):
    conn = get_connection()
    cursor = conn.cursor()
    # Ensure group is owned by user
    cursor.execute("SELECT id FROM groups WHERE id = %s AND user_id = %s", (group_id, user_id))
    if not cursor.fetchone():
        conn.close()
        return {"removed": False}
    cursor.execute(
        "DELETE FROM group_items WHERE group_id = %s AND item_name = %s",
        (group_id, item_name)
    )
    conn.commit()
    removed = cursor.rowcount > 0
    conn.close()
    return {"removed": removed}

# Get all items in a group (must be owned by user)
def model_get_group_items(user_id: int, group_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT group_items.* FROM group_items
        JOIN groups ON group_items.group_id = groups.id
        WHERE groups.user_id = %s AND group_items.group_id = %s
    """, (user_id, group_id))
    rows = cursor.fetchall()
    #print(rows)
    columns = [desc[0] for desc in cursor.description]
    conn.close()
    items = [dict(zip(columns, row)) for row in rows]
    for item in items:
        try:
            item["item_json"] = json.loads(item["item_json"])
        except Exception:
            pass
    return items