# Utiliza la imagen base de Neo4j desde Docker Hub
FROM neo4j

# Establece las variables de entorno para Neo4j (puerto, contraseña, etc.)
ENV NEO4J_AUTH=neo4j/neo4j
ENV NEO4J_dbms_security_procedures_unrestricted=apoc.*

# Exponer puertos de Neo4j
EXPOSE 7474 7687

# Puedes añadir configuraciones adicionales si es necesario

# Ejecuta Neo4j
CMD ["neo4j"]
