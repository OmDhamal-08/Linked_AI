"""Payment abstraction. The MVP ships a mock provider so premium features can be tested
without real payments. Add a Stripe/Razorpay implementation of PaymentProvider later."""

import uuid
from abc import ABC, abstractmethod

from app.core.errors import ForbiddenError


class PaymentProvider(ABC):
    name: str = "base"

    @abstractmethod
    def start_subscription(self, user_id: str, plan: str) -> str:
        """Return an external subscription id (or raise)."""

    @abstractmethod
    def cancel_subscription(self, external_id: str | None) -> None: ...


class MockPaymentProvider(PaymentProvider):
    name = "mock"

    def start_subscription(self, user_id: str, plan: str) -> str:
        return f"mock_sub_{uuid.uuid4().hex[:12]}"

    def cancel_subscription(self, external_id: str | None) -> None:
        return None


class PaymentService:
    def __init__(self, provider: PaymentProvider, *, allow_mock: bool, is_production: bool) -> None:
        self._provider = provider
        self._allow_mock = allow_mock
        self._is_production = is_production

    @property
    def provider_name(self) -> str:
        return self._provider.name

    def ensure_mock_allowed(self) -> None:
        if self._provider.name == "mock" and (self._is_production or not self._allow_mock):
            raise ForbiddenError("Mock payments are disabled in this environment.")

    def start_subscription(self, user_id: str, plan: str) -> str:
        return self._provider.start_subscription(user_id, plan)

    def cancel_subscription(self, external_id: str | None) -> None:
        self._provider.cancel_subscription(external_id)
