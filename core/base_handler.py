from abc import ABC, abstractmethod
from typing import List, Tuple

class BaseHandler(ABC):
    def __init__(self, user_id: int):
        self.user_id = user_id
        
    @abstractmethod
    async def auth_accounts(self, accounts: List[Tuple[str, str, str]]):
        pass
    
    @abstractmethod
    async def start_registration(self, accounts: List[Tuple[str, str, str]]):
        pass
    
    @abstractmethod
    async def start_mining(self, accounts: List[Tuple[str, str, str]]):
        pass
    
    @abstractmethod
    async def stop(self):
        pass