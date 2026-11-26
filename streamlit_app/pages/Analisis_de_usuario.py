from datetime import date
import pandas as pd
import streamlit as st

from db import call_procedure, run_query

st.set_page_config(
    page_title="AquaLife · Análisis de Usuario",
    page_icon="👤",
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

# Cargar usuarios disponibles 
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

if enviar:
    if f_ini > f_fin:
        st.error("La fecha inicial no puede ser posterior a la fecha final.")
    else:
        resultados = call_procedure("sp_analisis_usuario", (int(user_id), f_ini, f_fin))

        if not resultados:
            st.warning(
                "No se obtuvieron datos del procedimiento almacenado. "
                "Verifica la conexión a MySQL y que `sp_analisis_usuario` esté creado."
            )
        else:
            row = resultados[0]
            nombre = row.get("nombre")

            if nombre is None:
                st.warning(
                    f"No existe ningún usuario registrado con el ID **{int(user_id)}**."
                )
            else:
                publicaciones = int(row.get("publicaciones") or 0)
                reacciones_dadas = int(row.get("reacciones_dadas") or 0)
                reacciones_recibidas = int(row.get("reacciones_recibidas") or 0)
                comentarios = int(row.get("comentarios") or 0)
                compras = int(row.get("compras") or 0)
                monto_gastado = float(row.get("monto_gastado") or 0.0)
                contribuciones = int(row.get("contribuciones") or 0)
                esp_comprada = row.get("especie_mas_comprada")
                esp_contribuida = row.get("especie_mas_contribuida")

                st.divider()

                # Encabezado del perfil consultado
                st.markdown(
                    f"""
                    <div class="module-card">
                        <h4>🪪 Perfil analizado: {nombre} (ID #{int(user_id)})</h4>
                        <p>Período consultado: del <strong>{f_ini.strftime('%d/%m/%Y')}</strong>
                        al <strong>{f_fin.strftime('%d/%m/%Y')}</strong></p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.write("")

                # Métricas de interacción social
                st.subheader("💬 Actividad en la comunidad")
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("📝 Publicaciones", f"{publicaciones:,}")
                m2.metric("👍 Reacciones dadas", f"{reacciones_dadas:,}")
                ratio_reacc = (
                    f"{reacciones_recibidas / publicaciones:.1f} / pub."
                    if publicaciones > 0
                    else "Sin publicaciones"
                )
                m3.metric(
                    "❤️ Reacciones recibidas",
                    f"{reacciones_recibidas:,}",
                    delta=ratio_reacc,
                    delta_color="off",
                )
                m4.metric("💭 Comentarios", f"{comentarios:,}")

                st.write("")

                # Métricas de contribuciones y compras
                st.subheader("🛒 Contribuciones y actividad comercial")
                k1, k2, k3 = st.columns(3)
                k1.metric("📘 Contribuciones (bitácoras)", f"{contribuciones:,}")
                k2.metric("🛍️ Compras realizadas", f"{compras:,}")
                ticket_prom = (
                    f"Prom. ${monto_gastado / compras:,.2f} / compra"
                    if compras > 0
                    else "Sin compras"
                )
                k3.metric(
                    "💲 Monto gastado",
                    f"${monto_gastado:,.2f}",
                    delta=ticket_prom,
                    delta_color="off",
                )

                st.write("")

                # Especies destacadas
                e1, e2 = st.columns(2)
                with e1:
                    st.markdown(
                        f"""
                        <div class="module-card">
                            <h4>🐠 Especie más comprada</h4>
                            <div class="highlight-value">
                                {esp_comprada if esp_comprada else "Sin compras en el período"}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                with e2:
                    st.markdown(
                        f"""
                        <div class="module-card">
                            <h4>🌿 Especie más contribuida</h4>
                            <div class="highlight-value">
                                {esp_contribuida if esp_contribuida else "Sin contribuciones en el período"}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                st.divider()

                # Gráfico y tabla resumen
                g_col, t_col = st.columns([3, 2])

                actividad_df = pd.DataFrame(
                    {
                        "Indicador": [
                            "Publicaciones",
                            "Reacciones dadas",
                            "Reacciones recibidas",
                            "Comentarios",
                            "Contribuciones",
                            "Compras",
                        ],
                        "Cantidad": [
                            publicaciones,
                            reacciones_dadas,
                            reacciones_recibidas,
                            comentarios,
                            contribuciones,
                            compras,
                        ],
                    }
                )

                with g_col:
                    st.subheader("📊 Distribución de actividad")
                    st.bar_chart(
                        actividad_df.set_index("Indicador"),
                        width="stretch",
                        color="#1481ba",
                    )

                with t_col:
                    st.subheader("📋 Resumen del perfil")
                    resumen_df = pd.DataFrame(
                        [
                            {"Métrica": "Nombre", "Valor": nombre},
                            {"Métrica": "Publicaciones", "Valor": str(publicaciones)},
                            {"Métrica": "Reacciones dadas", "Valor": str(reacciones_dadas)},
                            {"Métrica": "Reacciones recibidas", "Valor": str(reacciones_recibidas)},
                            {"Métrica": "Comentarios realizados", "Valor": str(comentarios)},
                            {"Métrica": "Contribuciones", "Valor": str(contribuciones)},
                            {"Métrica": "Compras realizadas", "Valor": str(compras)},
                            {"Métrica": "Monto gastado", "Valor": f"${monto_gastado:,.2f}"},
                            {
                                "Métrica": "Especie más comprada",
                                "Valor": esp_comprada or "—",
                            },
                            {
                                "Métrica": "Especie más contribuida",
                                "Valor": esp_contribuida or "—",
                            },
                        ]
                    )
                    st.dataframe(resumen_df, hide_index=True, width="stretch")

                with st.expander("🔎 Ver resultado directo de `sp_analisis_usuario`"):
                    st.dataframe(pd.DataFrame(resultados), hide_index=True, width="stretch")

st.divider()
st.caption("AquaSolutions · Departamento de Analítica de Datos · Bases de Datos 2026-2027")