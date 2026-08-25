from abc import ABC, abstractmethod
from typing import List, Tuple


class BaseLoader(ABC):
    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def create_schema(self):
        pass

    @abstractmethod
    def load_nodes(self, node_ids: List[int]):
        pass

    @abstractmethod
    def load_relationships(self, edges: List[Tuple[int, int]]):
        pass

    @abstractmethod
    def create_indexes(self):
        pass

    @abstractmethod
    def count_nodes(self) -> int:
        pass

    @abstractmethod
    def count_relationships(self) -> int:
        pass

    @abstractmethod
    def clear(self):
        pass
