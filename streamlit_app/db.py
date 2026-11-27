from pathlib import Path
import re

import mysql.connector
from mysql.connector import Error
import pymongo
from neo4j import GraphDatabase
import streamlit as st

# Raíz del repo (streamlit_app/db.py → parents[1])
repo_root = Path(__file__).resolve().parents[1]

# Objetos de BD que viven en sql/ y NO se generan dentro de init.sql.
PROCEDURE_SQL = "sql/procedures/3g_procedimiento_almacenado_para_análisis_de_actividad_de_usuario.sql"
TRIGGER_SQL = "sql/triggers/3f_auditoria_precios.sql"

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
    return (repo_root / rel_path).read_text(encoding="utf-8")


def _extract_create(sql_text: str, kind: str) -> str:
    """Saca el CREATE PROCEDURE/TRIGGER de un .sql que usa DELIMITER.
    """
    match = re.search(
        rf"CREATE\s+{kind}\b.*?\bEND\s*(//|\$\$|;)",
        sql_text,
        re.IGNORECASE | re.DOTALL,
    )
    if not match:
        raise ValueError(f"No se encontró un CREATE {kind} en el fichero SQL")
    return match.group(0)[: -len(match.group(1))].strip()


def _extract_create_table(sql_text: str, table: str) -> str:
    """Saca el CREATE TABLE IF NOT EXISTS de un fichero SQL."""
    match = re.search(
        rf"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+{re.escape(table)}\b.*?;",
        sql_text,
        re.IGNORECASE | re.DOTALL,
    )
    if not match:
        raise ValueError(f"No se encontró un CREATE TABLE {table} en el fichero SQL")
    return match.group(0).strip()


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


def _object_exists(
    conn, schema_view: str, schema_col: str, name_col: str, name: str, extra: str = ""
) -> bool:
    cur = conn.cursor()
    try:
        cur.execute(
            f"SELECT COUNT(*) FROM information_schema.{schema_view} "
            f"WHERE {schema_col} = DATABASE() AND {name_col} = %s{extra}",
            (name,),
        )
        return cur.fetchone()[0] > 0
    finally:
        cur.close()


def ensure_db_objects() -> bool:
    """Crea, si faltan, el procedure, la tabla de auditoría y el trigger.
    """
    conn = _get_live_connection()
    if conn is None:
        return False

    creados = []
    try:
        if not _object_exists(
            conn,
            "ROUTINES",
            "ROUTINE_SCHEMA",
            "ROUTINE_NAME",
            "sp_analisis_usuario",
            " AND ROUTINE_TYPE = 'PROCEDURE'",
        ):
            cur = conn.cursor()
            cur.execute(_extract_create(load_sql(PROCEDURE_SQL), "PROCEDURE"))
            cur.close()
            creados.append("sp_analisis_usuario")

        trigger_sql = load_sql(TRIGGER_SQL)
        if not _object_exists(
            conn, "TABLES", "TABLE_SCHEMA", "TABLE_NAME", "Historial_Precios"
        ):
            cur = conn.cursor()
            cur.execute(_extract_create_table(trigger_sql, "Historial_Precios"))
            cur.close()
            creados.append("Historial_Precios")

        if not _object_exists(
            conn, "TRIGGERS", "TRIGGER_SCHEMA", "TRIGGER_NAME", "trg_auditoria_precio"
        ):
            cur = conn.cursor()
            cur.execute(_extract_create(trigger_sql, "TRIGGER"))
            cur.close()
            creados.append("trg_auditoria_precio")

        if creados:
            conn.commit()
        return True
    except (Error, ValueError) as e:
        conn.rollback()
        st.error(f"No se pudieron crear los objetos de la BD: {e}")
        return False


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