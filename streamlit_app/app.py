import streamlit as st
from db import get_mysql, get_mongo, get_neo4j

st.set_page_config(page_title="AquaLife · Panel de Control", page_icon="🐠", layout="wide")
st.title("🐠 AquaLife — Panel de Control")

st.caption("AquaSolutions · Bases de Datos 2026-2027")
st.divider()

st.subheader("Estado de conexión de las bases de datos")

c1, c2, c3 = st.columns(3)

c1.success("✅ MySQL conectado") if get_mysql() is not None else c1.error("❌ MySQL")
c2.success("✅ MongoDB conectado") if get_mongo() is not None else c2.error("❌ MongoDB")
c3.success("✅ Neo4j conectado") if get_neo4j() is not None else c3.error("❌ Neo4j")

st.divider()
st.markdown("Use el menú lateral para navegar entre las funcionalidades del panel.")