from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from app.auth.cognito_jwt import get_current_user
from app.utils import validate_price_history
from app.utils.utils_redis import redis_cache
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
async def create_group(request: Request, user=Depends(get_current_user)):
    data = await request.json()
    title = data.get("title")
    if not title:
        raise HTTPException(status_code=400, detail="Title is required")
    try:
        result = model_create_group(user["user_id"], title)
        # Invalidate cache for all groups
        await redis_cache.delete("groups:all")
        return {
            "message": "Group created",
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Change a group name
async def update_group_name(group_id: int, request: Request, user=Depends(get_current_user)):
    data = await request.json()
    title = data.get("title")
    if not title:
        raise HTTPException(status_code=400, detail="Title is required")
    try:
        result = model_update_group(user["user_id"], group_id, title)
        if not result.get("updated"):
            raise HTTPException(status_code=404, detail="Group not found or not owned by user")
        # Invalidate cache for this group and all groups
        await redis_cache.delete(f"group:{group_id}")
        await redis_cache.delete("groups:all")
        print("Cache invalidated for group and all groups")
        return {"message": f"Group name updated to {title}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Add item to an existing group
async def add_item_to_group(group_id: int, request: Request, user=Depends(get_current_user)):
    data = await request.json()
    item_name = data.get("item_name")
    item_json = data.get("item_json")

    is_valid, error_msg = validate_price_history(item_json)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Invalid price history: {error_msg}")
    if not item_name or not item_json or not group_id:
        raise HTTPException(status_code=400, detail="Item name, item JSON, and Group ID are required")
    try:
        result = model_add_item_to_group(user["user_id"], group_id, item_name, item_json)
        if not result.get("added"):
            raise HTTPException(status_code=404, detail="Group not found, not owned by user, or item could not be added")
        # Invalidate cache for this group's items
        await redis_cache.delete(f"group:{group_id}:items:{user['user_id']}")
        print("Cache deleted for group items")
        return {
            "message": f"Item {item_name} added to group",
            "id": result.get("id")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Remove item from an existing group
async def remove_item_from_group(group_id: int, request: Request, user=Depends(get_current_user)):
    data = await request.json()
    item_name = data.get("item_name")
    if not item_name or not group_id:
        raise HTTPException(status_code=400, detail="Item name and Group ID are required")
    try:
        result = model_remove_item_from_group(user["user_id"], group_id, item_name)
        if not result.get("removed"):
            raise HTTPException(status_code=404, detail="Group or Item not found, or not owned by user")
        # Invalidate cache for this group's items
        await redis_cache.delete(f"group:{group_id}:items:{user['user_id']}")
        print("Cache deleted for group items")
        return {"message": f"Item {item_name} removed from group"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Delete an existing group
async def delete_group(group_id: int, user=Depends(get_current_user)):
    try:
        result = model_remove_group(user["user_id"], group_id)
        if not result.get("deleted"):
            raise HTTPException(status_code=404, detail="Group not found or not owned by user")
        # Invalidate all related caches
        await redis_cache.delete(f"group:{group_id}")
        await redis_cache.delete(f"group:{group_id}:items:{user['user_id']}")
        await redis_cache.delete("groups:all")
        print("Cache invalidated for group, group items, and all groups")
        return {"message": "Group deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get all groups
async def get_all_groups():
    try:
        # Check cache first
        cached = await redis_cache.get("groups:all")
        if cached:
            print("Cache hit for all groups")
            return JSONResponse(content=cached)
        
        # Cache miss: Query DB and cache
        groups = model_get_all_groups()
        await redis_cache.set("groups:all", groups, ttl=300)
        print("Cache set for all groups")
        return JSONResponse(content=groups)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get a group by ID
async def get_group_by_id(group_id: int):
    try:
        # Check cache first
        cached = await redis_cache.get(f"group:{group_id}")
        if cached:
            print("Cache hit for group by ID")
            return JSONResponse(content=cached)
        
        # Cache miss: Query DB and cache
        group = model_get_group_by_id(group_id)
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        await redis_cache.set(f"group:{group_id}", group, ttl=300)
        print("Cache set for group by ID")
        return JSONResponse(content=group)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get all items in a group
async def get_group_items(group_id: int, user=Depends(get_current_user)):
    try:
        # Check group ownership first
        group = model_get_group_by_id(group_id)
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        if group["user_id"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorized to view this group")
        
        # Check cache for items
        cache_key = f"group:{group_id}:items:{user['user_id']}"
        cached = await redis_cache.get(cache_key)
        if cached:
            print("Cache hit for group items")
            return JSONResponse(content=cached)
        
        # Cache miss: Query DB and cache
        items = model_get_group_items(user["user_id"], group_id)
        await redis_cache.set(cache_key, items, ttl=300)
        print("Cache set for group items")
        return JSONResponse(content=items)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))