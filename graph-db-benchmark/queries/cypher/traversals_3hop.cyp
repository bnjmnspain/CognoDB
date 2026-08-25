MATCH (a:User {id: $id})-[:FOLLOWS]->(:User)-[:FOLLOWS]->(:User)-[:FOLLOWS]->(d:User)
RETURN d.id
