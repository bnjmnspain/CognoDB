import time
from typing import List, Tuple
from gremlin_python.driver import client, serializer
from .base import BaseLoader


class NeptuneLoader(BaseLoader):
    def __init__(self, config: dict):
        super().__init__(config)
        self.client = None

    def connect(self):
        self.client = client.Client(
            f"wss://{self.config['endpoint']}:{self.config['port']}/gremlin",
            "g",
            username=self.config.get("access_key", ""),
            password=self.config.get("secret_key", ""),
            message_serializer=serializer.GraphSONSerializersV2d0(),
        )
        self.client.submit("g.V().limit(1)").all().result()

    def close(self):
        if self.client:
            self.client.close()

    def create_schema(self):
        pass

    def load_nodes(self, node_ids: List[int]):
        batch = []
        for nid in node_ids:
            batch.append(f"g.addV('User').property('id', {nid})")
        query = "; ".join(batch)
        self.client.submit(query).all().result()

    def load_relationships(self, edges: List[Tuple[int, int]]):
        batch_size = 500
        for i in range(0, len(edges), batch_size):
            batch = edges[i:i + batch_size]
            gremlin_stmts = []
            for src, tgt in batch:
                gremlin_stmts.append(
                    f"g.V().has('User','id',{src}).addE('FOLLOWS').to(g.V().has('User','id',{tgt}))"
                )
            query = "; ".join(gremlin_stmts)
            self.client.submit(query).all().result()

    def create_indexes(self):
        self.client.submit("g.V().hasLabel('User').has('id').values('id').barrier()").all().result()
        self.client.submit("g.V().hasLabel('User').has('id').elementMap()").all().result()

    def count_nodes(self) -> int:
        result = self.client.submit("g.V().hasLabel('User').count()").all().result()
        return int(result[0]) if result else 0

    def count_relationships(self) -> int:
        result = self.client.submit("g.E().hasLabel('FOLLOWS').count()").all().result()
        return int(result[0]) if result else 0

    def clear(self):
        self.client.submit("g.V().drop()").all().result()
        self.client.submit("g.E().drop()").all().result()
