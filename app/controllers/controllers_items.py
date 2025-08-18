from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from app.auth.jwt import authenticate_token
from app.models import (
  get_all,
  get_by_id,
  create,
  update,
  remove
  )

router = APIRouter()

def get_all_tasks():
  try:
    return JSONResponse(content=get_all())
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

def get_task_by_id(task_id: int):
  try:
    result = get_by_id(task_id)
    if not result:
      raise HTTPException(status_code=404, detail="Task not found")
    return JSONResponse(content=result)
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

async def create_task(request: Request, user=Depends(authenticate_token)):
  data = await request.json()
  title = data.get("title")
  if not title:
    raise HTTPException(status_code=400, detail="Title is required")
  try:
    return create(title)
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

async def update_task(task_id: int, request: Request, user=Depends(authenticate_token)):
  data = await request.json()
  title = data.get("title")
  completed = data.get("completed", False)
  try:
    result = update(task_id, title, completed)
    if not result.get("updated"):
      raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task updated"}
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

def delete_task(task_id: int, user=Depends(authenticate_token)):
  try:
    result = remove(task_id)
    if not result.get("deleted"):
      raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted"}
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))