from fastapi import HTTPException, Depends, Request
from fastapi.responses import Response
from app.auth.cognito_jwt import get_current_user
from app.models import model_save_ml_index, model_get_ml_index, model_get_group_items, model_get_group_by_id, model_delete_ml_index
from app.services.sklearn import SklearnClient
from app.services.redis import redis_cache
from shared import S3StorageManager
from datetime import datetime
import base64, os

# Initialize sklearn client
sklearn_client = SklearnClient()

# Handle training groups of models, go through each item in the group and train them
async def group_train_model(request: Request, user=Depends(get_current_user)):
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
            is_valid, error_msg = await sklearn_client.validate_price_history(price_history)
            if not is_valid:
                raise HTTPException(status_code=400, detail=f"Invalid price history for item {item_id}: {error_msg}")

            # Call sklearn service to train model
            try:
                response = await sklearn_client.train_model(
                    user["user_id"], 
                    user["username"], 
                    item_id, 
                    item_name, 
                    price_history
                )
                
                if not response.get("success"):
                    raise HTTPException(status_code=500, detail=f"Training failed for item {item_id}")
                
                model_data = response["data"]
                save_info = model_save_ml_index(
                    user["user_id"],
                    group_id,
                    item_id,
                    model_data["data_hash"]
                )
                
                results.append({
                    "item_id": item_id,
                    "item_name": item_name,
                    "save_info": save_info,
                    "graph": model_data["graph"],
                    "graph_url": model_data["graph_url"],
                    "metrics": model_data.get("metrics", {})
                })
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Training failed for item {item_id}: {str(e)}")

        if not results:
            raise HTTPException(status_code=400, detail="No models trained (no price history for any items)")

        # Invalidate cache for this group's models
        # If only one item, return the singular graph and URL
        await redis_cache.delete(f"group:{group_id}:models:{user['user_id']}")
        print("Cache deleted for group models")
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
async def get_group_with_models(group_id: int, user=Depends(get_current_user)):
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
        print("Cache set for group model items")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch group with models: {str(e)}")

# Delete group that have generated models
async def delete_group_model(group_id: int, user=Depends(get_current_user)):
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
            print("Cache deleted for group models")
            return {"success": True, "message": "Models deleted for group", "group_id": group_id}
        else:
            raise HTTPException(status_code=404, detail="No models found for this group or user")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete models for group: {str(e)}")

# NOTE: Graphs have no way to be deleted currently
async def predict_item_prices(group_id: int, request: Request, user=Depends(get_current_user)):
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

        # Call sklearn service to predict price
        try:
            response = await sklearn_client.predict_price(
                user["user_id"],
                user["username"], 
                item_id,
                item_name,
                model_info["data_hash"],
                start_time.isoformat(),
                end_time.isoformat()
            )
            
            if not response.get("success"):
                raise HTTPException(status_code=500, detail="Prediction failed")
            
            prediction_data = response["data"]
            return {
                "graph": prediction_data["graph"],
                "graph_url": prediction_data["graph_url"]
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate prediction: {str(e)}")