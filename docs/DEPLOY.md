# Deploy de Carwash V2 al VPS Mukusoft

Reference deployment guide for running the stack on a VPS. Public examples use placeholders intentionally; production hostnames, usernames, credentials and customer data are kept outside the repository.

> Para developmento local con Docker, ver el README principal o `docker-compose.yml`.

---

## 0. Inventario del entorno destino

Target: a Linux VPS reachable through the deployment secrets configured in GitHub Actions.

Lo que **ya está instalado** (verificado el 2026-05-12):

- Docker 29.4.2 + Compose v5.1.3.
- NGINX Proxy Manager corriendo en `~/infra/nginx-proxy-manager/` (puertos 80/443
  públicos, admin en 127.0.0.1:81).
- Network Docker `proxy` (externa, compartida entre NPM y otros stacks).
- Usuario `<DEPLOY_USER>` en grupo `docker` (puede usar Docker sin sudo).

Lo que **no está**:

- PostgreSQL en host. La DB del V2 corre en container (parte del stack).
- Firewall (UFW). NPM abre solo 80/443.
- DNS para `*.carwash.<VPS_ALIAS>.com` (a configurar — sección 2).

---

## 1. DNS de los subdominios

Esto lo hacés en el provider de DNS de `<VPS_ALIAS>.com` (Cloudflare, Namecheap,
donde sea que tengas el dominio).

Para cada cliente vas a necesitar un subdominio. Hoy:

| Subdominio | Tipo | Valor |
|---|---|---|
| `autocare.carwash.<VPS_ALIAS>.com` | A | `<VPS_HOST>` |
| `demo.carwash.<VPS_ALIAS>.com` | A | `<VPS_HOST>` |

Validación local (puede tardar minutos en propagar):

```bash
dig +short autocare.carwash.<VPS_ALIAS>.com
dig +short demo.carwash.<VPS_ALIAS>.com
# Ambos deben devolver <VPS_HOST>
```

> **Decisión vigente**: SSL por subdominio con HTTP challenge (más simple).
> Si más adelante hay decenas de clientes, evaluamos wildcard con DNS challenge.

---

## 2. Apagar el carwash viejo (Streamlit)

El container `carwash-app` (chacalra/carwash, Streamlit) está corriendo desde
hace días. Lo bajamos antes del deploy del V2 para evitar confusión.

```bash
ssh <VPS_ALIAS>
cd ~/projects/carwash
docker compose down
docker ps | grep carwash  # no debe aparecer carwash-app
```

Si en algún momento querés volver al viejo (no debería ser el caso):

```bash
cd ~/projects/carwash && docker compose up -d
```

> Coordinate with any active users before stopping a legacy deployment.

---

## 3. Clonar el repo en el VPS

```bash
ssh <VPS_ALIAS>
mkdir -p ~/projects && cd ~/projects
git clone https://github.com/chacalra/carwashV2.git carwash-v2
cd carwash-v2
ls   # debe verse backend.Dockerfile, docker-compose.yml, etc.
```

---

## 4. Crear `.env` de producción

El `.env` NO se commite. Se crea **una sola vez** en el VPS con los secretos
reales. Si lo perdés y no tenés respaldo, tenés que rotar el JWT secret y
todos los usuarios deberán reloguearse.

```bash
cd ~/projects/carwash-v2
cp .env.example .env

# Generar el secret del JWT:
echo "AUTH_TOKEN_SECRET=$(openssl rand -hex 32)" >> .env
# Si ya tenías la línea AUTH_TOKEN_SECRET= en .env (vacía), editala con nano
# en su lugar (no quieras dos líneas con la misma var).

nano .env
```

Editar para que quede así (con valores reales, no estos placeholders):

```env
# Database (interna al stack, no expuesta al host)
POSTGRES_USER=carwash
POSTGRES_PASSWORD=<password-fuerte-generada>   # ej: openssl rand -base64 24
POSTGRES_DB=carwash

# JWT
AUTH_TOKEN_SECRET=<la-que-generaste-arriba>
AUTH_TOKEN_EXPIRES_MINUTES=60

# CORS: regex que matchea los subdominios de carwash en <VPS_ALIAS>
CORS_ALLOW_ORIGIN_REGEX=https://[a-z0-9-]+\.carwash\.<VPS_ALIAS>\.com

# Frontend port no se usa en prod (NPM proxea internamente).
# FRONTEND_PORT=80
```

> Guardá una copia segura del `.env` en 1Password / Bitwarden. Si el VPS se
> pierde o hay que restaurar, lo necesitás idéntico.

---

## 5. Build y levantado del stack

```bash
cd ~/projects/carwash-v2

# Build + up con override de prod.
# (el `--env-file .env` no haría falta porque docker compose lee .env por
# default, pero lo dejamos explicito.)
docker compose \
  --env-file .env \
  -f docker-compose.yml -f docker-compose.prod.yml \
  up -d --build
```

Esto:
- Crea el volume `carwash-v2_carwash-db-data` (datos de Postgres, persisten).
- Levanta `carwash-v2-db-1` (Postgres), `carwash-v2-backend-1` (uvicorn) y
  `carwash-v2-frontend-1` (nginx con dist estático).
- El backend corre migrations alembic y siembra permisos automáticamente.
- Backend y frontend se unen a la network `proxy` (donde vive NPM).

Verificación:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
# Los 3 servicios deben aparecer "Up" y la DB "healthy".

docker compose -f docker-compose.yml -f docker-compose.prod.yml logs backend --tail 30
# Debe terminar con "Uvicorn running on http://0.0.0.0:8000".
```

> **Si algo falla**: ver sección "Operación y troubleshooting" al final.

---

## 6. Configurar Proxy Hosts en NGINX Proxy Manager

NPM expone su UI en el VPS en `localhost:81`. Para acceder desde tu máquina,
abrí un túnel SSH:

```bash
# en tu maquina local
ssh -L 8181:127.0.0.1:81 <VPS_ALIAS>
```

Después abrí en el browser local: `http://localhost:8181` (el túnel redirige
a `:81` del VPS).

Credenciales del NPM admin (las tuyas, las definiste cuando lo instalaste).

### Para cada subdominio, crear un Proxy Host

Hacer **dos** entradas (una por subdominio, mismas opciones):

**Proxy Host #1 — `autocare.carwash.<VPS_ALIAS>.com`**

- Domain Names: `autocare.carwash.<VPS_ALIAS>.com`
- Scheme: `http`
- Forward Hostname / IP: `carwash-v2-frontend-1`
- Forward Port: `80`
- Block Common Exploits: ✓
- Websockets Support: ✓ (no se usan hoy pero no estorba)

Tab **SSL**:
- SSL Certificate: "Request a new SSL Certificate"
- Force SSL: ✓
- HTTP/2 Support: ✓
- Email: tu mail
- I agree to Let's Encrypt TOS: ✓

Save. NPM va a Let's Encrypt, valida el dominio (DNS challenge HTTP, requiere
que el A record ya esté apuntando al VPS) y emite el cert.

**Proxy Host #2 — `demo.carwash.<VPS_ALIAS>.com`**

Igual al anterior, cambiando el Domain Name.

### Verificación

Desde tu máquina:

```bash
curl -sI https://demo.carwash.<VPS_ALIAS>.com | head -3
# HTTP/2 200

curl -s https://demo.carwash.<VPS_ALIAS>.com/api/health
# {"status":"ok"}
```

---

## 7. Crear los tenants en producción

Ya tenés el stack arriba, ahora hay que crear los dos tenants.

### Tenant demo

```bash
cd ~/projects/carwash-v2

# Contraseña fuerte. Guardala en 1Password.
DEMO_PASSWORD=$(openssl rand -base64 18)
echo "Demo password: $DEMO_PASSWORD"   # copiala YA, despues no se imprime

docker compose -f docker-compose.yml -f docker-compose.prod.yml exec backend \
  uv run python -m backend.cli create-tenant \
  --subdomain demo \
  --name "Demo Carwash" \
  --responsible "Mukusoft" \
  --admin-username admin \
  --admin-password "$DEMO_PASSWORD"
```

Inmediatamente lo poblamos con datos demo:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec backend \
  uv run python scripts/seed_demo.py --subdomain demo
```

### Tenant autocare

```bash
CLIENT_PASSWORD="<contraseña que defina el cliente o vos>"

docker compose -f docker-compose.yml -f docker-compose.prod.yml exec backend \
  uv run python -m backend.cli create-tenant \
  --subdomain client-a \
  --name "Client A" \
  --responsible "<CLIENT_OWNER>" \
  --admin-username admin \
  --admin-password "$CLIENT_PASSWORD" \
  --email "<CONTACT_EMAIL>" \
  --phone "<CONTACT_PHONE>"
```

Importar el .db legacy actualizado. Bajar el .db reciente desde Render:

```bash
# En tu maquina local
scp <LEGACY_SOURCE_SSH>:/var/data/carwash.db/carwash.db \
  /tmp/client_legacy.db

# Subir al VPS (dentro de la carpeta `datos/` del proyecto)
scp /tmp/client_legacy.db <VPS_ALIAS>:~/projects/carwash-v2/datos/

# En el VPS
ssh <VPS_ALIAS>
cd ~/projects/carwash-v2
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec backend \
  uv run python scripts/import_autocare_legacy.py \
  --subdomain client-a \
  --db-path datos/client_legacy.db \
  --dry-run

# Si el dry-run se ve OK:
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec backend \
  uv run python scripts/import_autocare_legacy.py \
  --subdomain client-a \
  --db-path datos/client_legacy.db
```

---

## 8. Smoke test

Desde tu máquina (no desde el VPS):

1. Abrí `https://demo.carwash.<VPS_ALIAS>.com` → debe cargar el login.
2. Logueate con `admin` + la contraseña que guardaste + subdominio `demo` (el
   campo `subdominio` solo aparece en localhost; en prod se infiere del Host).
3. Dashboard con KPIs reales.
4. Repetir con `https://autocare.carwash.<VPS_ALIAS>.com` (admin / contraseña de
   Client A). Dashboard con ~468 ventas si la importación fue completa.
5. Crear una venta de prueba en `demo`, anularla.

Si algo falla, ver sección "Operación".

---

## 9. Operación y troubleshooting

### Ver logs

```bash
# Todo el stack
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f

# Solo backend
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f backend

# Ultimas 100 lineas y salir
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs --tail 100
```

### Reiniciar servicios

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart backend
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart frontend
```

### Re-deploy después de un cambio (manual, hasta que tengamos CD)

```bash
cd ~/projects/carwash-v2
git pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

Las migrations corren solas en el entrypoint del backend.

### Backup de la DB

```bash
# Dump comprimido a un archivo local en el VPS
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T db \
  pg_dump -U carwash -d carwash | gzip > ~/backups/carwash-$(date +%Y%m%d-%H%M).sql.gz

# Bajarlo a tu maquina
scp <VPS_ALIAS>:~/backups/carwash-*.sql.gz /tmp/
```

Recomendación: cron diario.

```bash
# crontab -e (en el VPS)
0 3 * * * cd ~/projects/carwash-v2 && docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T db pg_dump -U carwash -d carwash | gzip > ~/backups/carwash-$(date +\%Y\%m\%d).sql.gz
```

### Restore

```bash
# Subir el dump al VPS
scp /tmp/carwash-20260512.sql.gz <VPS_ALIAS>:~/backups/

# Restaurar (CUIDADO: pisa la DB actual)
ssh <VPS_ALIAS>
cd ~/projects/carwash-v2
gunzip -c ~/backups/carwash-20260512.sql.gz | docker compose \
  -f docker-compose.yml -f docker-compose.prod.yml exec -T db \
  psql -U carwash -d carwash
```

### Rollback rápido

Si un deploy rompe algo:

```bash
cd ~/projects/carwash-v2
git log --oneline -10
git checkout <commit-anterior>
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

### Bajar todo (sin perder DB)

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml down
```

### Bajar y borrar TODA la data (cuidado, irrecuperable)

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml down -v
```

---

## 10. Problemas comunes

### `502 Bad Gateway` al entrar al subdominio

NPM no encuentra el container del frontend. Verificar:

```bash
ssh <VPS_ALIAS>
docker network inspect proxy --format '{{range .Containers}}{{.Name}} {{end}}'
# Tiene que aparecer: nginx-proxy-manager carwash-v2-frontend-1 ...
```

Si no aparece el frontend, levantaste el stack sin el override de prod. Revisar
que el comando lleve `-f docker-compose.prod.yml`.

### Login no funciona pero `/api/health` sí

Probablemente el `AUTH_TOKEN_SECRET` cambió entre deploys y los tokens viejos
quedaron inválidos. Limpiar el localStorage del browser y reloguear.

### El `create-tenant` dice "No hay permisos activos"

El seed de permisos no se ejecutó. Correrlo manualmente:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec backend \
  uv run python -c "
from backend.database.connection import SessionLocal
from backend.database.seed import seed_permissions
with SessionLocal() as s:
    seed_permissions(s)
    s.commit()
print('OK')
"
```

(Normalmente lo corre el entrypoint en cada boot del backend.)

### Certs SSL no se renuevan

NPM intenta renovar 30 días antes de expirar. Si falla:

1. UI NPM → SSL Certificates → click en el cert → "Renew".
2. Verificar logs de NPM: `docker logs nginx-proxy-manager --tail 100`.

---

## 11. Procedimiento de alta de cliente nuevo

Para sumar `<cliente>.carwash.<VPS_ALIAS>.com`:

1. **DNS**: A record `<cliente>.carwash.<VPS_ALIAS>.com` → `<VPS_HOST>`.
2. **NPM**: Proxy Host nuevo → forward a `carwash-v2-frontend-1:80` + SSL Let's Encrypt.
3. **Tenant** en backend:
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.prod.yml exec backend \
     uv run python -m backend.cli create-tenant \
     --subdomain <cliente> --name "<Nombre>" --responsible "<Owner>" \
     --admin-username admin --admin-password "<password>"
   ```
4. (Opcional) **Branding**:
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.prod.yml exec backend \
     uv run python -m backend.cli set-branding \
     --subdomain <cliente> --primary "#FF6B00" --secondary "#003D6B" \
     --logo "https://..."
   ```

Todo dura ~5 minutos por cliente.

---

## 12. Próximos pasos

Pendientes después del primer deploy:

- **CD automático** desde GitHub Actions (push a `main` → deploy). Ver
  iteración futura.
- **Sentry / monitoreo de errores** en runtime.
- **Backups remotos** (no solo en el VPS).
- **Wildcard SSL** si la cantidad de clientes crece.
