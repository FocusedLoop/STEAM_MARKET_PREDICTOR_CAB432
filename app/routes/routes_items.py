from fastapi import APIRouter
from app.controllers import (
    create_group,
    update_group_name,
    add_item_to_group,
    remove_item_from_group,
    delete_group,
    get_all_groups,
    get_groups_by_id,
    get_steam_top_games,
    get_steam_item_history
)

router = APIRouter()

# TODO: Setup swagger

router.post("/groups")(create_group)

router.put("/groups/{group_id}")(update_group_name)

router.post("/groups/{group_id}/items")(add_item_to_group)

router.delete("/groups/{group_id}/items")(remove_item_from_group)

router.delete("/groups/{group_id}")(delete_group)

router.get("/groups")(get_all_groups)

router.get("/groups/{group_id}")(get_groups_by_id)

router.get("/steam/top-games")(get_steam_top_games)

router.get("/steam/item-history")(get_steam_item_history)

# from app.controllers import (
#     get_all_tasks, 
#     get_task_by_id, 
#     create_task, 
#     update_task,
#     delete_task
#     )
# router.get("/", response_model=list)(get_all_tasks)
# router.get("/{task_id}", response_model=dict)(get_task_by_id)
# router.post("/", response_model=dict)(create_task)
# router.put("/{task_id}", response_model=dict)(update_task)
# router.delete("/{task_id}", response_model=dict)(delete_task)