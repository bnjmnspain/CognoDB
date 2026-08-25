MATCH (a:User {id: $id})-[:FOLLOWS]->(:User)-[:FOLLOWS]->(c:User)
RETURN c.id
