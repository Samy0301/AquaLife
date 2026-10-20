# AquaLife · Proyecto final de Bases de Datos

Panel de control en Streamlit sobre la base de datos AquaLife (MySQL).

## Estructura

```
.
├── docker-compose.yml, Dockerfile, generate_init_sql.py, 000-hash-init.sh, zzz-cleanup.sh
│                           # Infraestructura (MySQL, MongoDB, Neo4j, MonetDB, etcd, Redis)
├── streamlit_app/          # Traea 6
│   ├── app.py              # Página principal (estado de conexión)
│   ├── db.py               # Conexión y helpers SQL (run_query, execute, call_procedure)
│   └── pages/              # Una página por funcionalidad 
├── sql/
│   ├── queries/            # Consultas Tarea 3 (3a–3e - 3h-3i) (un .sql por consulta; las lee el selector)
│   ├── conversations/      # Tarea 4a
│   ├── procedures/         # sp_analisis_usuario (3g)
│   └── triggers/           # Trigger de auditoría de precios (3f)
├── nosql/
│   ├── mongo               # Tarea 5
│   └── neo4j               # Tarea 4b
├── docs/                   # MERX, informe técnico (Tarea 4c, Tarea 5 justificacion), orientacion
├── requirements.txt
└── .env.example
```

## Requisitos
- Python 3.10+
- Docker

## Puesta en marcha
```bash
# 1. Contenedores (la primera vez tarda ~2-3 min en cargar los datos)
docker compose up -d --build
docker compose ps            # esperar a que mysqllab esté "healthy"

# 2. Entorno Python
python -m venv .venv
source .venv/bin/activate  
pip install -r requirements.txt

# 4. App
cd streamlit_app
streamlit run app.py
```

## Convenciones del equipo
- Cada consulta de la Tarea 3 va en `sql/queries/` con nombre tipo `3a_reacciones_por_publicacion.sql`
- Triggers y procedimientos se crean con el usuario `root` (MySQL con binlog activo no deja a `aqualife_user` crear triggers sin `--log-bin-trust-function-creators=1`).
- Una rama por tarea y pull request al repo.
