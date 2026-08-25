#!/usr/bin/env python3
from neo4j import GraphDatabase
import os

uri = os.getenv("COGNODB_URI", "")
username = os.getenv("COGNODB_USERNAME", "")
password = os.getenv("COGNODB_PASSWORD", "")

if not all([uri, username, password]):
    # Try reading .env directly
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())
        uri = os.getenv("COGNODB_URI", "")
        username = os.getenv("COGNODB_USERNAME", "")
        password = os.getenv("COGNODB_PASSWORD", "")

print(f"Connecting to {uri}...")
driver = GraphDatabase.driver(uri, auth=(username, password))

try:
    with driver.session(database="cognodb") as session:
        result = session.run("RETURN 1 AS n")
        print(f"Connection OK: {result.single()['n']}")
        nodes = session.run("MATCH (n) RETURN count(n) AS c").single()["c"]
        rels = session.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
        print(f"Current state: {nodes} nodes, {rels} relationships")
except Exception as e:
    print(f"Connection failed: {e}")
finally:
    driver.close()
