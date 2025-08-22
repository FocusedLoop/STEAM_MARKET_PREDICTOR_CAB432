from app.db import get_connection
import json

# Get all items in a group
def model_get_all_groups():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM groups")
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    conn.close()
    return [dict(zip(columns, row)) for row in rows]

# Get a group by ID
def model_get_groups_by_id(group_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM group_items WHERE id = ?", (group_id,))
    row = cursor.fetchone()
    columns = [desc[0] for desc in cursor.description]
    conn.close()
    return dict(zip(columns, row)) if row else None

# Create a new group
def model_create_group(user_id, title):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO group_items (user_id, title) VALUES (?, ?)", (user_id, title))
    conn.commit()
    group_id = cursor.lastrowid
    conn.close()
    return {"id": group_id, "user_id": user_id, "title": title}

# Update an existing group
def model_update_group(user_id, group_id, title):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE group_items SET title = ? WHERE id = ? AND user_id = ?",
        (title, group_id, user_id)
    )
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    return {"updated": updated}

# Remove an existing group
def model_remove_group(user_id, group_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM group_items WHERE id = ? AND user_id = ?", (group_id, user_id))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return {"deleted": deleted}

# Add an item to an existing group
def model_add_item_to_group(user_id, group_id, item_name, item_json):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO group_items (user_id, group_id, item_name, item_json) VALUES (?, ?, ?, ?)",
        (user_id, group_id, item_name, json.dumps(item_json))
    )
    conn.commit()
    added = cursor.rowcount > 0
    conn.close()
    return {"added": added}

# Remove an item from an existing group
def model_remove_item_from_group(user_id, group_id, item_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM group_items WHERE user_id = ? AND group_id = ? AND item_name = ?",
        (user_id, group_id, item_name)
    )
    conn.commit()
    removed = cursor.rowcount > 0
    conn.close()
    return {"removed": removed}

# def get_all():
#   conn = get_connection()
#   cursor = conn.cursor()
#   cursor.execute("SELECT * FROM tasks")
#   rows = cursor.fetchall()
#   columns = [desc[0] for desc in cursor.description]
#   conn.close()
#   return [dict(zip(columns, row)) for row in rows]

# def get_by_id(task_id):
#   conn = get_connection()
#   cursor = conn.cursor()
#   cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
#   row = cursor.fetchone()
#   columns = [desc[0] for desc in cursor.description]
#   conn.close()
#   return dict(zip(columns, row)) if row else None

# def create(title):
#   conn = get_connection()
#   cursor = conn.cursor()
#   cursor.execute("INSERT INTO tasks (title, completed) VALUES (?, ?)", (title, 0))
#   conn.commit()
#   task_id = cursor.lastrowid
#   conn.close()
#   return {"id": task_id, "title": title, "completed": 0}

# def update(task_id, title, completed):
#   conn = get_connection()
#   cursor = conn.cursor()
#   cursor.execute(
#     "UPDATE tasks SET title = ?, completed = ? WHERE id = ?",
#     (title, 1 if completed else 0, task_id)
#   )
#   conn.commit()
#   updated = cursor.rowcount > 0
#   conn.close()
#   return {"updated": updated}

# def remove(task_id):
#   conn = get_connection()
#   cursor = conn.cursor()
#   cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
#   conn.commit()
#   deleted = cursor.rowcount > 0
#   conn.close()
#   return {"deleted": deleted}