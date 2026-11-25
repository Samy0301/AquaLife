import streamlit as st
from datetime import date
from db import run_query


st.set_page_config(
    page_title="AquaLife · Análisis de Usuario",
    page_icon="👤",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilos coherentes con app.py
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
        font-size: 0.95rem;
        opacity: 0.9;
        line-height: 1.45;
    }
    .highlight-value {
        font-size: 1.25rem;
        font-weight: 700;
        color: #1481ba;
        margin-top: 0.2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Cabecera
st.markdown(
    """
    <div class="hero-box">
        <div class="hero-badge">PROCEDIMIENTO ALMACENADO · sp_analisis_usuario</div>
        <div class="hero-title">👤 Análisis de Actividad de Usuario</div>
        <p class="hero-subtitle">
            Consulta de un vistazo el perfil de participación y compras de cualquier
            acuarista de AquaLife en un rango de fechas determinado.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### 🐠 AquaLife")
    st.caption("Sistema de soporte a decisiones · AquaSolutions (2026-2027)")
    # Cargar usuarios disponibles mediante SQL explícito para facilitar la selección
usuarios = run_query("SELECT IDU, Nombre FROM Usuario ORDER BY IDU")

modo = "Ingresar ID manualmente"
if usuarios:
    modo = st.radio(
        "Selección del acuarista",
        options=["Elegir de la lista", "Ingresar ID manualmente"],
        horizontal=True,
    )

with st.form("form_analisis_usuario"):
    c1, c2, c3 = st.columns([2, 1, 1])

    if modo == "Elegir de la lista" and usuarios:
        opciones = {u["IDU"]: f"#{u['IDU']} · {u['Nombre']}" for u in usuarios}
        user_id = c1.selectbox(
            "Usuario",
            options=list(opciones.keys()),
            format_func=lambda uid: opciones[uid],
        )
    else:
        user_id = c1.number_input("ID de usuario (IDU)", min_value=1, step=1, value=1)

    f_ini = c2.date_input("Fecha inicial", value=date(2020, 1, 1))
    f_fin = c3.date_input("Fecha final", value=date.today())
    enviar = st.form_submit_button("🔍 Analizar actividad", type="primary")