from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from app.auth.jwt import authenticate_token
from app.services import steamAPI
from app.models import (
  model_get_all_groups,
  model_get_groups_by_id,
  model_create_group,
  model_update_group,
  model_remove_group,
  model_add_item_to_group,
  model_remove_item_from_group,
)

router = APIRouter()

# Create a new group
async def create_group(request: Request, user=Depends(authenticate_token)):
    data = await request.json()
    title = data.get("title")
    if not title:
        raise HTTPException(status_code=400, detail="Title is required")
    try:
        return model_create_group(user["user_id"], title)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Change a group name
async def update_group_name(group_id: int, request: Request, user=Depends(authenticate_token)):
    data = await request.json()
    title = data.get("title")
    if not title:
        raise HTTPException(status_code=400, detail="Title is required")
    try:
        result = model_update_group(user["user_id"], group_id, title)
        if not result.get("updated"):
            raise HTTPException(status_code=404, detail="Group not found or not owned by user")
        return {"message": "Group name updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Add item to an existing group
async def add_item_to_group(group_id: int, request: Request, user=Depends(authenticate_token)):
    data = await request.json()
    item_name = data.get("item_name")
    item_json = data.get("item_json")
    if not item_name or not item_json or not group_id:
        raise HTTPException(status_code=400, detail="Item name, item JSON, and Group ID are required")
    try:
        result = model_add_item_to_group(user["user_id"], group_id, item_name, item_json)
        if not result.get("added"):
            raise HTTPException(status_code=404, detail="Group not found, not owned by user, or item could not be added")
        return {"message": "Item added to group"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Remove item from an existing group
async def remove_item_from_group(group_id: int, request: Request, user=Depends(authenticate_token)):
    data = await request.json()
    item_name = data.get("item_name")
    if not item_name or not group_id:
        raise HTTPException(status_code=400, detail="Item name and Group ID are required")
    try:
        result = model_remove_item_from_group(user["user_id"], group_id, item_name)
        if not result.get("removed"):
            raise HTTPException(status_code=404, detail="Group or Item not found, or not owned by user")
        return {"message": "Item removed from group"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Delete an existing group
async def delete_group(group_id: int, user=Depends(authenticate_token)):
    try:
        result = model_remove_group(user["user_id"], group_id)
        if not result.get("deleted"):
            raise HTTPException(status_code=404, detail="Group not found or not owned by user")
        return {"message": "Group deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get all groups - no auth
def get_all_groups():
    try:
        groups = model_get_all_groups()
        return JSONResponse(content=groups)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get a group by ID - no auth
def get_groups_by_id(group_id: int):
    try:
        group = model_get_groups_by_id(group_id)
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        return JSONResponse(content=group)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get top games for the authenticated user
async def get_steam_top_games(user=Depends(authenticate_token)):
    try:
        steam = steamAPI(user["steam_id"])
        top_games = steam.find_suitable_games()
        return JSONResponse(content=top_games)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get price history for a specific item
async def get_steam_item_history(appid: int, item_name: str, user=Depends(authenticate_token)):
    if not appid or not item_name:
        raise HTTPException(status_code=400, detail="App Id and Item name is required")
    try:
        steam = steamAPI(user["steam_id"])
        item_info = steam.search_item(appid, item_name)
        if not item_info or not item_info.get("market_hash_name"):
            raise HTTPException(status_code=404, detail="Item not found in inventory")
        
        # Use the found info to generate the price history URL
        item_history_url = steam.generate_price_history_url(
            appid=appid,
            marker_hash=item_info["market_hash_name"],
            # classid=item_info.get("classid"),
            # instanceid=item_info.get("instanceid")
        )
        return JSONResponse(content={"price_history_url": item_history_url})
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


# OLD
# def get_all_tasks():
#   try:
#     return JSONResponse(content=get_all())
#   except Exception as e:
#     raise HTTPException(status_code=500, detail=str(e))

# def get_task_by_id(task_id: int):
#   try:
#     result = get_by_id(task_id)
#     if not result:
#       raise HTTPException(status_code=404, detail="Task not found")
#     return JSONResponse(content=result)
#   except Exception as e:
#     raise HTTPException(status_code=500, detail=str(e))

# async def create_task(request: Request, user=Depends(authenticate_token)):
#   data = await request.json()
#   title = data.get("title")
#   if not title:
#     raise HTTPException(status_code=400, detail="Title is required")
#   try:
#     return create(title)
#   except Exception as e:
#     raise HTTPException(status_code=500, detail=str(e))

# async def update_task(task_id: int, request: Request, user=Depends(authenticate_token)):
#   data = await request.json()
#   title = data.get("title")
#   completed = data.get("completed", False)
#   try:
#     result = update(task_id, title, completed)
#     if not result.get("updated"):
#       raise HTTPException(status_code=404, detail="Task not found")
#     return {"message": "Task updated"}
#   except Exception as e:
#     raise HTTPException(status_code=500, detail=str(e))

# def delete_task(task_id: int, user=Depends(authenticate_token)):
#   try:
#     result = remove(task_id)
#     if not result.get("deleted"):
#       raise HTTPException(status_code=404, detail="Task not found")
#     return {"message": "Task deleted"}
#   except Exception as e:
#     raise HTTPException(status_code=500, detail=str(e))