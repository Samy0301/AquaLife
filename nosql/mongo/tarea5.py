import importlib.util
import random
import sys
from pathlib import Path
from pymongo import  MongoClient,ASCENDING
import mysql.connector
from datetime import datetime,timezone
# Streamlit ejecuta las páginas con `streamlit_app/` en sys.path (=> `from db import ...`).
# Al ejecutar este archivo de forma independiente desde la raíz del repo, el módulo
# se encuentra como `streamlit_app.db`. Se admiten ambos contextos.
try:
    from db import MONGO_URI, MYSQL_CONFIG
except ModuleNotFoundError:
    from streamlit_app.db import MONGO_URI, MYSQL_CONFIG

# configuracion para conectarse a la bd de mongodb
BASE_DATOS = "aqualife_docs"
COLECCION_FICHAS = "fichas_especie"
COLECCION_SECUNDARIOS = "documentos_secundarios"


# id de ejemplo para buscar puede ser del 1 al 4000, fuere de ese rango la consulta de ejemplo dara como resultado None ( porque no existe) 
#ID =4000

# crear cliente de mongo, colecion de fichas y documentos secundarios
cliente = MongoClient(MONGO_URI)
db_mongo = cliente[BASE_DATOS]

fichas = db_mongo[COLECCION_FICHAS]
secundarios = db_mongo[COLECCION_SECUNDARIOS]




def consulta(query,params=None):
    """ para ejecutar una consulta en la bd mysql, devuelve todas las filas resultantes"""
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cur = conn.cursor()
    cur.execute(query, params or ())
    rows = cur.fetchall()
    return rows


CONSULTA_ESPECIES = """SELECT e.IDProd,e.NombreCientifico,e.NombreComun,e.TipoSustrato,e.Categoria,e.HorasLuz,e.LitrosMinimosTanque,ta.Tipo,t.Nombre,ce.Descripcion FROM Especie e JOIN TipoAgua ta ON e.IDTA =ta.IDTA JOIN Temporada t ON e.IDT =t.IDT JOIN Cuidados_Especificos ce ON e.IDCE =ce.IDCE"""


def _cargar_generador():
    """Carga generate_init_sql.py desde la raíz del repo para reutilizar sus catálogos."""
    nombre = "aqualife_generador_init"
    if nombre in sys.modules:
        return sys.modules[nombre]
    ruta = Path(__file__).resolve().parents[2] / "generate_init_sql.py"
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = modulo
    spec.loader.exec_module(modulo)
    return modulo


def filas_especie():
    """Devuelve las filas de origen para las fichas.

    Primero intenta leerlas de MySQL. Si las tablas de especies están vacías
    (init.sql incompleto), genera las mismas filas con los catálogos de
    generate_init_sql.py para que la colección de MongoDB nunca quede vacía.
    """
    try:
        filas = consulta(CONSULTA_ESPECIES)
        if filas:
            return filas
    except Exception:
        # MySQL no disponible: se generan las filas localmente.
        pass

    gen = _cargar_generador()
    gen.random.seed(2026)
    _, especies_info = gen.gen_especies_productos(gen.CONFIG["especies"])
    tipos_agua = gen.gen_tipos_agua(gen.CONFIG["tipos_agua"])
    cuidados = gen.gen_cuidados_especificos(gen.CONFIG["cuidados_especificos"])
    temporadas = gen.TEMPORADAS
    generadas = gen.gen_especies(especies_info, len(tipos_agua), len(temporadas), len(cuidados))

    tipos = {i: fila[0] for i, fila in enumerate(tipos_agua, start=1)}
    temps = {i: nombre for i, nombre in enumerate(temporadas, start=1)}
    cuidados_map = {i: fila[0] for i, fila in enumerate(cuidados, start=1)}

    return [
        (idp, namecien, namecom, sustrato, categ, horas, litros,
         tipos.get(id_ta, "Sin definir"), temps.get(id_t, "Sin definir"),
         cuidados_map.get(id_ce, "Sin definir"))
        for (idp, namecien, namecom, sustrato, categ, horas, litros,
             id_ta, id_t, id_ce) in generadas
    ]

def generar_min_max(a,b):
    """"para generar dos valores val1<val2 aleatorios en el rango a,b"""
    val1 = random.randint(a,b+2)
    val2 = abs(b-val1) 

    if val1!=val2:
         val1 = val1-1 if val1-1>a else a
         val2 = val2+1 if val2+1<b else b
    
    return min(val2,val1),max(val1,val2) 

def fecha(aaaa, mm, dd):
    """Fecha UTC sin hora ."""
    return datetime(aaaa, mm, dd, tzinfo=timezone.utc)

def obtener_documentos_especie(db,id_especie):
    """Dado el identificador de una especie (el mismo que en la base
    relacional, Especie.IDProd), retorna su ficha con todos sus documentos
    secundarios organizados jerárquicamente.

    Estructura devuelta (dict):
        ficha (campos de la Ficha de Especie)
        + "documentosSecundarios": lista con los secundarios embebidos y los
          referenciados, cada uno con "almacenamiento" = "embebido" o
          "referenciado", ordenados por tipo y fecha
        + "resumenSecundarios": {tipo: cantidad}
        + "totalDocumentosSecundarios": cantidad total

    Retorna None si no existe ficha para ese idEspecie.
    """
    ficha = db[COLECCION_FICHAS].find_one({"IDProd": id_especie})
    if ficha is None:
        return None

    # Secundarios embebidos: ya vienen dentro de la ficha.
    secundarios = []
    for doc in ficha.get("documentosSecundarios", []):
        copia = dict(doc)
        copia["almacenamiento"] = "embebido"
        secundarios.append(copia)

    # Secundarios referenciados: se buscan por idEspecie en la segunda
    # colección, ordenados por tipo y fecha
    referenciados = db[COLECCION_SECUNDARIOS].find({"IDProd": id_especie}).sort(
        [("tipo", ASCENDING), ("fecha", ASCENDING)]
    )
    for doc in referenciados:
        copia = dict(doc)
        copia.pop("_id", None)  # el _id interno de Mongo no forma parte del documento
        copia["almacenamiento"] = "referenciado"
        secundarios.append(copia)

    # Orden jerárquico: primero por tipo (alfabético) y luego por fecha.
    secundarios.sort(key=lambda d: (d["tipo"], str(d.get("fecha", ""))))

    resultado = dict(ficha)
    resultado["documentosSecundarios"] = secundarios
    resultado["totalDocumentosSecundarios"] = len(secundarios)
    resumen = {}
    for doc in secundarios:
        resumen[doc["tipo"]] = resumen.get(doc["tipo"], 0) + 1
    resultado["resumenSecundarios"] = resumen
    return resultado

def insertar(fichas,secundarios):

    # eliminar todos los doc anteriores para reinsertarlos
    fichas.delete_many({})
    secundarios.delete_many({})
      # consulta para retornar los filas y columnas necesarios 
    tabla_especie = filas_especie()

    niveles_de_cuidado = ['Facil',"Medio","Dificil","Muy Dificil"]
    resultados = ["Apto","No Apto"]
    enfermedades_names= ["Podredumbre del rizoma","Algas en las hojas","Hojas amarillas","Blanqueamiento"]
    agentes=["Pérdida de zooxantelas por temperatura o luz excesiva","Parámetros inestables o lesiones","Flujo inadecuado o vecinos agresivos","Exceso de luz o nutrientes"]
    sintomas = ["Puntos verdes o filamentos sobre las hojas","Bacterias por rizoma enterrado o dañado","Falta de nutrientes (hierro o potasio)","El tejido se retira y deja el esqueleto expuesto"]

    i=1 
    for idp,namecien,namecom,tiposus,categ,hl,lmt,tipoa,namet,desc in tabla_especie:

            # buscar el max y min del ph
            phMin,phMax = generar_min_max(1,7)
            tempMin,tempMax = generar_min_max(-5,40)
            tamannoMax = random.randint(1,8)
            durezagmMin,durezaGhMax = generar_min_max(1,15)
            espeMin,espeMax = generar_min_max(5,30)
            semanas = random.randint(1,20)

            resultado = random.choice(resultados)
            enfermedades = []
            cant_enfermedades = random.randint(1,5)
            for _ in range(cant_enfermedades):
                    enfermedades.append({
                    "nombre": random.choice(enfermedades_names),
                    "agente": random.choice(agentes),
                    "sintomas": random.choice(sintomas),
                    "tratamiento": f"Subir la temperatura a {random.randint(25,28)}-{random.randint(29,31)} °C durante {random.randint(1,11)} días y verde de malaquita según la dosis indicada",
                    "prevencion": random.choice([f"Cuarentena de los {categ} nuevos",f"Mantener amoníaco y nitritos en {random.randint(0,5)}","Fertilizar cada semana tras el cambio de agua",f"Luz moderada ({random.randint(1,9)} h) y cambios de agua semanales"])
                    })

            ficha = {

                # son los de la tabla orginal 
                "IDProd": idp,
                "nombreCientifico":namecien,
                "nombreComun": namecom,
                "categoria": categ,
                "tipoAgua": tipoa,
                "temporada": namet,
                "cuidadosEspecificos": desc,
                "tipoSustrato": tiposus,
                "horasLuz": hl,
                "litrosMinimosTanque": lmt,

                # son nuevos 
                "parametrosAgua": {
                                    "pHMin": phMin, "pHMax": phMax,
                                    "temperaturaMinC": tempMin, "temperaturaMaxC":tempMax,
                                    "durezaGH": f"{durezagmMin}-{durezaGhMax} dGH", "salinidadPpt": None,
                                },

                "tamanoMaximoCm": tamannoMax,
                "esperanzaVidaAnios": f"{espeMin}-{espeMax}",
                "temperamento": "Pacífico, pez de cardumen",
                "nivelCuidado": random.choice(niveles_de_cuidado),
                "dieta": random.choice(["Omnívoro","Fertilización líquida (no se alimenta como un animal)","Fotosintético (zooxantelas) y zooplancton","Omnívoro y detritívoro"]),
                "schemaVersion": 1,
                "actualizadoEn": fecha(2026, 2, 10),
                "fuenteRelacional": {"tabla": "Especie", "idProd": idp},

                "documentosSecundarios": [
                            {
                                "tipo": "Certificado Sanitario",
                                "numeroCertificado": f"CERT-2026-{i}",
                                "emitidoPor": "Clínica Veterinaria Acuática Habana",
                                "fechaEmision": fecha(2026, 1, 10),
                                "fechaVencimiento": fecha(random.randint(2026,2030), random.randint(1,12), random.randint(1,27)),
                                "resultado":resultado ,
                                "observaciones": f"Sin parásitos externos visibles; aletas intactas; cuarentena de {semanas} semanas completada." if resultado == "Apto" else f"Con parásitos visibles; cuarentena de {semanas} semanas para curarse",
                            },
                            {
                                "tipo": "Guía de Alimentación Estacional",
                                "temporada": namet,
                                "alimentos": random.choices(["Escamas finas para tetras", "Artemia recién eclosionada", "Dafnia","Zooplancton (fitoplancton y artemia)", "Alimento líquido para corales LPS"],k=2),
                                "frecuenciaDiaria": random.randint(1,5),
                                "notas": f"Raciones pequeñas que se consuman en {random.randint(1,15)} minutos; un día de ayuno a la semana.",
                            },
                            {
                                "tipo": "Manual de Tratamiento de Enfermedades",
                                "enfermedades": enfermedades
                            },
                        ],

            }
            etapas = ["juvenil","adulto","anciano","recien nacido"]
            cant_doc_ref = random.randint(2,6)
            doc_refetenciados=[]
            for i in range(cant_doc_ref):
                f = {
                    "IDProd":idp,
                    "fecha":fecha(random.randint(2026,2030), random.randint(1,12), random.randint(1,27)),
                    "etapa":random.choice(etapas),
                    "tipo":random.choice(["Historial de Crecimiento","Análisis de Agua"])

                }
                if random.random()<0.4:
                    f['temperatura'] = random.randint(1,40)
                if random.random()<0.5:
                    f['ph']= random.randint(1,8)
                doc_refetenciados.append(f)
            i+=1
            fichas.insert_one(ficha)
            secundarios.insert_many(doc_refetenciados)

