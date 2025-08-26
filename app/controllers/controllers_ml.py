from fastapi import HTTPException, Depends, Request
from fastapi.responses import Response
from app.auth.jwt import authenticate_token
from app.utils.ml_utils import PriceModel
from app.models import model_save_model_index, model_get_model_index, model_get_group_items, model_get_group_by_id, model_delete_model_index

# Handle training groups of models, go through each item in the group and train them
async def group_train_model(request: Request, user=Depends(authenticate_token)):
    try:
        data = await request.json()
        group_id = data.get("group_id")
        if not group_id:
            raise HTTPException(status_code=400, detail="Group ID is required")
        
        group_items = model_get_group_items(user["user_id"], group_id)
        if not group_items:
            raise HTTPException(status_code=404, detail="Group not found or no items in group")

        results = []
        for item in group_items:
            item_id = item["id"]
            item_json = item.get("item_json", {})
            price_history = item_json.get("prices")
            price_history = {"prices": price_history}

            # TODO: Add a json structure validation

            model = PriceModel(user["user_id"], item_id)
            model_info = model.create_model(price_history)
            save_info = model_save_model_index(
                user["user_id"],
                group_id,
                item_id,
                model_info["data_hash"],
                model_info["model_path"],
                model_info["scaler_path"],
                model_info["stats_path"]
            )
            results.append({"item_id": item_id, "model_info": save_info})

        if not results:
            raise HTTPException(status_code=400, detail="No models trained (no price history for any items)")

        return {"success": True, "trained_models": results}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to train models for group: {str(e)}")

# Get a group that have generated models
async def get_group_with_models(group_id: int, user=Depends(authenticate_token)):
    try:
        group = model_get_group_by_id(group_id)
        if not group or group.get("user_id") != user["user_id"]:
            raise HTTPException(status_code=404, detail="Group not found")

        items = model_get_group_items(user["user_id"], group_id)
        items_with_models = []
        for item in items:
            item_id = item["id"]
            item_name = item["item_name"]
            model_info = model_get_model_index(user["user_id"], item_id)
            if model_info:
                items_with_models.append({
                    "item_id": item_id,
                    "item_name": item_name
                })

        if not items_with_models:
            raise HTTPException(status_code=404, detail="No generated models found for this group")

        return {
            "group_id": group_id,
            "group_name": group["group_name"],
            "items": items_with_models
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch group with models: {str(e)}")

# Delete group that have generated models
async def delete_group_model(group_id: int, user=Depends(authenticate_token)):
    try:
        result = model_delete_model_index(user["user_id"], group_id)
        print(result)
        if result.get("deleted"):
            return {"success": True, "message": "Models deleted for group", "group_id": group_id}
        else:
            raise HTTPException(status_code=404, detail="No models found for this group and user")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete models for group: {str(e)}")

async def predict_item_prices(request: Request, user=Depends(authenticate_token)):
    try:
        data = await request.json()
        item_id = data.get("item_id")
        start_time = data.get("start_time")
        end_time = data.get("end_time")

        if not item_id or not start_time or not end_time:
            raise HTTPException(status_code=400, detail="item_id, start_time, and end_time are required")

        model_info = model_get_model_index(user["user_id"], item_id)
        if not model_info:
            raise HTTPException(status_code=404, detail="Model not found for user/item")

        model = PriceModel(user["user_id"], item_id)
        prediction = model.generate_prediction(
            start_time,
            end_time,
            model_info["model_path"],
            model_info["scaler_path"],
            model_info["stats_path"]
        )
        img_bytes = model._generate_prediction_graph(prediction["result"])
        return Response(content=img_bytes, media_type="image/png")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate prediction: {str(e)}")