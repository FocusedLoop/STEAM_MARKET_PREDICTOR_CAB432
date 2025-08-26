from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from app.auth.jwt import authenticate_token
from app.models import (
  model_get_all_groups,
  model_get_group_by_id,
  model_create_group,
  model_update_group,
  model_remove_group,
  model_add_item_to_group,
  model_remove_item_from_group,
  model_get_group_items
)

router = APIRouter()

# Create a new group
async def create_group(request: Request, user=Depends(authenticate_token)):
    data = await request.json()
    title = data.get("title")
    if not title:
        raise HTTPException(status_code=400, detail="Title is required")
    try:
        result = model_create_group(user["user_id"], title)
        return {
            "message": "Item added to group",
            **result
        }
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
        return {"message": f"Group name updated to {title}"}
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
        return {
            "message": f"Item {item_name} added to group",
            "id": result.get("id")
        }
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
        return {"message": f"Item {item_name} removed from group"}
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
def get_group_by_id(group_id: int):
    try:
        group = model_get_group_by_id(group_id)
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        return JSONResponse(content=group)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get all items in a group
async def get_group_items(group_id: int, user=Depends(authenticate_token)):
    try:
        items = model_get_group_items(user["user_id"], group_id)
        return JSONResponse(content=items)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))