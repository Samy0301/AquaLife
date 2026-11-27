import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from db import get_mongo, repo_root


def cargar_tarea5():
    """Carga explícitamente nosql/mongo/tarea5.py desde su ruta en el repositorio."""
    mod_name = "nosql_mongo_tarea5"
    if mod_name in sys.modules:
        return sys.modules[mod_name]

    candidatos = [
        repo_root / "nosql" / "mongo" / "tarea5.py",
        Path.cwd() / "nosql" / "mongo" / "tarea5.py",
        *[p / "nosql" / "mongo" / "tarea5.py" for p in Path(__file__).resolve().parents],
    ]
    ruta = next((p for p in candidatos if p.is_file()), None)
    if ruta is None:
        return None

    spec = importlib.util.spec_from_file_location(mod_name, ruta)
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = modulo
    spec.loader.exec_module(modulo)
    return modulo


st.set_page_config(
    page_title="AquaLife · Explorador de Documentos",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilos 
st.markdown(
    """
    <style>
    .hero-box {
        background: linear-gradient(135deg, #0b4f6c 0%, #1481ba 60%, #17bebb 100%);
        padding: 1.75rem 2rem;
        border-radius: 14px;
        color: #ffffff;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.12);
    }
    .hero-badge {
        display: inline-block;
        background: rgba(255, 255, 255, 0.18);
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        margin-bottom: 0.65rem;
    }
    .hero-title {
        font-size: 1.9rem;
        font-weight: 700;
        margin: 0 0 0.35rem 0;
        line-height: 1.2;
    }
    .hero-subtitle {
        font-size: 0.98rem;
        opacity: 0.94;
        margin: 0;
        max-width: 820px;
        line-height: 1.5;
    }
    .module-card {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 12px;
        padding: 1.15rem 1.25rem;
        height: 100%;
    }
    .module-card h4 {
        margin: 0 0 0.45rem 0;
        font-size: 1rem;
    }
    .module-card p {
        margin: 0;
        font-size: 0.92rem;
        opacity: 0.9;
        line-height: 1.45;
    }
    .doc-badge {
        display: inline-block;
        padding: 0.15rem 0.55rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
        background: rgba(20, 129, 186, 0.15);
        color: #1481ba;
        margin-right: 0.4rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def fmt_fecha(valor) -> str:
    if isinstance(valor, datetime):
        return valor.strftime("%d/%m/%Y")
    return str(valor) if valor is not None else "—"


# Cabecera
st.markdown(
    """
    <div class="hero-box">
        <div class="hero-badge">REPOSITORIO DOCUMENTAL · MONGODB (TAREA 5)</div>
        <div class="hero-title">📚 Explorador de Documentos de Especies</div>
        <p class="hero-subtitle">
            Consulta de forma organizada y jerárquica la Ficha de Especie y toda su
            documentación secundaria asociada (certificados sanitarios, guías de
            alimentación, manuales de enfermedades, historial de crecimiento y análisis de agua).
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### 🐠 AquaLife")
    st.caption("Sistema de soporte a decisiones · AquaSolutions (2026-2027)")

tarea5 = cargar_tarea5()
if tarea5 is None:
    st.error("No se encontró el archivo `nosql/mongo/tarea5.py` en el repositorio.")
    st.stop()

mongo_default = get_mongo()
if mongo_default is None:
    st.error("No hay conexión disponible con MongoDB.")
    st.stop()

# Usar la BD definida en nosql/mongo/tarea5.py (aqualife_docs)
db_docs = mongo_default.client[tarea5.BASE_DATOS]
if db_docs[tarea5.COLECCION_FICHAS].count_documents({}, limit=1) == 0:
    if mongo_default[tarea5.COLECCION_FICHAS].count_documents({}, limit=1) > 0:
        db_docs = mongo_default

fichas_col = db_docs[tarea5.COLECCION_FICHAS]
secundarios_col = db_docs[tarea5.COLECCION_SECUNDARIOS]

# Si todavía no se ejecutó insertar() de tarea5.py, hacerlo automáticamente al cargar
if fichas_col.count_documents({}, limit=1) == 0:
    with st.spinner("Generando fichas y documentos secundarios en MongoDB..."):
        try:
            tarea5.insertar(fichas_col, secundarios_col)
            if fichas_col.count_documents({}, limit=1) == 0:
                st.error("No se insertaron fichas. Revisa la conexión con las fuentes de datos.")
                st.stop()
            st.success("Fichas y documentos generados correctamente. Recargando...")
            st.rerun()
        except Exception as e:
            st.error(f"Error al ejecutar insertar() de nosql/mongo/tarea5.py: {e}")
            st.stop()

# Traer catálogo resumido de especies desde mongo para el selector
lista_fichas = list(
    fichas_col.find(
        {},
        {
            "_id": 0,
            "IDProd": 1,
            "nombreComun": 1,
            "nombreCientifico": 1,
            "categoria": 1,
            "tipoAgua": 1,
        },
    ).sort("IDProd", 1)
)

# Filtros y selector de especie
f_col1, f_col2, f_col3 = st.columns([1, 1, 2])
categorias = ["Todas"] + sorted({d.get("categoria", "Sin categoría") for d in lista_fichas})
tipos_agua = ["Todos"] + sorted({d.get("tipoAgua", "Sin definir") for d in lista_fichas})

cat_sel = f_col1.selectbox("Filtrar por categoría", categorias)
agua_sel = f_col2.selectbox("Filtrar por tipo de agua", tipos_agua)

filtradas = [
    d
    for d in lista_fichas
    if (cat_sel == "Todas" or d.get("categoria") == cat_sel)
    and (agua_sel == "Todos" or d.get("tipoAgua") == agua_sel)
]

if not filtradas:
    st.info("No hay especies que coincidan con los filtros seleccionados.")
    st.stop()

opciones = {
    d["IDProd"]: f"#{d['IDProd']} · {d.get('nombreComun', 'Sin nombre')} ({d.get('nombreCientifico', '')})"
    for d in filtradas
}
especie_id = f_col3.selectbox(
    "Selecciona una especie",
    options=list(opciones.keys()),
    format_func=lambda eid: opciones[eid],
)

ficha_completa = tarea5.obtener_documentos_especie(db_docs, int(especie_id))

if ficha_completa is None:
    st.warning(f"No se encontró ninguna ficha en MongoDB para `IDProd = {especie_id}`.")
    st.stop()

st.divider()

# ficha de especie
st.subheader("📄 Nivel 1 · Ficha Principal de la Especie")

st.markdown(
    f"""
    <div class="module-card">
        <span class="doc-badge">IDProd #{ficha_completa.get('IDProd')}</span>
        <span class="doc-badge">{ficha_completa.get('categoria', '—')}</span>
        <span class="doc-badge">{ficha_completa.get('tipoAgua', '—')}</span>
        <span class="doc-badge">Nivel: {ficha_completa.get('nivelCuidado', '—')}</span>
        <h4 style="margin-top:0.6rem; font-size:1.25rem;">
            🐠 {ficha_completa.get('nombreComun', 'Sin nombre común')}
            <em style="font-weight:400; opacity:0.8;">({ficha_completa.get('nombreCientifico', '—')})</em>
        </h4>
        <p>
            <strong>Temporada:</strong> {ficha_completa.get('temporada', '—')} ·
            <strong>Temperamento:</strong> {ficha_completa.get('temperamento', '—')} ·
            <strong>Actualizado:</strong> {fmt_fecha(ficha_completa.get('actualizadoEn'))}
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("")

# métricas de mantenimiento
k1, k2, k3, k4 = st.columns(4)
k1.metric("🪣 Litros mínimos", f"{ficha_completa.get('litrosMinimosTanque', '—')} L")
k2.metric("☀️ Horas de luz", f"{ficha_completa.get('horasLuz', '—')} h/día")
k3.metric("📏 Tamaño máximo", f"{ficha_completa.get('tamanoMaximoCm', '—')} cm")
k4.metric("⏳ Esperanza de vida", f"{ficha_completa.get('esperanzaVidaAnios', '—')} años")

st.write("")

# parámetros de agua y cuidados generales
p_col, c_col = st.columns(2)
params = ficha_completa.get("parametrosAgua", {})

with p_col:
    salinidad = params.get("salinidadPpt")
    sal_txt = f"{salinidad} ppt" if salinidad is not None else "No aplica (agua dulce)"
    st.markdown(
        f"""
        <div class="module-card">
            <h4>💧 Parámetros de Agua Requeridos</h4>
            <p>
                • <strong>pH:</strong> {params.get('pHMin', '—')} – {params.get('pHMax', '—')}<br>
                • <strong>Temperatura:</strong> {params.get('temperaturaMinC', '—')} °C – {params.get('temperaturaMaxC', '—')} °C<br>
                • <strong>Dureza GH:</strong> {params.get('durezaGH', '—')}<br>
                • <strong>Salinidad:</strong> {sal_txt}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c_col:
    st.markdown(
        f"""
        <div class="module-card">
            <h4>🌱 Cuidados y Biología</h4>
            <p>
                • <strong>Cuidados específicos:</strong> {ficha_completa.get('cuidadosEspecificos', '—')}<br>
                • <strong>Tipo de sustrato:</strong> {ficha_completa.get('tipoSustrato', '—')}<br>
                • <strong>Dieta:</strong> {ficha_completa.get('dieta', '—')}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

# documentos secundarios
total_sec = ficha_completa.get("totalDocumentosSecundarios", 0)
resumen = ficha_completa.get("resumenSecundarios", {})
docs_sec = ficha_completa.get("documentosSecundarios", [])

st.subheader(f"🗂️ Nivel 2 · Documentos Secundarios Asociados ({total_sec})")

if resumen:
    resumen_df = pd.DataFrame(
        [{"Tipo de documento": k, "Cantidad": v} for k, v in resumen.items()]
    )
    st.dataframe(resumen_df, hide_index=True)

tipos_disponibles = ["Todos"] + list(resumen.keys())
tipo_filtro = st.selectbox("Filtrar documentos secundarios por tipo", tipos_disponibles)

docs_filtrados = [
    d for d in docs_sec if tipo_filtro == "Todos" or d.get("tipo") == tipo_filtro
]

iconos_tipo = {
    "Certificado Sanitario": "🩺",
    "Guía de Alimentación Estacional": "🍽️",
    "Manual de Tratamiento de Enfermedades": "💊",
    "Historial de Crecimiento": "📈",
    "Análisis de Agua": "🧪",
}

for idx, doc in enumerate(docs_filtrados, start=1):
    tipo = doc.get("tipo", "Documento")
    alm = doc.get("almacenamiento", "—")
    icono = iconos_tipo.get(tipo, "📎")
    fecha_doc = doc.get("fecha") or doc.get("fechaEmision")
    titulo_exp = f"{icono} {tipo} · [{alm}]" + (
        f" · {fmt_fecha(fecha_doc)}" if fecha_doc else ""
    )

    with st.expander(titulo_exp, expanded=(idx <= 3)):
        st.caption(f"Modo de almacenamiento en MongoDB: **{alm}**")

        if tipo == "Certificado Sanitario":
            c1, c2, c3 = st.columns(3)
            c1.write(f"**N.º Certificado:** {doc.get('numeroCertificado', '—')}")
            c2.write(f"**Emitido por:** {doc.get('emitidoPor', '—')}")
            c3.write(f"**Resultado:** `{doc.get('resultado', '—')}`")
            st.write(
                f"**Vigencia:** {fmt_fecha(doc.get('fechaEmision'))} → {fmt_fecha(doc.get('fechaVencimiento'))}"
            )
            st.write(f"**Observaciones:** {doc.get('observaciones', '—')}")

        elif tipo == "Guía de Alimentación Estacional":
            c1, c2 = st.columns(2)
            c1.write(f"**Temporada:** {doc.get('temporada', '—')}")
            c2.write(f"**Frecuencia diaria:** {doc.get('frecuenciaDiaria', '—')} veces/día")
            alimentos = doc.get("alimentos", [])
            st.write("**Alimentos recomendados:** " + (", ".join(alimentos) if alimentos else "—"))
            st.write(f"**Notas:** {doc.get('notas', '—')}")

        elif tipo == "Manual de Tratamiento de Enfermedades":
            enfermedades = doc.get("enfermedades", [])
            if not enfermedades:
                st.info("No hay enfermedades registradas en este manual.")
            else:
                enf_df = pd.DataFrame(enfermedades)
                st.dataframe(enf_df, hide_index=True)

        else:
            # documentos referenciados (historial de crecimiento / análisis de agua)
            campos_ocultos = {"IDProd", "tipo", "almacenamiento"}
            campos_visibles = {
                k: (fmt_fecha(v) if isinstance(v, datetime) else v)
                for k, v in doc.items()
                if k not in campos_ocultos
            }
            cols = st.columns(max(1, len(campos_visibles)))
            for col, (clave, valor) in zip(cols, campos_visibles.items()):
                col.metric(clave.capitalize(), str(valor))

st.divider()

with st.expander("🌳 Nivel 3 · Ver estructura documental jerárquica completa (JSON)"):
    json_seguro = json.loads(json.dumps(ficha_completa, default=str))
    st.json(json_seguro, expanded=False)

st.divider()
st.caption("AquaSolutions · Departamento de Analítica de Datos · Bases de Datos 2026-2027")