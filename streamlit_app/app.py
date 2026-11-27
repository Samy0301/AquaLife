import streamlit as st
from db import ensure_db_objects, get_mysql, get_mongo, get_neo4j

st.set_page_config(
    page_title="AquaLife · Panel de Control",
    page_icon="🐠",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
    .hero-box {
        background: linear-gradient(135deg, #0b4f6c 0%, #1481ba 60%, #17bebb 100%);
        padding: 2rem 2.2rem;
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
        margin-bottom: 0.75rem;
    }
    .hero-title {
        font-size: 2.1rem;
        font-weight: 700;
        margin: 0 0 0.4rem 0;
        line-height: 1.2;
    }
    .hero-subtitle {
        font-size: 1.02rem;
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
        font-size: 1.05rem;
    }
    .module-card p {
        margin: 0;
        font-size: 0.9rem;
        opacity: 0.88;
        line-height: 1.45;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# cabecera 
st.markdown(
    """
    <div class="hero-box">
        <div class="hero-badge">AQUASOLUTIONS · PANEL DIRECTIVO Y OPERATIVO</div>
        <div class="hero-title">🐠 AquaLife — Centro de Analítica y Gestión</div>
        <p class="hero-subtitle">
            Plataforma integral de monitoreo para la comunidad global de acuarismo.
            Supervisa la actividad de usuarios, el rendimiento de vendedores, la trazabilidad
            de precios, las conversaciones técnicas y la documentación especializada de especies.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# estado de los motores de datos 
st.subheader("🔌 Estado de la infraestructura de datos")

mysql_ok = get_mysql() is not None
mongo_ok = get_mongo() is not None
neo4j_ok = get_neo4j() is not None


if mysql_ok:
    ensure_db_objects()

c1, c2, c3 = st.columns(3)

with c1:
    if mysql_ok:
        st.success("✅ **MySQL** · Conectado")    
    else:
        st.error("❌ **MySQL** · Sin conexión")
    st.caption("Núcleo transaccional, analítica SQL, `sp_analisis_usuario` y auditoría de precios.")

with c2:
    if mongo_ok:
        st.success("✅ **MongoDB** · Conectado")
    else:
        st.error("❌ **MongoDB** · Sin conexión")
    st.caption("Repositorio documental jerárquico de especies (fichas, certificados y guías).")

with c3:
    if neo4j_ok:
        st.success("✅ **Neo4j** · Conectado")
    else:
        st.error("❌ **Neo4j** · Sin conexión")
    st.caption("Modelo de grafos para hilos de conversación y respuestas anidadas.")

st.divider()

# módulos disponibles en el panel 
st.subheader("🧭 Módulos del Panel de Control")
st.markdown("Selecciona una herramienta en el **menú lateral** para comenzar:")

r1_c1, r1_c2, r1_c3 = st.columns(3)

with r1_c1:
    st.markdown(
        """
        <div class="module-card">
            <h4>📊 Selector de Consultas Analíticas</h4>
            <p>
                Explora métricas clave de la comunidad: termómetro de reacciones,
                perfil demográfico, tendencias por tipo de agua, ranking de vendedores,
                análisis de <em>influencers</em> y detección de anomalías.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with r1_c2:
    st.markdown(
        """
        <div class="module-card">
            <h4>👤 Análisis de Actividad de Usuario</h4>
            <p>
                Consulta el perfil detallado de cualquier acuarista por rango de fechas
                mediante el procedimiento almacenado <code>sp_analisis_usuario</code>:
                publicaciones, reacciones, compras y especies favoritas.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with r1_c3:
    st.markdown(
        """
        <div class="module-card">
            <h4>💬 Gestión de Conversaciones</h4>
            <p>
                Navega por hilos de diagnóstico y dudas técnicas de la comunidad y publica
                nuevas respuestas manteniendo la trazabilidad jerárquica entre comentarios.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.write("")  # espacio entre filas

r2_c1, r2_c2 = st.columns(2)

with r2_c1:
    st.markdown(
        """
        <div class="module-card">
            <h4>📚 Explorador de Documentos de Especies</h4>
            <p>
                Consulta la Ficha de Especie y toda su documentación secundaria asociada
                (certificados sanitarios, guías de alimentación, tratamientos, historial
                de crecimiento y parámetros de agua).
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with r2_c2:
    st.markdown(
        """
        <div class="module-card">
            <h4>💲 Gestor y Auditoría de Precios</h4>
            <p>
                Administra los precios de especies y equipos del catálogo y verifica
                en tiempo real el registro automático generado por el <em>trigger</em>
                en la tabla <code>Historial_Precios</code>.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()


with st.sidebar:
    st.markdown("### 🐠 AquaLife")
    st.caption("Sistema de soporte a decisiones · AquaSolutions (2026-2027)")

st.caption("AquaSolutions · Departamento de Analítica de Datos · Bases de Datos 2026-2027")