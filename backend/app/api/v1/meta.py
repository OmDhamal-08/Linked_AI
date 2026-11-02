from fastapi import APIRouter, Depends

from app.api.deps import get_app_container
from app.core.taxonomy import public_options
from app.services.container import Container

router = APIRouter(prefix="/meta", tags=["meta"])


@router.get("/taxonomy")
def taxonomy():
    """Categories, tones, post types and other options. The frontend reads these instead of hard-coding them."""
    return public_options()


@router.get("/plans")
def plans(c: Container = Depends(get_app_container)):
    """Plan limits from configuration, so pricing copy always matches the running system."""
    s = c.settings
    return {
        "free": {
            "generations_per_day": s.free_generations_per_day,
            "enhancements_per_day": s.free_enhancements_per_day,
            "full_post_generation": c.access.can("free", "generate_full_post"),
            "enhanced_post": c.access.can("free", "enhance_full_post"),
            "variations": c.access.max_variations("free"),
            "advanced_analysis": c.access.can("free", "advanced_analysis"),
        },
        "premium": {
            "daily_cap": s.premium_daily_cap,
            "full_post_generation": True,
            "enhanced_post": True,
            "variations": c.access.max_variations("premium"),
            "advanced_analysis": True,
        },
    }
