from neo4j import GraphDatabase

class ExploitDatabase:
    def __init__(self, uri, username, password):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))

    def close(self):
        self.driver.close()

    def load_data(self, row):
        with self.driver.session() as session:
            exploit_node = session.write_transaction(self._create_exploit_node, row)
            exploit_node_id = exploit_node.id
            self._create_platform_node(session, exploit_node_id, row)
            self._create_port_node(session, exploit_node_id, row)
            self._create_tag_nodes(session, exploit_node_id, row)

    def backup(self, path):
        with self.driver.session() as session:
            result = session.run("CALL db.backup($path)", path=path)
            for record in result:
                print(record)

    @staticmethod
    def _create_exploit_node(tx, row):
        return tx.run("""
            MERGE (e:Exploit {id: $id})
            ON CREATE SET e.file = $file, e.description = $description, e.date_published = $date_published,
            e.author = $author, e.type = $type, e.date_added = $date_added, e.date_updated = $date_updated,
            e.verified = $verified, e.codes = $codes, e.tags = $tags, e.aliases = $aliases, 
            e.screenshot_url = $screenshot_url, e.application_url = $application_url, e.source_url = $source_url
            RETURN e
        """, **row).single()[0]

    @staticmethod
    def _create_platform_node(session, exploit_node_id, row):
        session.run("""
            MERGE (p:Platform {name: $platform})
            WITH p
            MATCH (e:Exploit) WHERE ID(e) = $exploit_node_id
            MERGE (e)-[:Afecta_a]->(p)
        """, exploit_node_id=exploit_node_id, **row)

    @staticmethod
    def _create_port_node(session, exploit_node_id, row):
        session.run("""
            MERGE (pt:Port {number: $port})
            WITH pt
            MATCH (e:Exploit) WHERE ID(e) = $exploit_node_id
            MERGE (e)-[:Usa_puerto]->(pt)
        """, exploit_node_id=exploit_node_id, **row)

    @staticmethod
    def _create_tag_nodes(session, exploit_node_id, row):
        for tag in row["tags"].split(","):
            session.run("""
                MERGE (t:Tag {name: $tag})
                WITH t
                MATCH (e:Exploit) WHERE ID(e) = $exploit_node_id
                MERGE (e)-[:Tiene_etiqueta]->(t)
            """, exploit_node_id=exploit_node_id, tag=tag)



