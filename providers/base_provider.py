from abc import ABC, abstractmethod
#import uuid

class BaseProvider(ABC):
    # def __init__(self, state: str | None = None):
    #     # auto-generate a UUID if state is not provided
    #     self.state = state or str(uuid.uuid4())

    # def __init__(self):
    #     # auto-generate a UUID if state is not provided
    #     self.state = None

    @abstractmethod
    async def get_auth_url(self, state: str | None):
        pass

    @abstractmethod
    async def exchange_code(self, code: str, state: str | None):
        pass

    @abstractmethod
    async def get_user_info(self, access_token: str):
        pass