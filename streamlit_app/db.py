from pathlib import Path
import mysql.connector
from mysql.connector import Error
import pymongo
from neo4j import GraphDatabase
import streamlit as st

# Raíz del repo (streamlit_app/db.py → parents[1])
REPO_ROOT = Path(__file__).resolve().parents[1]

MYSQL_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "root",
    "database": "AquaLife",
}

MONGO_URI = "mongodb://admin:password@localhost:27017/?authSource=admin"
MONGO_DATABASE = "AquaLife"

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"


@st.cache_resource
def get_mysql():
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        return conn
    except Error as e:
        st.error(f"MySQL: {e}")
        return None


@st.cache_resource
def get_mongo():
    """Devuelve el objeto Database o None. Verifica con ping real."""
    try:
        client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
        client.admin.command("ping")          # fuerza la conexión ahora
        return client[MONGO_DATABASE]
    except Exception as e:
        st.error(f"MongoDB: {e}")
        return None


@st.cache_resource
def get_neo4j():
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        driver.verify_connectivity()
        return driver
    except Exception as e:
        st.error(f"Neo4j: {e}")
        return None


def load_sql(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def _get_live_connection():
    """Devuelve una conexión MySQL viva, reconectando si es necesario."""
    conn = get_mysql()
    if conn is None:
        return None
    try:
        if not conn.is_connected():
            conn.reconnect(attempts=3, delay=1)
    except Error as e:
        st.error(f"MySQL (reconexión): {e}")
        return None
    return conn


def run_query(sql: str, params=None) -> list:
    conn = _get_live_connection()
    if conn is None:
        return []
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params or ())
        rows = cur.fetchall()
        cur.close()
        return rows
    except Error as e:
        st.error(f"Error en consulta: {e}")
        return []


def execute(sql: str, params=None) -> int:
    conn = _get_live_connection()
    if conn is None:
        return -1
    try:
        cur = conn.cursor()
        cur.execute(sql, params or ())
        conn.commit()
        n = cur.rowcount
        cur.close()
        return n
    except Error as e:
        conn.rollback()
        st.error(f"Error en operación: {e}")
        return -1


def call_procedure(name: str, params: tuple) -> list:
    conn = _get_live_connection()
    if conn is None:
        return []
    try:
        cur = conn.cursor(dictionary=True)
        cur.callproc(name, params)
        out = []
        for res in cur.stored_results():
            out.extend(res.fetchall())
        cur.close()
        return out
    except Error as e:
        st.error(f"Error en {name}: {e}")
        return []