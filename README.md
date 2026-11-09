# FastAPI API

API REST de ejemplo pensada como base para aplicaciones reales que necesitan
usuarios, autenticación y contenido.

El proyecto muestra cómo construir un backend ordenado con **FastAPI, MySQL y
Redis**, aplicando buenas prácticas de estructura, seguridad, pruebas y
documentación. Sirve como plantilla para arrancar una API sin resolver desde
cero el login, los permisos, las migraciones o el manejo de errores.

## ¿Qué incluye?

- Registro e inicio de sesión con contraseñas cifradas.
- Autenticación mediante tokens de acceso y tokens de refresco.
- Renovación segura de sesión, cierre de sesión y detección de reutilización de
  tokens.
- Roles de usuario: usuario normal y superusuario.
- Gestión de usuarios: perfil propio, listado, búsqueda, edición y borrado.
- Publicaciones asociadas a un autor, con paginación, búsqueda y filtros.
- Permisos para que cada usuario solo pueda modificar sus propios recursos.
- Validación de datos de entrada y respuestas de error uniformes.
- Límite de intentos de inicio de sesión para evitar ataques de fuerza bruta.
- Logs con identificador de petición para facilitar el seguimiento.
- Comprobaciones de salud y métricas para monitorizar la aplicación.
- Migraciones de base de datos y pruebas automatizadas.

## Tecnologías utilizadas

| Tecnología | Para qué se usa |
| --- | --- |
| **FastAPI** | Framework principal para construir la API y su documentación |
| **SQLAlchemy** | Acceso y modelado de la base de datos |
| **MySQL** | Base de datos relacional |
| **Alembic** | Control de cambios y migraciones de la base de datos |
| **Pydantic** | Validación de datos de entrada y salida |
| **PyJWT** | Creación y validación de tokens de autenticación |
| **pwdlib** | Cifrado seguro de contraseñas con Argon2 |
| **Redis** | Límite de intentos de login y control de sesiones |
| **Prometheus Client** | Métricas de uso de la API |
| **Pytest** | Pruebas automatizadas |
| **Ruff** | Análisis y formato del código |
| **ty** | Comprobación de tipos |
| **uv** | Gestión de Python y dependencias |

## Estructura del proyecto

```text
app/
├── api/          # Rutas HTTP y dependencias de la API
├── core/         # Configuración, seguridad, errores, logs y métricas
├── db/           # Conexión y base de los modelos
├── models/       # Tablas de la base de datos
├── schemas/      # Validación de datos de entrada y salida
├── repositories/ # Consultas a la base de datos
├── services/     # Reglas de negocio
└── main.py       # Punto de arranque de la aplicación

alembic/          # Migraciones de la base de datos
scripts/          # Utilidades, como la creación del primer administrador
tests/            # Pruebas automatizadas
```

La aplicación sigue una separación por capas:

```text
Ruta HTTP → Servicio → Repositorio → Base de datos
```

Cada capa tiene una responsabilidad concreta, lo que facilita mantener y hacer
crecer el proyecto sin mezclar la lógica de negocio con el acceso a datos.

## Cómo ejecutarlo

Requisitos:

- Python 3.13
- `uv`
- MySQL local
- Redis local (recomendado)

```powershell
uv sync
uv run alembic upgrade head
uv run fastapi dev
```

La API queda disponible en:

- Aplicación: <http://127.0.0.1:8000>
- Documentación interactiva: <http://127.0.0.1:8000/docs>
- Estado del servicio: <http://127.0.0.1:8000/health>
- Métricas: <http://127.0.0.1:8000/metrics>

Antes de arrancar, copia `.env.example` a `.env` y ajusta las credenciales de
MySQL, Redis y la clave secreta.

Para crear el primer usuario administrador:

```powershell
uv run python -m scripts.seed_superuser `
  --email admin@example.com `
  --password cambiar123 `
  --full-name "Administrador"
```

## Endpoints principales

Todas las rutas de negocio están bajo el prefijo `/api/v1`.

| Área | Endpoints | Descripción |
| --- | --- | --- |
| Autenticación | `register`, `login`, `refresh`, `logout` | Crear cuenta, iniciar sesión, renovar tokens y cerrar sesión |
| Usuarios | `GET /users`, `GET /users/{id}`, `POST /users`, `PATCH /users/{id}`, `DELETE /users/{id}` | Consultar y administrar usuarios |
| Perfil | `GET /users/me` | Datos del usuario autenticado |
| Publicaciones | `GET /posts`, `GET /posts/{id}`, `POST /posts`, `PATCH /posts/{id}`, `DELETE /posts/{id}` | Crear y consultar publicaciones con su autor |
| Sistema | `/health`, `/health/ready`, `/metrics` | Estado de la aplicación y métricas |



## Objetivo del proyecto

Más que una API aislada, este repositorio busca mostrar una forma ordenada de
trabajar: separación de responsabilidades, seguridad desde el inicio,
validación de datos, pruebas automatizadas, observabilidad y documentación.

Es un punto de partida útil para proyectos que necesiten usuarios, inicio de
sesión, permisos y contenido, y también una muestra práctica del tipo de
arquitectura utilizada en aplicaciones backend reales.
