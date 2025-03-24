from fastapi import APIRouter

users_router = APIRouter()


@users_router.get("/all_users")
async def read_users():
    return [{"username": "Rick"}, {"username": "Morty"}]




