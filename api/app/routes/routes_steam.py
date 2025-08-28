from fastapi import APIRouter
from app.controllers import get_steam_top_games, get_steam_item_history

router = APIRouter()

# GET /top-games
# Takes: No body. Requires authentication (JWT).
# Returns: JSON list of the user's top suitable games by playtime.
router.get("/top-games")(get_steam_top_games)

# POST /item-history
# Takes: JSON body with 'appid' (int) and 'item_name' (str). Requires authentication (JWT).
# Returns: JSON with 'price_history_url' for the specified item, or 404/400 error if not found or missing fields.
router.post("/item-history")(get_steam_item_history)