# ---------------------------------------------------------------------------
# Etapa 1 ("generator"): genera init.sql con Python. Esta etapa se descarta
# al final del build, asi que Python nunca forma parte de la imagen final de
# MySQL (mas liviana, sin dependencias extra instaladas de forma permanente).
# ---------------------------------------------------------------------------
FROM python:3.12-alpine AS generator

WORKDIR /gen
COPY generate_init_sql.py .
RUN python3 generate_init_sql.py --output /gen/init.sql \
    && echo "[hash-init:build] SHA-256 de init.sql: $(sha256sum /gen/init.sql | awk '{print $1}')"

# ---------------------------------------------------------------------------
# Etapa 2: imagen final de MySQL. Solo se copia el init.sql ya generado
# (y los scripts de hash/limpieza), sin instalar Python.
# ---------------------------------------------------------------------------
FROM mysql:8.0

WORKDIR /docker-entrypoint-initdb.d

# MySQL solo auto-ejecuta ficheros .sh/.sql/.sql.gz en docker-entrypoint-initdb.d,
# por eso el fichero generado se llama init.sql (no init.db).
COPY --from=generator /gen/init.sql init.sql

# Se ejecuta antes de init.sql (ordena alfabeticamente primero) e imprime en
# los logs del contenedor el SHA-256 de init.sql, justo antes de que MySQL
# lo cargue.
COPY 000-hash-init.sh .

# Se ejecuta despues de init.sql (ordena alfabeticamente al final) y borra
# init.sql una vez que MySQL ya cargo los datos, para que no quede accesible
# dentro del contenedor tras el primer arranque.
COPY zzz-cleanup.sh .

RUN chmod +x 000-hash-init.sh zzz-cleanup.sh
