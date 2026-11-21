from abc import ABC, abstractmethod


class BaseProvider(ABC):
    def __init__(self, name: str, login_url: str):
        self.name = name
        self.login_url = login_url

    @abstractmethod
    async def fetch_codes(self, email: str, password: str) -> str:
        """Return a human-readable string of available discount codes."""
        pass
