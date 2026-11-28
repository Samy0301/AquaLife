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
    "buffered": True,
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
    """Devuelve una conexión MySQL viva, regenerándola si quedó en mal estado."""
    conn = get_mysql()
    if conn is None:
        return None
    try:
        if not conn.is_connected():
            conn.reconnect(attempts=3, delay=1)
        return conn
    except Error:
        # Si quedó un resultado sin leer o se rompió la sesión, cerramos y limpiamos la caché para abrir una conexión limpia.
        try:
            conn.close()
        except Exception:
            pass
        get_mysql.clear()
        return get_mysql()

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
    cur = None
    try:
        cur = conn.cursor(dictionary=True, buffered=True)
        cur.execute(sql, params or ())
        rows = cur.fetchall()
        conn.commit()
        return rows
    except Error as e:
        st.error(f"Error en consulta: {e}")
        return []
    finally:
        if cur is not None:
            cur.close()


def execute(sql: str, params=None) -> int:
    conn = _get_live_connection()
    if conn is None:
        return -1
    cur = None
    try:
        cur = conn.cursor(buffered=True)
        cur.execute(sql, params or ())
        conn.commit()
        return cur.rowcount
    except Error as e:
        conn.rollback()
        st.error(f"Error en operación: {e}")
        return -1
    finally:
        if cur is not None:
            cur.close()


def call_procedure(name: str, params: tuple) -> list:
    conn = _get_live_connection()
    if conn is None:
        return []
    cur = None
    try:
        cur = conn.cursor(dictionary=True, buffered=True)
        cur.callproc(name, params)
        out = []
        for res in cur.stored_results():
            out.extend(res.fetchall())
        conn.commit()
        return out
    except Error as e:
        st.error(f"Error en {name}: {e}")
        return []
    finally:
        if cur is not None:
            cur.close()

def dividir_sentencias_sql(sql: str) -> list[str]:
    sentencias = []
    actual = []
    en_simple = False
    en_doble = False
    en_linea = False
    en_bloque = False
    i = 0
    n = len(sql)

    while i < n:
        c = sql[i]
        sig = sql[i + 1] if i + 1 < n else ""

        if en_linea:
            actual.append(c)
            if c == "\n":
                en_linea = False
        elif en_bloque:
            actual.append(c)
            if c == "*" and sig == "/":
                actual.append(sig)
                en_bloque = False
                i += 1
        elif en_simple:
            actual.append(c)
            if c == "\\" and sig:
                actual.append(sig)
                i += 1
            elif c == "'":
                en_simple = False
        elif en_doble:
            actual.append(c)
            if c == "\\" and sig:
                actual.append(sig)
                i += 1
            elif c == '"':
                en_doble = False
        else:
            if (c == "-" and sig == "-") or c == "#":
                en_linea = True
                actual.append(c)
            elif c == "/" and sig == "*":
                en_bloque = True
                actual.append(c)
            elif c == "'":
                en_simple = True
                actual.append(c)
            elif c == '"':
                en_doble = True
                actual.append(c)
            elif c == ";":
                stmt = "".join(actual).strip()
                if stmt:
                    sentencias.append(stmt)
                actual = []
            else:
                actual.append(c)
        i += 1

    ultimo = "".join(actual).strip()
    if ultimo:
        sentencias.append(ultimo)

    resultado = []
    for s in sentencias:
        sin_bloque = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
        sin_coment = re.sub(r"(?m)(--.*$|#.*$)", "", sin_bloque)
        if sin_coment.strip():
            resultado.append(s)
    return resultado