# Base de Datos AquaLife - MySQL Docker

Este proyecto contiene la configuración de Docker para crear y cargar automáticamente la base de datos **AquaLife** en MySQL.

## Archivos

- `docker-compose.yml`: Configuración de Docker Compose para construir y desplegar el contenedor MySQL y las bases de datos NoSQL (documental, grafo, columnar y llave-valor).
- `Dockerfile`: Define cómo se construye la imagen de MySQL con la base de datos ya cargada.
- `guidelines.tex`: Orientación del proyecto.

## Uso a través de Docker Compose

1. **Construir e iniciar el contenedor**:
   ```bash
   docker compose up -d --build
   ```
   La primera vez, Docker construye la imagen (puede tardar unos minutos mientras se carga la base de datos). Si quieres ver el avance del proceso en detalle:
   ```bash
   docker compose build --progress=plain
   docker compose up -d
   ```

2. **Verificar que la base de datos se generó correctamente**:
   La imagen incluye un `init.sql` cuyo contenido debe ser siempre el mismo (la generación es reproducible). Comprueba su hash SHA-256 así:
   ```bash
   docker run --rm --entrypoint sh aqualife-mysql:local -c \
     "sha256sum /docker-entrypoint-initdb.d/init.sql"
   ```
   El resultado esperado es:
   ```
   ee4fc1f407daa82927d0be4459333810f65e6b474abec667d1f6f9f37d28f7f5  /docker-entrypoint-initdb.d/init.sql
   ```
   Si tu hash no coincide con este, tu imagen no se construyó igual que la de referencia (por ejemplo, si modificaste el `Dockerfile` o partiste de un checkout distinto) — reconstruye desde un clon limpio del repositorio antes de continuar.

3. **Verificar que el contenedor está corriendo**:
   ```bash
   docker compose ps
   ```
   La primera carga de datos de `mysqllab` (varios millones de filas) tarda **~2-3 minutos**. Durante ese tiempo el contenedor se ve como `starting` (no `healthy` todavía) — es normal, espera a que cambie a `healthy` antes de conectarte o hacer consultas; si consultas antes de tiempo, verás tablas con menos filas de las esperadas (o en 0) porque la carga sigue en curso.

4. **Conectarse a MySQL**:
   ```bash
   docker exec -it aqualife_mysql mysql -u root -p
   # Contraseña: root
   ```

5. **Detener el contenedor**:
   ```bash
   docker compose down
   ```

6. **Detener y eliminar los datos**:
   ```bash
   docker compose down -v
   ```

## Credenciales

| Servicio | Tipo de base | Host → Puerto | Usuario / contraseña |
|---|---|---|---|
| `mysqllab` | SQL relacional (MySQL) | `localhost:3306` | `root/root` o `aqualife_user/aqualife_pass` (base `AquaLife`) |
| `mongo` | NoSQL documental (MongoDB) | `localhost:27017` | `admin/password` |
| `neo4j` | NoSQL de grafos (Neo4j) | `localhost:7474` (HTTP) / `localhost:7687` (Bolt) | `neo4j/password` |
| `monetdb` | NoSQL columnar (MonetDB) | `localhost:50001` | `monetdb/monetdb` (base `aqualife-db`) |
| `etcd1`/`etcd2`/`etcd3` | NoSQL llave-valor (cluster etcd) | solo red interna (`aqualife_net`) | sin autenticación |
| `redis` | NoSQL llave-valor en memoria (Redis) | `localhost:6379` | sin autenticación |

## Verificar que todos los servicios funcionan

Con los contenedores arriba (`docker compose up -d --build`), conéctate a cada servicio con su propio cliente y confirma que responde. Para MySQL, sigue el paso 4 de la sección anterior (conectarte con `mysql` y ejecutar cualquier consulta).

**MongoDB (documental)**:
```bash
docker exec -it aqualife_mongo mongosh --username admin --password password --authenticationDatabase admin --eval "db.runCommand({ ping: 1 })"
```
Respuesta esperada: `{ ok: 1 }`.

**Neo4j (grafo)**:
```bash
docker exec -it aqualife_neo4j cypher-shell -u neo4j -p password "RETURN 1 AS ok;"
```
Respuesta esperada: una fila con `ok` = `1`.

**MonetDB (columnar)**:
```bash
docker exec aqualife_monetdb sh -c "printf 'user=monetdb\npassword=monetdb\n' > /tmp/.monetdb && DOTMONETDBFILE=/tmp/.monetdb mclient -d aqualife-db -s 'SELECT 1;'"
```
Respuesta esperada: una tabla con una fila de valor `1` seguida de `1 tuple`.

**etcd (llave-valor, cluster de 3 nodos)**:
```bash
docker exec aqualife_etcd1 etcdctl put ping pong
docker exec aqualife_etcd1 etcdctl get ping
docker exec aqualife_etcd1 etcdctl endpoint health --endpoints=http://etcd1:2379,http://etcd2:2379,http://etcd3:2379
```
Respuesta esperada: `OK`; luego `ping` seguido de `pong`; y los tres endpoints reportando `is healthy`.

**Redis (llave-valor en memoria)**:
```bash
docker exec -it aqualife_redis redis-cli ping
```
Respuesta esperada: `PONG`.

## Conectar desde Jupyter Notebook

Para conectarse desde un notebook Jupyter usando `ipython-sql`:

```python
%load_ext sql
%sql mysql://root:root@localhost:3306/AquaLife
```

O si estás usando el mismo docker compose que el notebook:

```python
%load_ext sql
%sql mysql://root:root@mysqllab:3306/AquaLife
```

## Reiniciar la base de datos

Si necesitas reiniciar la base de datos con los datos iniciales:

```bash
# Detener y eliminar el contenedor y volumen
docker compose down -v

# Volver a iniciar
docker compose up -d
```
