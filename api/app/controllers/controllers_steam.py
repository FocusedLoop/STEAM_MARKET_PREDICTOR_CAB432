from fastapi import HTTPException, Request, Depends
from app.auth.cognito_jwt import get_current_user 
from fastapi.responses import JSONResponse
from app.services import steamAPI
import logging

logger = logging.getLogger(__name__)

# Get top games for the authenticated user
async def get_steam_top_games(user=Depends(get_current_user)):
    try:
        logger.info(f"Fetching top games for user {user['user_id']}")
        steam = steamAPI(user["steam_id"])
        top_games = steam.find_suitable_games()
        logger.info(f"Successfully retrieved top games for user {user['user_id']}")
        return JSONResponse(content=top_games)
    except Exception as e:
        logger.error(f"Failed to fetch top games for user {user['user_id']}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Get price history for a specific item
async def get_steam_item_history(request: Request, user=Depends(get_current_user)):
    try:
        logger.info(f"Fetching item history for user {user['user_id']}")
        data = await request.json()
        appid = data.get("appid")
        item_name = data.get("item_name")
        if not appid or not item_name:
            logger.warning(f"Missing appid or item_name for user {user['user_id']}")
            raise HTTPException(status_code=400, detail="App Id and Item name is required")
        
        steam = steamAPI(user["steam_id"])
        try:
            logger.info(f"Searching for item '{item_name}' in app {appid} for user {user['user_id']}")
            item_info = steam.search_item(appid, item_name)
        except ValueError as e:
            logger.warning(f"Item not found: {str(e)} for user {user['user_id']}")
            raise HTTPException(status_code=404, detail=str(e))
        if not item_info or not item_info.get("market_hash_name"):
            logger.warning(f"Item not found in inventory for user {user['user_id']}")
            raise HTTPException(status_code=404, detail="Item not found in inventory")
        
        item_history_url = steam.generate_price_history_url(
            appid=appid,
            marker_hash=item_info["market_hash_name"],
        )
        logger.info(f"Successfully generated price history URL for user {user['user_id']}")
        return JSONResponse(content={"price_history_url": item_history_url})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch item history for user {user['user_id']}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))