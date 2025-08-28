from fastapi import Request, HTTPException
from app.models import model_get_user_by_username, model_get_user_id_by_username, model_get_steam_id_by_username, model_create_user
from app.auth.jwt import generate_access_token

# Handle user login
async def login(request: Request):
    data = await request.json()
    username = data.get('username')
    password = data.get('password')
    user = model_get_user_by_username(username)
    if not user or user['password'] != password:
        raise HTTPException(status_code=401, detail='Unauthorized')
    
    user_id = model_get_user_id_by_username(username)
    steam_id = model_get_steam_id_by_username(username)
    token = generate_access_token(user_id, username, steam_id)
    return { 'authToken': token }

# Handle user sign up
async def sign_up(request: Request):
    data = await request.json()
    username = data.get('username')
    steamd_id = data.get('steam_id')
    password = data.get('password')
    if not username or not password or not steamd_id:
        raise HTTPException(status_code=400, detail='Username, password, and Steam ID are required')
    user = model_get_user_by_username(username)
    if user:
        raise HTTPException(status_code=400, detail='User already exists')
    
    model_create_user(username, password, steamd_id)
    user_id = model_get_user_id_by_username(username)
    steam_id = model_get_steam_id_by_username(username)
    token = generate_access_token(user_id, username, steam_id)
    return { 'authToken': token }