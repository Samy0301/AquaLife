import streamlit as st
from db import run_query, execute

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

st.subheader("✏️ Modificar precio")

opciones = {
    f"#{p['IDProd']} · {p['Nombre']}": p
    for p in productos
}

seleccion = st.selectbox(
    "Selecciona el producto que deseas modificar",
    options=list(opciones.keys())
)

elegido = opciones[seleccion]

id_prod = elegido["IDProd"]
nombre = elegido["Nombre"]
precio_actual = float(elegido["Precio"])

st.metric("Producto seleccionado", nombre)

st.metric(
    "Precio actual",
    f"${precio_actual:.2f}"
)

st.divider()

nuevo_precio = st.number_input(
    "Introduce el nuevo precio",
    min_value=0.01,
    value=precio_actual,
    step=0.50,
    format="%.2f"
)

if st.button("💾 Actualizar precio", type="primary"):

    if round(nuevo_precio, 2) == round(precio_actual, 2):
        st.info("El nuevo precio coincide con el precio actual.")

    else:
        SQL_ACTUALIZAR = """
        UPDATE Producto
        SET Precio = %s
        WHERE IDProd = %s;
        """

        filas = execute(
            SQL_ACTUALIZAR,
            (round(nuevo_precio, 2), id_prod)
        )

        if filas > 0:
            st.success(
                f"Precio de {nombre} actualizado correctamente: "
                f"${precio_actual:.2f} → ${nuevo_precio:.2f}"
            )

            st.info(
                "El trigger trg_auditoria_precio registró el cambio."
            )

            st.rerun()

        elif filas == 0:
            st.warning("No se modificó ninguna fila.")

        else:
            st.error("No se pudo actualizar el precio.")
