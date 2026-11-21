import streamlit as st
from db import run_query

st.set_page_config(
    page_title="Gestor de Precios · AquaLife",
    page_icon="💲",
    layout="wide"
)

st.title("💲 Gestor y Auditoría de Precios")

st.caption(
    "Administra los precios del catálogo y consulta "
    "el historial de modificaciones."
)

st.subheader("📦 Catálogo de productos")

busqueda = st.text_input("Buscar producto por nombre o ID")

SQL_LISTAR_PRODUCTOS = """
SELECT
    IDProd,
    Nombre,
    Descripcion,
    Precio
FROM Producto
WHERE
    Nombre LIKE CONCAT('%', %s, '%')
    OR CAST(IDProd AS CHAR) LIKE CONCAT('%', %s, '%')
ORDER BY IDProd;
"""

productos = run_query(
    SQL_LISTAR_PRODUCTOS, 
    (busqueda, busqueda)
    )

if not productos:
    st.warning("No se encontraron productos.")
    st.stop()

st.caption(f"Productos encontrados: {len(productos)}")

st.dataframe(
    productos,
    width="stretch",
    hide_index=True
)

st.divider()


