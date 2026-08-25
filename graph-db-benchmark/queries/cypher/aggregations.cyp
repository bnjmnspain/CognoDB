MATCH (n:User)<-[:FOLLOWS]-(f)
RETURN n.id, count(f) AS followers
ORDER BY followers DESC
LIMIT 100
