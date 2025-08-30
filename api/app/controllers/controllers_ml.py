from fastapi import HTTPException, Depends, Request
from fastapi.responses import Response
from app.auth.jwt import authenticate_token
from app.utils.ml_utils import validate_price_history, PriceModel
from app.models import model_save_ml_index, model_get_ml_index, model_get_group_items, model_get_group_by_id, model_delete_ml_index
from datetime import datetime
import base64, os

# Handle training groups of models, go through each item in the group and train them
async def group_train_model(request: Request, user=Depends(authenticate_token)):
    try:
        data = await request.json()
        group_id = data.get("group_id")
        if not group_id:
            raise HTTPException(status_code=400, detail="Group ID is required")
        
        # Check if the group has a generated model
        group = model_get_group_by_id(group_id)
        if group.get("has_model"):
            raise HTTPException(status_code=400, detail="Models already exist for this group. Please delete them before retraining.")
        
        group_items = model_get_group_items(user["user_id"], group_id)
        if not group_items:
            raise HTTPException(status_code=404, detail="Group not found or no items in group")

        results = []
        for item in group_items:
            item_id = item["id"]
            item_name = item["item_name"]
            item_json = item.get("item_json", {})
            price_history = item_json.get("prices")
            price_history = {"prices": price_history}

            # Validate JSON structure
            is_valid, error_msg = validate_price_history(price_history)
            if not is_valid:
                raise HTTPException(status_code=400, detail=f"Invalid price history for item {item_id}: {error_msg}")

            model = PriceModel(user["user_id"], user["username"], item_id, item_name)
            model_info = model.create_model(price_history)
            save_info = model_save_ml_index(
                user["user_id"],
                group_id,
                item_id,
                model_info["data_hash"],
                model_info["model_path"],
                model_info["scaler_path"],
                model_info["stats_path"]
            )
            results.append({
                "item_id": item_id,
                "item_name": item_name,
                "save_info": save_info,
                "graph": model_info.get("graph"),
                "metrics": model_info.get("metrics", {})
            })

        if not results:
            raise HTTPException(status_code=400, detail="No models trained (no price history for any items)")

        # If only one item, return the singular graph
        if len(results) == 1:
            return Response(content=results[0]["graph"], media_type="image/png")

        # If multiple, return a JSON with base64-encoded graphs
        for r in results:
            if r["graph"]:
                r["graph"] = base64.b64encode(r["graph"]).decode("utf-8")
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
            model_info = model_get_ml_index(user["user_id"], item_id)
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
        # Get all model_index entries for this group/user before deleting
        items = model_get_group_items(user["user_id"], group_id)
        model_files = []
        for item in items:
            model_info = model_get_ml_index(user["user_id"], item["id"])
            if model_info:
                model_files.append(model_info.get("model_path"))
                model_files.append(model_info.get("scaler_path"))
                model_files.append(model_info.get("stats_path"))

        # Delete from DB
        result = model_delete_ml_index(user["user_id"], group_id)
        #print(result)
        if result.get("deleted"):
            # Delete files from disk
            for f in model_files:
                if f and os.path.exists(f):
                    try:
                        os.remove(f)
                    except Exception as e:
                        print(f"Warning: Could not delete {f}: {e}")
            return {"success": True, "message": "Models deleted for group", "group_id": group_id}
        else:
            raise HTTPException(status_code=404, detail="No models found for this group or user")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete models for group: {str(e)}")

# Handle predicting item prices
async def predict_item_prices(group_id: int, request: Request, user=Depends(authenticate_token)):
    try:
        data = await request.json()
        item_id = data.get("item_id")
        items = model_get_group_items(user["user_id"], group_id)
        item = next((i for i in items if i["id"] == item_id), None)
        if not item:
            raise HTTPException(status_code=404, detail="Item not found in group")
        item_name = item.get("item_name")

        group = model_get_group_by_id(group_id)
        if not group or group.get("user_id") != user["user_id"]:
            raise HTTPException(status_code=404, detail="Group not found")

        try:
            start_time = datetime.fromisoformat(data.get("start_time"))
            end_time = datetime.fromisoformat(data.get("end_time"))
        except Exception:
            raise HTTPException(status_code=400, detail="start_time and end_time must be in ISO 8601 datetime format")

        if not item_id or not start_time or not end_time:
            raise HTTPException(status_code=400, detail="item_id, start_time, and end_time are required")

        model_info = model_get_ml_index(user["user_id"], item_id)
        if not model_info:
            raise HTTPException(status_code=404, detail="Model not found for user/item")

        model = PriceModel(user["user_id"], user["username"], item_id, item_name)
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