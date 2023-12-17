from neo4j import GraphDatabase

class Neo4jDataLoader:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def create_nodes(self, df_cve, df_exploit, df_news):
        with self.driver.session() as session:
            # Crear nodos CVE
            cve_query = """
            UNWIND cve_data as row
            MERGE (c:CVE {name: row.Name})
            SET c.status = row.Status,
                c.description = row.Description,
                c.references = row.References,
                c.phase = row.Phase,
                c.votes = row.Votes,
                c.comments = row.Comments
            """
            cve_data = df_cve.to_dict(orient='records')
            session.run(cve_query, cve_data=cve_data)

            # Crear nodos Exploits
            exploit_query = """
            UNWIND exploit_data as row
            MERGE (e:Exploit {codes: row.codes})
            SET e.file = row.file,
                e.description = row.description,
                e.date_published = row.date_published,
                e.author = row.author,
                e.type = row.type,
                e.platform = row.platform,
                e.port = row.port,
                e.date_added = row.date_added,
                e.date_updated = row.date_updated,
                e.verified = row.verified,
                e.codes = row.codes,
                e.tags = row.tags,
                e.aliases = row.aliases,
                e.screenshot_url = row.screenshot_url,
                e.application_url = row.application_url,
                e.source_url = row.source_url
            """
            exploit_data = df_exploit.to_dict(orient='records')
            session.run(exploit_query, exploit_data=exploit_data)

            # Crear nodos Noticias
            news_query = """
            UNWIND news_data as row
            MERGE (n:News {title: row.title})
            SET n.url = row.url,
                n.text = row.text
            """
            news_data = df_news.to_dict(orient='records')
            session.run(news_query, news_data=news_data)

    def create_relationships(self):
        with self.driver.session() as session:
            cve_exploit_relation_query = """
                    MATCH (c:CVE), (e:Exploit)
                    WHERE c.name = e.codes
                    CREATE (c)-[:HAS_EXPLOIT]->(e)
                    """
            session.run(cve_exploit_relation_query)

            # Relaciones entre Exploits y News basadas en la presencia de códigos en el texto
            exploit_news_relation_query = """
                    MATCH (e:Exploit), (n:News)
                    WHERE n.text CONTAINS e.codes
                    CREATE (e)-[:MENTIONED_IN]->(n)
                    """
            session.run(exploit_news_relation_query)

            cve_news_relation_query = """
                    MATCH (c:CVE), (n:News)
                    WHERE n.text CONTAINS c.name
                    CREATE (c)-[:MENTIONED_IN]->(n)
                    """
            session.run(cve_news_relation_query)


