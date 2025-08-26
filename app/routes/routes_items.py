from fastapi import APIRouter
from app.controllers import (
    create_group,
    update_group_name,
    add_item_to_group,
    remove_item_from_group,
    delete_group,
    get_all_groups,
    get_group_by_id,
    get_group_items,
    group_train_model,
    predict_item_prices,
    get_group_with_models,
    delete_group_model
)

router = APIRouter()

# TODO: Add swagger documentation


# PUBLIC GROUPS

# GET /
# Takes: No body, no authentication.
# Returns: JSON list of all groups.
router.get("/")(get_all_groups)

# GET /{group_id}
# Takes: No body, no authentication.
# Returns: JSON with group details for the given group_id, or 404 if not found.
router.get("/{group_id}")(get_group_by_id)


# PRIVATE GROUPS

# POST /
# Takes: JSON body with 'title' (str). Requires authentication (JWT).
# Returns: JSON with group info if created, or 400/500 error if missing fields or server error.
router.post("/")(create_group)

# PUT /{group_id}
# Takes: JSON body with 'title' (str). Requires authentication (JWT).
# Returns: JSON message if updated, or 404/400/500 error if not found or missing fields.
router.put("/{group_id}")(update_group_name)

# DELETE /{group_id}
# Takes: No body. Requires authentication (JWT).
# Returns: JSON message if deleted, or 404/500 error if not found or server error.
router.delete("/{group_id}")(delete_group)

# POST /{group_id}/items
# Takes: JSON body with 'item_name' (str) and 'item_json' (dict). Requires authentication (JWT).
# Returns: JSON message and item id if added, or 404/400/500 error if not found or missing fields.
router.post("/{group_id}/items")(add_item_to_group)

# GET /{group_id}/items
# Takes: No body. Requires authentication (JWT).
# Returns: JSON list of items in the group, or 500 error if server error.
router.get("/{group_id}/items")(get_group_items)

# DELETE /{group_id}/items
# Takes: JSON body with 'item_name' (str). Requires authentication (JWT).
# Returns: JSON message if removed, or 404/400/500 error if not found or missing fields.
router.delete("/{group_id}/items")(remove_item_from_group)


# PRIVATE MODELS

# POST /{group_id}/train
# Takes: No body. Requires authentication (JWT).
# Returns: JSON with training results, or 400/500 error if group/items not found or server error.
router.post("/{group_id}/train")(group_train_model)

# GET /{group_id}/model
# Takes: No body. Requires authentication (JWT).
# Returns: JSON with model info for the group, or 404/500 error if not found or server error.
router.get("/{group_id}/model")(get_group_with_models)

# DELETE /{group_id}/model
# Takes: No body. Requires authentication (JWT).
# Returns: JSON message if model deleted, or 404/500 error if not found or server error.
router.delete("/{group_id}/model")(delete_group_model)

# POST /{group_id}/predict
# Takes: No body. Requires authentication (JWT).
# Returns: JSON with prediction results, or 400/500 error if group/items not found or server error.
router.post("/{group_id}/predict")(predict_item_prices)