import time
from typing import List, Tuple
from arango import ArangoClient
from .base import BaseLoader


class ArangoDBLoader(BaseLoader):
    def __init__(self, config: dict):
        super().__init__(config)
        self.client = None
        self.db = None

    def connect(self):
        self.client = ArangoClient(hosts=self.config["host"])
        self.db = self.client.db(
            self.config.get("database", "_system"),
            username=self.config["username"],
            password=self.config["password"],
        )

    def close(self):
        pass

    def create_schema(self):
        if not self.db.has_collection("users"):
            self.db.create_collection("users")
        if not self.db.has_collection("follows"):
            self.db.create_collection("follows", edge=True)

    def load_nodes(self, node_ids: List[int]):
        collection = self.db.collection("users")
        batch = [{"_key": str(nid), "id": nid} for nid in node_ids]
        for doc in batch:
            collection.insert(doc, overwrite=True)

    def load_relationships(self, edges: List[Tuple[int, int]]):
        collection = self.db.collection("follows")
        batch = []
        for src, tgt in edges:
            batch.append({
                "_from": f"users/{src}",
                "_to": f"users/{tgt}",
            })
        for doc in batch:
            collection.insert(doc, overwrite=True)

    def create_indexes(self):
        collection = self.db.collection("users")
        try:
            collection.add_hash_index(fields=["id"], unique=True)
        except Exception:
            pass

    def count_nodes(self) -> int:
        collection = self.db.collection("users")
        return collection.count()

    def count_relationships(self) -> int:
        collection = self.db.collection("follows")
        return collection.count()

    def clear(self):
        if self.db.has_collection("follows"):
            self.db.collection("follows").truncate()
        if self.db.has_collection("users"):
            self.db.collection("users").truncate()
