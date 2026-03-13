from abc import ABC, abstractmethod
import uuid

class BaseProvider(ABC):
    def __init__(self, state: str | None = None):
        # auto-generate a UUID if state is not provided
        self.state = state or str(uuid.uuid4())

    @abstractmethod
    async def get_auth_url(self):
        pass

    @abstractmethod
    async def exchange_code(self, code: str):
        pass

    @abstractmethod
    async def get_user_info(self, access_token: str):
        pass