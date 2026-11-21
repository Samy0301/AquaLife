import streamlit as st
from db import repo_root

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

# selector y botón de ejecucion
col_sel, col_btn = st.columns([4, 1])
with col_sel:
    archivo = st.selectbox(
        "Selecciona una consulta",
        archivos_sql,
        format_func=lambda p: p.stem.replace("_", " ").capitalize(),
    )
with col_btn:
    st.write("")
    st.write("")
    st.button("🔄 Ejecutar", use_container_width=True)

sql_texto = archivo.read_text(encoding="utf-8-sig").strip()

if not sql_texto:
    st.warning(f"El archivo `{archivo.name}` está vacío.")
    st.stop()

tab_tabla, tab_sql = st.tabs(["📋 Resultados", "💻 Ver SQL"])

with tab_sql:
    st.code(sql_texto, language="sql")