import streamlit as st
from db import ensure_db_objects, execute, run_query

st.set_page_config(
    page_title="Gestor de Precios · AquaLife",
    page_icon="💲",
    layout="wide"
)

ensure_db_objects()

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

st.subheader(f"📜 Historial de precios: {nombre}")

SQL_HISTORIAL = """
SELECT
    IDProd,
    PrecioAnterior,
    PrecioNuevo,
    PorcentajeCambio,
    FechaCambio,
    HoraCambio,
    Usuario
FROM Historial_Precios
WHERE IDProd = %s
ORDER BY IDHist DESC;
"""

historial = run_query(SQL_HISTORIAL, (id_prod,))

if historial:

    ultimo = historial[0]

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Precio anterior",
        f"${float(ultimo['PrecioAnterior']):.2f}"
    )

    c2.metric(
        "Precio nuevo",
        f"${float(ultimo['PrecioNuevo']):.2f}"
    )

    if ultimo["PorcentajeCambio"] is not None:
        c3.metric(
            "Variación",
            f"{float(ultimo['PorcentajeCambio']):+.2f}%"
        )
    else:
        c3.metric("Variación", "No calculable")

    st.dataframe(
        historial,
        hide_index=True
    )

else:
    st.info(
        "Este producto todavía no tiene cambios registrados en Historial_Precios."
    )

with st.expander("🌎 Consultar últimos 50 cambios globales"):

    SQL_HISTORIAL_GLOBAL = """
    SELECT
        h.IDHist,
        h.IDProd,
        p.Nombre,
        h.PrecioAnterior,
        h.PrecioNuevo,
        h.PorcentajeCambio,
        h.FechaCambio,
        h.HoraCambio,
        h.Usuario
    FROM Historial_Precios h
    INNER JOIN Producto p ON h.IDProd = p.IDProd
    ORDER BY h.IDHist DESC
    LIMIT 50;
    """

    historial_global = run_query(SQL_HISTORIAL_GLOBAL)

    if historial_global:
        st.dataframe(
            historial_global,
            hide_index=True
        )
    else:
        st.info("Todavía no existen registros de auditoría.")
