from app.db import get_connection

def get_all():
  conn = get_connection()
  cursor = conn.cursor()
  cursor.execute("SELECT * FROM tasks")
  rows = cursor.fetchall()
  columns = [desc[0] for desc in cursor.description]
  conn.close()
  return [dict(zip(columns, row)) for row in rows]

def get_by_id(task_id):
  conn = get_connection()
  cursor = conn.cursor()
  cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
  row = cursor.fetchone()
  columns = [desc[0] for desc in cursor.description]
  conn.close()
  return dict(zip(columns, row)) if row else None

def create(title):
  conn = get_connection()
  cursor = conn.cursor()
  cursor.execute("INSERT INTO tasks (title, completed) VALUES (?, ?)", (title, 0))
  conn.commit()
  task_id = cursor.lastrowid
  conn.close()
  return {"id": task_id, "title": title, "completed": 0}

def update(task_id, title, completed):
  conn = get_connection()
  cursor = conn.cursor()
  cursor.execute(
    "UPDATE tasks SET title = ?, completed = ? WHERE id = ?",
    (title, 1 if completed else 0, task_id)
  )
  conn.commit()
  updated = cursor.rowcount > 0
  conn.close()
  return {"updated": updated}

def remove(task_id):
  conn = get_connection()
  cursor = conn.cursor()
  cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
  conn.commit()
  deleted = cursor.rowcount > 0
  conn.close()
  return {"deleted": deleted}