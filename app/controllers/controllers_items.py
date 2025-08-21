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

# MAYBE MAKE SO USER CAN ONLY HAVE ONE MODEL AT A TIME

# STEAM
# Get top games - Get a list of top games
# Get top inventory items from a game - Get a list of top inventory items from a game
# Get price history - Get the price history of an item > Returns a Link to get the price history

# ITEMS - DB
# Create Item Group - Create a new item group
# Update Item group - Update an existing item group with a new price history for an item
# DELETE Item Group - Delete an existing item group
# GET Item Group - Get details of a specific item group

# CREATE MODEL - PKL file with User ID
# Generate Item Group Model - Generate price models for a group of items (item_group) > Returns a group of price history graphs
# Generate Item Model - Generate price model for a specific item ({price history}}) > Returns a Graph of the price history

# MAKE PREDICTION - GRAPH
# Generate Item Group Prediction - Generate price predictions for a group of items (start, end)
# Generate Item Price Prediction - Generate price predictions for a specific item (start, end)