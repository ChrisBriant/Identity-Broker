from abc import ABC, abstractmethod

class BaseProvider(ABC):

    @abstractmethod
    async def get_auth_url(self):
        pass

    @abstractmethod
    async def exchange_code(self, code: str):
        pass

    @abstractmethod
    async def get_user_info(self, access_token: str):
        pass