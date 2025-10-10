from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from app.auth.cognito_jwt import get_current_user
from app.services.sklearn import SklearnClient
from app.services.redis import redis_cache
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
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize sklearn client
sklearn_client = SklearnClient()

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
        logger.info(f"Group created: {title} for user {user['user_id']}")
        return {
            "message": "Group created",
            **result
        }
    except Exception as e:
        logger.error(f"Error creating group: {str(e)}")
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
        logger.info(f"Cache invalidated for group {group_id} and all groups")
        return {"message": f"Group name updated to {title}"}
    except Exception as e:
        logger.error(f"Error updating group name: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Add item to an existing group
async def add_item_to_group(group_id: int, request: Request, user=Depends(get_current_user)):
    data = await request.json()
    item_name = data.get("item_name")
    item_json = data.get("item_json")

    is_valid, error_msg = sklearn_client.validate_price_history(item_json)
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
        logger.info(f"Cache deleted for group {group_id} items")
        return {
            "message": f"Item {item_name} added to group",
            "id": result.get("id")
        }
    except Exception as e:
        logger.error(f"Error adding item to group: {str(e)}")
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
        logger.info(f"Cache deleted for group {group_id} items")
        return {"message": f"Item {item_name} removed from group"}
    except Exception as e:
        logger.error(f"Error removing item from group: {str(e)}")
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
        logger.info(f"Cache invalidated for group {group_id}, group items, and all groups")
        return {"message": "Group deleted"}
    except Exception as e:
        logger.error(f"Error deleting group: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Get all groups
async def get_all_groups():
    try:
        # Check cache first
        cached = await redis_cache.get("groups:all")
        if cached:
            logger.info("Cache hit for all groups")
            return JSONResponse(content=cached)
        
        # Cache miss: Query DB and cache
        groups = model_get_all_groups()
        await redis_cache.set("groups:all", groups, ttl=300)
        logger.info("Cache set for all groups")
        return JSONResponse(content=groups)
    except Exception as e:
        logger.error(f"Error getting all groups: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Get a group by ID
async def get_group_by_id(group_id: int):
    try:
        # Check cache first
        cached = await redis_cache.get(f"group:{group_id}")
        if cached:
            logger.info(f"Cache hit for group {group_id}")
            return JSONResponse(content=cached)
        
        # Cache miss: Query DB and cache
        group = model_get_group_by_id(group_id)
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        await redis_cache.set(f"group:{group_id}", group, ttl=300)
        logger.info(f"Cache set for group {group_id}")
        return JSONResponse(content=group)
    except Exception as e:
        logger.error(f"Error getting group by ID: {str(e)}")
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
            logger.info(f"Cache hit for group {group_id} items")
            return JSONResponse(content=cached)
        
        # Cache miss: Query DB and cache
        items = model_get_group_items(user["user_id"], group_id)
        await redis_cache.set(cache_key, items, ttl=300)
        logger.info(f"Cache set for group {group_id} items")
        return JSONResponse(content=items)
    except Exception as e:
        logger.error(f"Error getting group items: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))