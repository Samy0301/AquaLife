import html
import importlib.util
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

from db import (
    _get_live_connection,
    dividir_sentencias_sql,
    ensure_db_objects,
    execute,
    get_neo4j,
    repo_root,
    run_query,
)


def cargar_tarea4b():
    """Carga nosql/neo4j/tarea4b.py asegurando repo_root en sys.path."""
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    mod_name = "nosql_neo4j_tarea4b"
    if mod_name in sys.modules:
        return sys.modules[mod_name]

    candidatos = [
        repo_root / "nosql" / "neo4j" / "tarea4b.py",
        Path.cwd() / "nosql" / "neo4j" / "tarea4b.py",
        *[p / "nosql" / "neo4j" / "tarea4b.py" for p in Path(__file__).resolve().parents],
    ]
    ruta = next((p for p in candidatos if p.is_file()), None)
    if ruta is None:
        return None

    spec = importlib.util.spec_from_file_location(mod_name, ruta)
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = modulo
    spec.loader.exec_module(modulo)
    return modulo


def ejecutar_script_migracion(rel_path: str) -> None:
    ruta = repo_root / rel_path
    if not ruta.is_file():
        raise FileNotFoundError(f"No se encontró el archivo `{rel_path}`.")

    sql_texto = ruta.read_text(encoding="utf-8-sig")
    conn = _get_live_connection()
    if conn is None:
        raise RuntimeError("No hay conexión disponible con MySQL.")

    cur = conn.cursor()
    try:
        for stmt in dividir_sentencias_sql(sql_texto):
            if stmt.strip().upper().startswith("USE "):
                continue
            cur.execute(stmt)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


def ensure_conversaciones_db() -> None:
    cols = run_query("SHOW COLUMNS FROM Comentar")
    if not cols:
        return

    nombres_cols = {r["Field"] for r in cols}
    if not {"IDC", "IDC_Padre"}.issubset(nombres_cols):
        with st.spinner("Preparando tabla `Comentar` para hilos..."):
            ejecutar_script_migracion("sql/migrations/4a_modificacion_tabla_Comentar.sql")

    respuestas = run_query("SELECT COUNT(*) AS total FROM Comentar WHERE IDC_Padre IS NOT NULL")
    tiene_respuestas = bool(respuestas and respuestas[0]["total"] > 0)

    if not tiene_respuestas:
        existe_prueba = run_query(
            "SELECT 1 AS ok FROM Comentar WHERE comentario LIKE 'Mis barbos tigre%' LIMIT 1"
        )
        if not existe_prueba:
            try:
                with st.spinner("Cargando hilo de diagnóstico de prueba..."):
                    ejecutar_script_migracion("sql/migrations/4a_insertar_datos_prueba.sql")
            except Exception as e:
                st.warning(f"No se pudieron insertar los datos de prueba automáticamente: {e}")


def guardar_filas_en_neo4j(filas: list[dict]) -> None:
    if not filas:
        return
    driver = get_neo4j()
    if driver is None:
        return

    datos = [
        {
            "IDC": int(r["IDC"]),
            "IDC_Padre": int(r["IDC_Padre"]) if r.get("IDC_Padre") is not None else None,
            "IDU": int(r["IDU"]),
            "IDPub": int(r["IDPub"]),
            "comentario": str(r.get("comentario") or ""),
        }
        for r in filas
    ]

    with driver.session() as s:
        s.run(
            """
            UNWIND $rows AS r
            MERGE (c:Comentario {IDC: r.IDC})
            SET c.comentario = r.comentario
            MERGE (u:Usuario {IDU: r.IDU})
            MERGE (p:Publicacion {IDPub: r.IDPub})
            MERGE (u)-[:ESCRIBIO]->(c)
            MERGE (c)-[:EN]->(p)
            """,
            rows=datos,
        )
        con_padre = [d for d in datos if d["IDC_Padre"] is not None]
        if con_padre:
            s.run(
                """
                UNWIND $rows AS r
                MATCH (c:Comentario {IDC: r.IDC})
                MATCH (padre:Comentario {IDC: r.IDC_Padre})
                MATCH (c)-[:EN]->(p:Publicacion)<-[:EN]-(padre)
                MERGE (c)-[:RESPONDE_A]->(padre)
                """,
                rows=con_padre,
            )


def sincronizar_hilo_neo4j(idc_inicial: int) -> None:
    filas = run_query(
        """
        WITH RECURSIVE Conversacion AS (
            SELECT c.IDC, c.IDC_Padre, c.IDU, c.IDPub, c.comentario, 0 AS Nivel
            FROM Comentar c
            WHERE c.IDC = %s
            UNION ALL
            SELECT c.IDC, c.IDC_Padre, c.IDU, c.IDPub, c.comentario, conv.Nivel + 1
            FROM Comentar c
            INNER JOIN Conversacion conv ON c.IDC_Padre = conv.IDC
        )
        SELECT IDC, IDC_Padre, IDU, IDPub, comentario
        FROM Conversacion
        ORDER BY Nivel, IDC
        """,
        (int(idc_inicial),),
    )
    guardar_filas_en_neo4j(filas)


def ensure_neo4j_tiene_hilos() -> None:
    driver = get_neo4j()
    if driver is None:
        return
    with driver.session() as s:
        rec = s.run(
            "CALL db.relationshipTypes() YIELD relationshipType RETURN collect(relationshipType) AS tipos"
        ).single()
        tipos = rec["tipos"] if rec else []
    if "RESPONDE_A" not in tipos:
        hilos_con_resp = run_query(
            """
            SELECT c.IDC
            FROM Comentar c
            WHERE c.IDC_Padre IS NULL
            AND EXISTS (SELECT 1 FROM Comentar h WHERE h.IDC_Padre = c.IDC)
            ORDER BY c.IDC DESC
            LIMIT 5
            """
        )
        for h in hilos_con_resp:
            sincronizar_hilo_neo4j(int(h["IDC"]))


def ordenar_como_arbol(mensajes: list[dict], raiz_id: int) -> list[dict]:
    por_id = {m["IDC"]: m for m in mensajes}
    hijos = {}
    for m in mensajes:
        pid = m.get("IDC_Padre")
        if pid in por_id and m["IDC"] != raiz_id:
            hijos.setdefault(pid, []).append(m)
    for lista in hijos.values():
        lista.sort(key=lambda x: x["IDC"])

    ordenados = []
    visitados = set()

    def dfs(cid: int):
        if cid in visitados or cid not in por_id:
            return
        visitados.add(cid)
        ordenados.append(por_id[cid])
        for h in hijos.get(cid, []):
            dfs(h["IDC"])

    dfs(raiz_id)
    for m in mensajes:
        if m["IDC"] not in visitados:
            ordenados.append(m)
    return ordenados


def iniciales(nombre: str) -> str:
    partes = [p[0].upper() for p in (nombre or "U").split() if p]
    return "".join(partes[:2]) or "U"


def insertar_comentario(idu: int, idpub: int, idc_padre, texto: str) -> bool:
    filas = execute(
        "INSERT INTO Comentar (IDC_Padre, IDU, IDPub, comentario) VALUES (%s, %s, %s, %s)",
        (idc_padre, int(idu), int(idpub), texto),
    )
    if filas <= 0:
        return False

    try:
        nuevo = run_query(
            """
            SELECT IDC, IDC_Padre, IDU, IDPub, comentario
            FROM Comentar
            WHERE IDU = %s AND IDPub = %s
            ORDER BY IDC DESC
            LIMIT 1
            """,
            (int(idu), int(idpub)),
        )
        guardar_filas_en_neo4j(nuevo)
    except Exception as e:
        st.warning(f"Comentario guardado en MySQL, pero falló Neo4j: {e}")
    return True


def toggle_respuesta_inline(idc: int) -> None:
    actual = st.session_state.get("reply_to_id")
    st.session_state["reply_to_id"] = None if actual == idc else idc


def toggle_hilo(root_idc: int) -> None:
    abiertos = st.session_state.setdefault("hilos_abiertos", set())
    if root_idc in abiertos:
        abiertos.remove(root_idc)
    else:
        abiertos.add(root_idc)


def al_cambiar_publicacion() -> None:
    st.session_state["pub_fijada"] = st.session_state["selector_pub"]
    st.session_state["reply_to_id"] = None


def render_caja_respuesta_inline(
    idc_objetivo: int,
    autor_objetivo: str,
    root_idc: int,
    idu_actual: int,
    pub_sel: int,
    sangria_px: int = 0,
) -> None:
    if st.session_state.get("reply_to_id") != idc_objetivo:
        return

    if sangria_px > 0:
        st.markdown(f'<div style="margin-left: {sangria_px}px;"></div>', unsafe_allow_html=True)

    with st.form(key=f"form_inline_reply_{idc_objetivo}", clear_on_submit=True):
        c_in, c_pub, c_can = st.columns([6, 1.3, 1.3])
        texto_resp = c_in.text_input(
            f"Responder a {autor_objetivo}",
            placeholder=f"Escribe una respuesta para @{autor_objetivo}...",
            label_visibility="collapsed",
        )
        btn_pub = c_pub.form_submit_button("Publicar", type="primary")
        btn_can = c_can.form_submit_button("Cancelar")

    if btn_can:
        st.session_state["reply_to_id"] = None
        st.rerun()

    if btn_pub:
        texto_limpio = texto_resp.strip()
        if not texto_limpio:
            st.warning("Escribe una respuesta antes de publicar.")
        elif insertar_comentario(idu_actual, pub_sel, int(idc_objetivo), texto_limpio):
            st.session_state["pub_fijada"] = int(pub_sel)
            st.session_state.setdefault("hilos_abiertos", set()).add(int(root_idc))
            st.session_state["reply_to_id"] = None
            st.rerun()


st.set_page_config(
    page_title="AquaLife · Comentarios",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)

ensure_db_objects()

# Estilos
st.markdown(
    """
    <style>
    .hero-box {
        background: linear-gradient(135deg, #0b4f6c 0%, #1481ba 60%, #17bebb 100%);
        padding: 1.4rem 1.8rem;
        border-radius: 14px;
        color: #ffffff;
        margin-bottom: 1.25rem;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.12);
    }
    .hero-title {
        font-size: 1.65rem;
        font-weight: 700;
        margin: 0 0 0.25rem 0;
    }
    .hero-subtitle {
        font-size: 0.94rem;
        opacity: 0.92;
        margin: 0;
    }
    .ig-post-header {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 14px;
        padding: 0.95rem 1.2rem;
        margin-bottom: 0.9rem;
        display: flex;
        align-items: center;
        gap: 0.85rem;
    }
    .ig-avatar {
        width: 36px;
        height: 36px;
        min-width: 36px;
        border-radius: 50%;
        background: linear-gradient(135deg, #0b4f6c, #17bebb);
        color: #ffffff;
        font-weight: 700;
        font-size: 0.82rem;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .ig-avatar-sm {
        width: 28px;
        height: 28px;
        min-width: 28px;
        border-radius: 50%;
        background: linear-gradient(135deg, #1481ba, #17bebb);
        color: #ffffff;
        font-weight: 700;
        font-size: 0.72rem;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .ig-comment {
        display: flex;
        align-items: flex-start;
        gap: 0.7rem;
        padding: 0.45rem 0.2rem;
    }
    .ig-reply-wrap {
        border-left: 2px solid rgba(128, 128, 128, 0.28);
        padding-left: 0.9rem;
    }
    .ig-text {
        font-size: 0.95rem;
        line-height: 1.42;
        margin: 0;
    }
    .ig-mention {
        color: #1481ba;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero-box">
        <div class="hero-title">💬 Comentarios de la Comunidad</div>
        <p class="hero-subtitle">
            Explora las publicaciones de AquaLife, inicia comentarios y responde directamente debajo de cada acuarista.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### 🐠 AquaLife")
    st.caption("Sistema de soporte a decisiones · AquaSolutions (2026-2027)")

tarea4b = cargar_tarea4b()
if tarea4b is None:
    st.error("No se encontró `nosql/neo4j/tarea4b.py` en el repositorio.")
    st.stop()

if get_neo4j() is None:
    st.error("No hay conexión disponible con Neo4j.")
    st.stop()

try:
    ensure_conversaciones_db()
    ensure_neo4j_tiene_hilos()
except Exception as e:
    st.error(f"Error al preparar conversaciones: {e}")
    st.stop()

st.session_state.setdefault("reply_to_id", None)
st.session_state.setdefault("hilos_abiertos", set())

usuarios = run_query("SELECT IDU, Nombre FROM Usuario ORDER BY IDU")
if not usuarios:
    st.warning("No hay usuarios registrados en la base de datos.")
    st.stop()

mapa_usuarios = {u["IDU"]: (u.get("Nombre") or f"Usuario #{u['IDU']}") for u in usuarios}

pubs_resumen = run_query(
    """
    SELECT
        c.IDPub,
        COUNT(*) AS total_comentarios,
        SUM(CASE WHEN c.IDC_Padre IS NOT NULL THEN 1 ELSE 0 END) AS total_respuestas
    FROM Comentar c
    GROUP BY c.IDPub
    ORDER BY total_respuestas DESC, total_comentarios DESC, c.IDPub DESC
    LIMIT 100
    """
)
pubs_info = run_query(
    """
    SELECT p.IDPub, u.Nombre AS autor_pub
    FROM Publicacion p
    JOIN Usuario u ON p.IDU = u.IDU
    ORDER BY p.IDPub
    """
)
mapa_autores_pub = {p["IDPub"]: p["autor_pub"] for p in pubs_info}

# Barra superior con estado persistente 
top1, top2 = st.columns([1, 2])

opciones_usr = {u["IDU"]: u.get("Nombre") or f"Usuario #{u['IDU']}" for u in usuarios}
idu_actual = top1.selectbox(
    "👤 Comentar como",
    options=list(opciones_usr.keys()),
    format_func=lambda uid: opciones_usr[uid],
    key="selector_usuario",
)

if pubs_resumen:
    opciones_pub = {}
    for p in pubs_resumen:
        pid = int(p["IDPub"])
        autor_p = mapa_autores_pub.get(pid, "Acuarista")
        n_com = int(p["total_comentarios"])
        n_resp = int(p["total_respuestas"])
        etiqueta = f"Publicación #{pid} · {autor_p} ({n_com} comentarios"
        if n_resp > 0:
            etiqueta += f", {n_resp} respuestas"
        etiqueta += ")"
        opciones_pub[pid] = etiqueta

    lista_ids_pub = list(opciones_pub.keys())
    pub_fijada = st.session_state.get("pub_fijada")

    # Si la publicación fijada no estaba en el top 100, mantenerla en opciones
    if pub_fijada is not None and pub_fijada not in opciones_pub:
        opciones_pub[pub_fijada] = f"Publicación #{pub_fijada} · {mapa_autores_pub.get(pub_fijada, 'Acuarista')}"
        lista_ids_pub.insert(0, pub_fijada)

    idx_inicial = lista_ids_pub.index(pub_fijada) if pub_fijada in lista_ids_pub else 0

    pub_sel = top2.selectbox(
        "📸 Publicación",
        options=lista_ids_pub,
        index=idx_inicial,
        format_func=lambda pid: opciones_pub[pid],
        key="selector_pub",
        on_change=al_cambiar_publicacion,
    )
    st.session_state["pub_fijada"] = int(pub_sel)
else:
    pub_sel = top2.number_input("📸 Publicación (IDPub)", min_value=1, step=1, value=59, key="input_pub_unica")
    st.session_state["pub_fijada"] = int(pub_sel)

autor_pub = mapa_autores_pub.get(pub_sel, "Acuarista AquaLife")

# Cabecera de la publicación
st.markdown(
    f"""
    <div class="ig-post-header">
        <div class="ig-avatar">{html.escape(iniciales(autor_pub))}</div>
        <div>
            <div style="font-weight:700; font-size:1rem;">{html.escape(autor_pub)}</div>
            <div style="font-size:0.84rem; opacity:0.78;">Publicación #{int(pub_sel)} · Comunidad AquaLife</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Caja de nuevo comentario de la publicación
with st.form("form_nuevo_comentario_inicio", clear_on_submit=True):
    c_nuevo, c_enviar = st.columns([6, 1.4])
    texto_raiz = c_nuevo.text_input(
        "Nuevo comentario",
        placeholder="Agrega un nuevo comentario a esta publicación...",
        label_visibility="collapsed",
    )
    publicar_raiz = c_enviar.form_submit_button("Publicar", type="primary")

if publicar_raiz:
    texto_limpio = texto_raiz.strip()
    if not texto_limpio:
        st.warning("Escribe un mensaje antes de publicar.")
    elif insertar_comentario(idu_actual, pub_sel, None, texto_limpio):
        st.session_state["pub_fijada"] = int(pub_sel)
        st.session_state["reply_to_id"] = None
        st.rerun()

st.markdown("<hr style='margin: 0.6rem 0 0.8rem 0; opacity: 0.18;'>", unsafe_allow_html=True)

# Cargar comentarios raíz de esta publicación
raices_pub = run_query(
    """
    SELECT
        c.IDC,
        c.IDU,
        u.Nombre AS autor,
        c.comentario,
        (SELECT COUNT(*) FROM Comentar h WHERE h.IDC_Padre = c.IDC) AS respuestas_directas
    FROM Comentar c
    JOIN Usuario u ON c.IDU = u.IDU
    WHERE c.IDPub = %s AND c.IDC_Padre IS NULL
    ORDER BY respuestas_directas DESC, c.IDC DESC
    LIMIT 30
    """,
    (int(pub_sel),),
)

if len(raices_pub) <= 5:
    for r in raices_pub:
        if r["respuestas_directas"] > 0 and f"auto_{r['IDC']}" not in st.session_state:
            st.session_state["hilos_abiertos"].add(r["IDC"])
            st.session_state[f"auto_{r['IDC']}"] = True

todos_mensajes_vistos = []

if not raices_pub:
    st.info("Aún no hay comentarios en esta publicación. ¡Sé el primero en comentar arriba!")
else:
    for r in raices_pub:
        root_idc = int(r["IDC"])
        autor_r = str(r.get("autor") or f"Usuario #{r['IDU']}")
        texto_r = str(r.get("comentario") or "")
        tiene_resp = int(r["respuestas_directas"]) > 0

        # Comentario raíz
        st.markdown(
            f"""
            <div class="ig-comment">
                <div class="ig-avatar">{html.escape(iniciales(autor_r))}</div>
                <div>
                    <p class="ig-text">
                        <strong>{html.escape(autor_r)}</strong>
                        {html.escape(texto_r)}
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Acciones debajo del comentario raíz
        abierto = root_idc in st.session_state["hilos_abiertos"]
        respondiendo_aqui = st.session_state.get("reply_to_id") == root_idc

        if tiene_resp:
            a1, a2, _ = st.columns([1.2, 2.2, 6])
            a1.button(
                "Cerrar" if respondiendo_aqui else "Responder",
                key=f"reply_{root_idc}",
                on_click=toggle_respuesta_inline,
                args=(root_idc,),
            )
            a2.button(
                "── Ocultar respuestas" if abierto else "── Ver respuestas",
                key=f"toggle_{root_idc}",
                on_click=toggle_hilo,
                args=(root_idc,),
            )
        else:
            a1, _ = st.columns([1.2, 8])
            a1.button(
                "Cerrar" if respondiendo_aqui else "Responder",
                key=f"reply_{root_idc}",
                on_click=toggle_respuesta_inline,
                args=(root_idc,),
            )

        # Caja de respuesta inline justo debajo del comentario raíz
        render_caja_respuesta_inline(
            idc_objetivo=root_idc,
            autor_objetivo=autor_r,
            root_idc=root_idc,
            idu_actual=idu_actual,
            pub_sel=pub_sel,
            sangria_px=38,
        )

        # Respuestas anidadas obtenidas desde Neo4j
        if tiene_resp and abierto:
            try:
                hilo = tarea4b.obtener_hilo(root_idc)
                if not hilo:
                    sincronizar_hilo_neo4j(root_idc)
                    hilo = tarea4b.obtener_hilo(root_idc)
                for m in hilo:
                    m["autor"] = mapa_usuarios.get(m["IDU"], f"Usuario #{m['IDU']}")
            except Exception as e:
                st.error(f"Error al cargar respuestas desde Neo4j: {e}")
                hilo = []

            if hilo:
                todos_mensajes_vistos.extend(hilo)
                por_id = {m["IDC"]: m for m in hilo}
                respuestas = [m for m in ordenar_como_arbol(hilo, root_idc) if m["IDC"] != root_idc]

                for resp in respuestas:
                    resp_idc = int(resp["IDC"])
                    nivel = int(resp["Nivel"])
                    sangria_px = 38 + min(nivel - 1, 3) * 24
                    autor_resp = str(resp.get("autor") or f"Usuario #{resp['IDU']}")
                    texto_resp = str(resp.get("comentario") or "")
                    padre_obj = por_id.get(resp.get("IDC_Padre"))
                    mencion_html = (
                        f'<span class="ig-mention">@{html.escape(padre_obj["autor"])}</span> '
                        if padre_obj
                        else ""
                    )

                    st.markdown(
                        f"""
                        <div class="ig-reply-wrap" style="margin-left: {sangria_px}px;">
                            <div class="ig-comment">
                                <div class="ig-avatar-sm">{html.escape(iniciales(autor_resp))}</div>
                                <div>
                                    <p class="ig-text">
                                        <strong>{html.escape(autor_resp)}</strong>
                                        {mencion_html}{html.escape(texto_resp)}
                                    </p>
                                </div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    r_esp, r_btn, _ = st.columns([0.5 + min(nivel, 3) * 0.35, 1.2, 7])
                    r_btn.button(
                        "Cerrar" if st.session_state.get("reply_to_id") == resp_idc else "Responder",
                        key=f"reply_{resp_idc}",
                        on_click=toggle_respuesta_inline,
                        args=(resp_idc,),
                    )

                    # Caja de respuesta inline justo debajo de esta respuesta
                    render_caja_respuesta_inline(
                        idc_objetivo=resp_idc,
                        autor_objetivo=autor_resp,
                        root_idc=root_idc,
                        idu_actual=idu_actual,
                        pub_sel=pub_sel,
                        sangria_px=sangria_px + 28,
                    )

        st.markdown("<hr style='margin: 0.45rem 0; opacity: 0.15;'>", unsafe_allow_html=True)

if todos_mensajes_vistos:
    with st.expander("🛠️ Ver datos técnicos del grafo (Neo4j)"):
        df_hilo = pd.DataFrame(todos_mensajes_vistos)[
            ["Nivel", "IDC", "IDC_Padre", "IDU", "autor", "comentario"]
        ]
        st.dataframe(df_hilo, hide_index=True)

st.divider()
st.caption("AquaSolutions · Departamento de Analítica de Datos · Bases de Datos 2026-2027")