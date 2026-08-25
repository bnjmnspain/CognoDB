import time
from typing import List, Tuple
from neo4j import GraphDatabase
from .base import BaseLoader


class MemgraphLoader(BaseLoader):
    def __init__(self, config: dict):
        super().__init__(config)
        self.driver = None

    def connect(self):
        self.driver = GraphDatabase.driver(
            self.config["uri"],
            auth=(self.config["username"], self.config["password"]),
        )
        with self.driver.session(database=self.config.get("database", "memgraph")) as session:
            session.run("RETURN 1")

    def close(self):
        if self.driver:
            self.driver.close()

    def create_schema(self):
        with self.driver.session(database=self.config.get("database", "memgraph")) as session:
            session.run("CREATE INDEX ON :User(id)")

    def load_nodes(self, node_ids: List[int]):
        with self.driver.session(database=self.config.get("database", "memgraph")) as session:
            for nid in node_ids:
                session.run("CREATE (u:User {id: $id})", id=nid)

    def load_relationships(self, edges: List[Tuple[int, int]]):
        batch_size = 1000
        with self.driver.session(database=self.config.get("database", "memgraph")) as session:
            for i in range(0, len(edges), batch_size):
                batch = edges[i:i + batch_size]
                params = {"edges": [{"source": s, "target": t} for s, t in batch]}
                session.run(
                    """
                    UNWIND $edges AS edge
                    MATCH (a:User {id: edge.source}), (b:User {id: edge.target})
                    CREATE (a)-[:FOLLOWS]->(b)
                    """,
                    **params,
                )

    def create_indexes(self):
        with self.driver.session(database=self.config.get("database", "memgraph")) as session:
            session.run("CREATE INDEX ON :User(id)")

    def count_nodes(self) -> int:
        with self.driver.session(database=self.config.get("database", "memgraph")) as session:
            result = session.run("MATCH (n:User) RETURN count(n) AS c")
            return result.single()["c"]

    def count_relationships(self) -> int:
        with self.driver.session(database=self.config.get("database", "memgraph")) as session:
            result = session.run("MATCH ()-[r:FOLLOWS]->() RETURN count(r) AS c")
            return result.single()["c"]

    def clear(self):
        with self.driver.session(database=self.config.get("database", "memgraph")) as session:
            session.run("MATCH (n) DETACH DELETE n")
