"""Plan-based feature access. Do not hard-code plans in UI components; ask this service."""

from app.core.config import Settings

FREE = "free"
PREMIUM = "premium"

GENERATE = "generate"
ENHANCE = "enhance"

FEATURES = ("generate_full_post", "enhance_full_post", "post_variations", "advanced_analysis")


class FeatureAccessService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def can(self, plan: str, feature: str) -> bool:
        if plan == PREMIUM:
            return True
        if feature == "generate_full_post":
            return self._settings.free_full_post_enabled
        return False

    def daily_limit(self, plan: str, usage_feature: str) -> int:
        if plan == PREMIUM:
            return self._settings.premium_daily_cap
        if usage_feature == GENERATE:
            return self._settings.free_generations_per_day
        if usage_feature == ENHANCE:
            return self._settings.free_enhancements_per_day
        return 0

    def max_variations(self, plan: str) -> int:
        return self._settings.premium_max_variations if plan == PREMIUM else 1
