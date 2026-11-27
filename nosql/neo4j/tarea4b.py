import sys

import mysql.connector
from neo4j import GraphDatabase

try:
    from streamlit_app.db import NEO4J_URI, NEO4J_USER ,NEO4J_PASSWORD , MYSQL_CONFIG
except ModuleNotFoundError:
    from streamlit_app.db import NEO4J_URI, NEO4J_USER ,NEO4J_PASSWORD , MYSQL_CONFIG

TABLA ="Comentar"

def cargar():
    #Copia los comentarios de MySQL a Neo4j conservando los mismos IDC.
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cur = conn.cursor(dictionary=True)
    cur.execute(f"SELECT IDC, IDC_Padre, IDU, IDPub, comentario FROM {TABLA} ORDER BY IDC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    with GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)) as driver, driver.session() as s:
        s.run("CREATE CONSTRAINT comentario_idc IF NOT EXISTS FOR (c:Comentario) REQUIRE c.IDC IS UNIQUE")
        s.run("CREATE CONSTRAINT usuario_idu IF NOT EXISTS FOR (u:Usuario) REQUIRE u.IDU IS UNIQUE")
        s.run("CREATE CONSTRAINT publicacion_id IF NOT EXISTS FOR (p:Publicacion) REQUIRE p.IDPub IS UNIQUE")

        # Pasada 1: nodos y relaciones con usuario y publicación
        s.run("""
            UNWIND $rows AS r
            MERGE (c:Comentario {IDC: r.IDC})
            SET c.comentario = r.comentario
            MERGE (u:Usuario {IDU: r.IDU})
            MERGE (p:Publicacion {IDPub: r.IDPub})
            MERGE (u)-[:ESCRIBIO]->(c)
            MERGE (c)-[:EN]->(p)
        """, rows=rows)

        # Pasada 2: relaciones de respuesta (ya existen todos los nodos)
        s.run("""
            UNWIND $rows AS r
            WITH r WHERE r.IDC_Padre IS NOT NULL
            MATCH (c:Comentario {IDC: r.IDC})
            MATCH (padre:Comentario {IDC: r.IDC_Padre})
            MATCH (c)-[:EN]->(p:Publicacion)<-[:EN]-(padre)
            MERGE (c)-[:RESPONDE_A]->(padre)
        """, rows=rows)
    
# Obtener un hilo interno mediante un IDC (Lista de dicts)

def obtener_hilo(idc):
    # Obtener un hilo interno mediante un IDC (Lista de dicts)
    query = """
        MATCH path = (c:Comentario)-[:RESPONDE_A*0..]->(raiz:Comentario {IDC: $idc})
        OPTIONAL MATCH (c)-[:RESPONDE_A]->(padre:Comentario)
        MATCH (u:Usuario)-[:ESCRIBIO]->(c)
        RETURN c.IDC AS IDC, padre.IDC AS IDC_Padre, u.IDU AS IDU,
            c.comentario AS comentario, length(path) AS Nivel
        ORDER BY Nivel, IDC
    """
    with GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)) as driver, driver.session() as s:
        return [dict(r) for r in s.run(query, idc=idc)]


