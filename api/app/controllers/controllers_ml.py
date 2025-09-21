from fastapi import HTTPException, Depends, Request
from fastapi.responses import Response
from app.auth.jwt import authenticate_token
from app.utils.ml_utils import validate_price_history, PriceModel
from app.models import model_save_ml_index, model_get_ml_index, model_get_group_items, model_get_group_by_id, model_delete_ml_index
from app.utils.utils_redis import redis_cache
from app.utils.utils_s3 import S3StorageManager
from datetime import datetime
import base64, os

# Handle training groups of models, go through each item in the group and train them
# async def group_train_model(request: Request, user=Depends(authenticate_token)):
#     try:
#         print("BEGINING GROUP TRAINING===============================")
#         data = await request.json()
#         group_id = data.get("group_id")
#         if not group_id:
#             raise HTTPException(status_code=400, detail="Group ID is required")
        
#         # Check if the group has a generated model
#         group = model_get_group_by_id(group_id)
#         if group.get("has_model"):
#             raise HTTPException(status_code=400, detail="Models already exist for this group. Please delete them before retraining.")
        
#         group_items = model_get_group_items(user["user_id"], group_id)
#         if not group_items:
#             raise HTTPException(status_code=404, detail="Group not found or no items in group")

#         results = []
#         for item in group_items:
#             item_id = item["id"]
#             item_name = item["item_name"]
#             item_json = item.get("item_json", {})
#             price_history = item_json.get("prices")
#             price_history = {"prices": price_history}

#             # Validate JSON structure
#             is_valid, error_msg = validate_price_history(price_history)
#             if not is_valid:
#                 raise HTTPException(status_code=400, detail=f"Invalid price history for item {item_id}: {error_msg}")

#             model = PriceModel(user["user_id"], user["username"], item_id, item_name)
#             model_info = model.create_model(price_history)
#             save_info = model_save_ml_index(
#                 user["user_id"],
#                 group_id,
#                 item_id,
#                 model_info["data_hash"],
#                 model_info["model_path"],
#                 model_info["scaler_path"],
#                 model_info["stats_path"]
#             )
#             results.append({
#                 "item_id": item_id,
#                 "item_name": item_name,
#                 "save_info": save_info,
#                 "graph": base64.b64encode(model_info["graph"]).decode("utf-8"),  # Base64 encode PNG bytes
#                 "graph_url": model_info["graph_url"],  # Include URL
#                 "metrics": model_info.get("metrics", {})
#             })

#         if not results:
#             raise HTTPException(status_code=400, detail="No models trained (no price history for any items)")

#         # Invalidate cache for this group's models
#         # If only one item, return the singular graph and URL
#         await redis_cache.delete(f"group:{group_id}:models:{user['user_id']}")
#         if len(results) == 1:
#             return {
#                 "graph": results[0]["graph"],  # Base64 PNG
#                 "graph_url": results[0]["graph_url"]  # URL
#             }

#         # If multiple, return a JSON with graphs and URLs
#         return {"success": True, "trained_models": results}
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to train models for group: {str(e)}")
async def group_train_model(request: Request, user=Depends(authenticate_token)):
    try:
        print("BEGINING GROUP TRAINING===============================")
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
                model_info["data_hash"]
            )
            results.append({
                "item_id": item_id,
                "item_name": item_name,
                "save_info": save_info,
                "graph": base64.b64encode(model_info["graph"]).decode("utf-8"),  # Base64 encode PNG bytes
                "graph_url": model_info["graph_url"],  # Include URL
                "metrics": model_info.get("metrics", {})
            })

        if not results:
            raise HTTPException(status_code=400, detail="No models trained (no price history for any items)")

        # Invalidate cache for this group's models
        # If only one item, return the singular graph and URL
        await redis_cache.delete(f"group:{group_id}:models:{user['user_id']}")
        if len(results) == 1:
            return {
                "graph": results[0]["graph"],  # Base64 PNG
                "graph_url": results[0]["graph_url"]  # URL
            }

        # If multiple, return a JSON with graphs and URLs
        return {"success": True, "trained_models": results}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to train models for group: {str(e)}")

# Get a group that have generated models (Read: Cache result)
async def get_group_with_models(group_id: int, user=Depends(authenticate_token)):
    try:
        # Check cache first
        cache_key = f"group:{group_id}:models:{user['user_id']}"
        cached = await redis_cache.get(cache_key)
        if cached:
            print("Cache hit for group model items")
            return cached
        
        # Cache miss: Query DB and cache
        group = model_get_group_by_id(group_id)
        if not group or group.get("user_id") != user["user_id"]:
            raise HTTPException(status_code=404, detail="Group not found")

        # Get model info for each item
        s3_manager = S3StorageManager()
        items = model_get_group_items(user["user_id"], group_id)
        items_with_models = []
        for item in items:
            item_id = item["id"]
            item_name = item["item_name"]
            model_info = model_get_ml_index(user["user_id"], item_id)
            if model_info:
                data_hash = model_info["data_hash"]
                
                # Generate download URLs for the artifacts
                model_url = None
                scaler_url = None
                stats_url = None
                graph_url = None
                if s3_manager.s3_client:
                    model_key = f"models/model_{data_hash}.joblib"
                    model_url = s3_manager.generate_download_url(model_key)
                    scaler_key = f"scalers/scaler_{data_hash}.joblib"
                    scaler_url = s3_manager.generate_download_url(scaler_key)
                    stats_key = f"features/feature_means_{data_hash}.json"
                    stats_url = s3_manager.generate_download_url(stats_key)
                    graph_key = f"graphs/training_graph_{data_hash}.png"
                    graph_url = s3_manager.generate_download_url(graph_key)
                items_with_models.append({
                    "item_id": item_id,
                    "item_name": item_name,
                    "model_url": model_url,
                    "scaler_url": scaler_url,
                    "stats_url": stats_url,
                    "graph_url": graph_url
                })

        if not items_with_models:
            raise HTTPException(status_code=404, detail="No generated models found for this group")

        result = {
            "group_id": group_id,
            "group_name": group["group_name"],
            "items": items_with_models
        }
        await redis_cache.set(cache_key, result, ttl=300)
        return result
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
                data_hash = model_info["data_hash"]
                model_files.append(f"models/model_{data_hash}.joblib")
                model_files.append(f"scalers/scaler_{data_hash}.joblib")
                model_files.append(f"features/feature_means_{data_hash}.json")
                model_files.append(f"graphs/training_graph_{data_hash}.png")

        # Delete from DB
        result = model_delete_ml_index(user["user_id"], group_id)
        if result.get("deleted"):
            # Delete files from disk or S3
            s3_manager = S3StorageManager()
            for f in model_files:
                if os.path.exists(f):
                    try:
                        os.remove(f)
                    except Exception as e:
                        print(f"Warning: Could not delete {f}: {e}")
                elif s3_manager.s3_client:
                    try:
                        s3_manager.delete_file(f)
                    except Exception as e:
                        print(f"Warning: Could not delete S3 object {f}: {e}")
            
            # Invalidate cache for this group's models
            await redis_cache.delete(f"group:{group_id}:models:{user['user_id']}")
            return {"success": True, "message": "Models deleted for group", "group_id": group_id}
        else:
            raise HTTPException(status_code=404, detail="No models found for this group or user")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete models for group: {str(e)}")


#TODO: Upload trained model files to S3 and update DB paths accordingly
# async def upload_group_models_to_s3(group_id: int, user=Depends(authenticate_token)):
# NOTE: Graphs have no way to be deleted currently
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
            model_info["data_hash"]
        )
        # Return JSON with both base64 graph and URL
        return {
            "graph": base64.b64encode(prediction["graph"]).decode("utf-8"),  # Base64 PNG
            "graph_url": prediction["graph_url"]  # URL
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate prediction: {str(e)}")