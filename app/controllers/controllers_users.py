from fastapi import Request, HTTPException
from app.models import get_user_by_username, create_user
from app.auth.jwt import generate_access_token

async def login(request: Request):
    data = await request.json()
    username = data.get('username')
    password = data.get('password')
    user = get_user_by_username(username)
    if not user or user['password'] != password:
        raise HTTPException(status_code=401, detail='Unauthorized')
    
    token = generate_access_token(username)
    return { 'authToken': token }

async def sign_up(request: Request):
    data = await request.json()
    username = data.get('username')
    steamd_id = data.get('steam_id')
    password = data.get('password')
    user = get_user_by_username(username)
    if user:
        raise HTTPException(status_code=400, detail='User already exists')
    
    create_user(username, password, steamd_id)
    token = generate_access_token(username)
    return { 'authToken': token }


