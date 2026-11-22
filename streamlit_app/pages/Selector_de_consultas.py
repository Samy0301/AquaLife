import streamlit as st
from db import repo_root, _get_live_connection
import re
import pandas as pd

st.set_page_config(
    page_title="Selector de Consultas · AquaLife",
    page_icon="📊",
    layout="wide",
)

st.markdown(
    """
    <style>
    .page-header {
        background: linear-gradient(135deg, #0b4f6c 0%, #1481ba 65%, #17bebb 100%);
        padding: 1.5rem 2rem;
        border-radius: 14px;
        color: #ffffff;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    .page-header h2 { margin: 0 0 0.3rem 0; font-size: 1.7rem; }
    .page-header p { margin: 0; opacity: 0.92; font-size: 0.95rem; }
    </style>
    <div class="page-header">
        <h2>📊 Selector de Consultas SQL</h2>
        <p>Explora y ejecuta las consultas analíticas de AquaLife directamente sobre MySQL.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

dir_queri = repo_root / "sql" / "queries"

archivos_sql = sorted(dir_queri.glob("*.sql"))

if not archivos_sql:
    st.warning(f"No hay archivos `.sql` dentro de `{dir_queri}`.")
    st.stop()

# selector 
archivo = st.selectbox(
    "Selecciona una consulta",
    archivos_sql,
    format_func=lambda p: p.stem.replace("_", " ").capitalize(),
)

sql_texto = archivo.read_text(encoding="utf-8-sig").strip()

if not sql_texto:
    st.warning(f"El archivo `{archivo.name}` está vacío.")
    st.stop()

tab_tabla, tab_sql = st.tabs(["📋 Resultados", "💻 Ver SQL"])

with tab_sql:
    st.code(sql_texto, language="sql")


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

    # filtrar bloques que solo tengan comentarios 
    resultado = []
    for s in sentencias:
        sin_bloque = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
        sin_coment = re.sub(r"(?m)(--.*$|#.*$)", "", sin_bloque)
        if sin_coment.strip():
            resultado.append(s)
    return resultado

def ejecutar_script_sql(sql_texto: str) -> list[list[dict]]:
    conn = _get_live_connection()
    if conn is None:
        return []

    conn.commit()  # refrescar snapshot de lectura
    resultados = []
    cur = conn.cursor(dictionary=True)
    try:
        for stmt in dividir_sentencias_sql(sql_texto):
            cur.execute(stmt)
            if cur.description is not None:
                resultados.append(cur.fetchall())
    finally:
        cur.close()
    return resultados

tablas_resultado = []
try:
    with st.spinner(f"Ejecutando `{archivo.name}`..."):
        tablas_resultado = ejecutar_script_sql(sql_texto)
except Exception as e:
    st.error(f"Error al ejecutar `{archivo.name}`: {e}")
    st.stop()

with tab_tabla:
    if not tablas_resultado:
        st.info("La consulta se ejecutó correctamente, pero no devolvió registros.")
    else:
        for idx, filas in enumerate(tablas_resultado, start=1):
            if len(tablas_resultado) > 1:
                st.subheader(f"Resultado #{idx}")

    
            df = pd.DataFrame(filas)
            
            csv = df.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                label=f"⬇️ Descargar CSV{f' (#{idx})' if len(tablas_resultado) > 1 else ''}",
                data=csv,
                file_name=f"{archivo.stem}{f'_{idx}' if len(tablas_resultado) > 1 else ''}.csv",
                mime="text/csv",
                key=f"dl_{archivo.stem}_{idx}",
            )
            st.dataframe(df, hide_index=True)