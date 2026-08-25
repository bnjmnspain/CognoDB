MATCH (a:User {id: $id})-[:FOLLOWS]->(b:User)
RETURN b.id
