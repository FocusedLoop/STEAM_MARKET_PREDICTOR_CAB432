from app.models import model_get_or_create_user_profile


async def get_user_profile(cognito_claims: dict):
    user_id = cognito_claims.get("sub")
    username = cognito_claims.get("cognito:username")

    user_profile = model_get_or_create_user_profile(user_id, username)
    return user_profile
