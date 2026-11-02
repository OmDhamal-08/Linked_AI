from fastapi import APIRouter

from app.api.v1 import admin, auth, health, meta, posts, subscriptions, usage, users
from app.core.config import get_settings

api_router = APIRouter(prefix=get_settings().api_prefix)
for module in (health, auth, users, posts, usage, subscriptions, admin, meta):
    api_router.include_router(module.router)
