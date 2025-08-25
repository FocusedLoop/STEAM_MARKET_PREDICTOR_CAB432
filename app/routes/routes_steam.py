from fastapi import APIRouter
from app.controllers import (
    get_steam_top_games,
    get_steam_item_history,
)

router = APIRouter()

router.get("/top-games")(get_steam_top_games)

router.post("/item-history")(get_steam_item_history)