from abc import ABC, abstractmethod
from typing import List

class ISiteConnector(ABC):
    @abstractmethod
    def request(self, url: str, method: str, headers: dict = {}, data: dict = {}) -> str:
        raise NotImplementedError
    
    @abstractmethod
    def get_page(self, url: str, headless: bool = False, need_scroll_down = False) -> List[str]:
        raise NotImplementedError
    
    @abstractmethod
    def slow_scroll_down(self, page) -> None:
        raise NotImplementedError


    