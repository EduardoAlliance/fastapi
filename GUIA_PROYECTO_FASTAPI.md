# Guía: Proyecto FastAPI profesional desde cero

Guía práctica para construir una API REST real con FastAPI, MySQL, SQLAlchemy, JWT y una estructura pensada para crecer.

> **Enfoque:** aprender FastAPI construyendo. No es un curso de Python desde cero; es una guía de arquitectura y patrones para alguien que ya viene de Laravel, React y Node.

---

## Índice

1. [Stack y responsabilidades](#1-stack-y-responsabilidades)
2. [Requisitos y creación del proyecto](#2-requisitos-y-creación-del-proyecto)
3. [Estructura de carpetas](#3-estructura-de-carpetas)
4. [Configuración con Pydantic Settings](#4-configuración-con-pydantic-settings)
5. [Base de datos con SQLAlchemy 2.0](#5-base-de-datos-con-sqlalchemy-20)
6. [Migraciones con Alembic](#6-migraciones-con-alembic)
7. [Modelos, schemas y validaciones](#7-modelos-schemas-y-validaciones)
8. [Autenticación JWT](#8-autenticación-jwt)
9. [Dependencias, permisos y middleware](#9-dependencias-permisos-y-middleware)
10. [CRUD de usuarios](#10-crud-de-usuarios)
11. [Relaciones entre tablas](#11-relaciones-entre-tablas)
12. [Paginación, filtros y búsqueda](#12-paginación-filtros-y-búsqueda)
13. [Manejo de errores](#13-manejo-de-errores)
14. [Pruebas automatizadas](#14-pruebas-automatizadas)
15. [Redis: caché y tareas](#15-redis-caché-y-tareas)
16. [Roadmap por fases](#16-roadmap-por-fases)
17. [Reglas de oro y convenciones](#17-reglas-de-oro-y-convenciones)
18. [Comandos útiles](#18-comandos-útiles)

---

## 1. Stack y responsabilidades

| Librería | Para qué sirve | En este proyecto |
|---|---|---|
| **FastAPI** | Framework principal | Rutas, validación, OpenAPI, inyección de dependencias |
| **SQLAlchemy 2.0** | ORM y acceso a datos | Modelos, sesiones, consultas tipadas |
| **Pydantic 2** | Validación y serialización | Schemas de entrada/salida y configuración |
| **Alembic** | Migraciones | Versionar el esquema de MySQL |
| **PyJWT** | Autenticación JWT | Access tokens firmados |
| **pwdlib** | Hash de contraseñas | Argon2 (recomendado sobre bcrypt) |
| **Uvicorn** | Servidor ASGI | Desarrollo y producción |
| **Pytest** | Pruebas automatizadas | Tests de endpoints y servicios |
| **Redis** | Caché y tareas | Caché de consultas, rate limiting, colas |

### ¿Por qué pwdlib y no passlib?

`passlib` está sin mantenimiento activo y tiene problemas con versiones recientes de Python. `pwdlib` es la alternativa moderna, con soporte para Argon2 y bcrypt, y es la que recomienda el ecosistema FastAPI actual.

### ¿Sync o async?

Para aprender y para la mayoría de APIs con MySQL, empieza con **SQLAlchemy síncrono**:

- Es más simple de depurar.
- FastAPI ejecuta las funciones `def` en un threadpool, así que no bloqueas el event loop.
- Los drivers async de MySQL añaden complejidad sin beneficio claro al principio.

**Regla:** si usas SQLAlchemy síncrono, declara los endpoints con `def`, no con `async def`.

---

## 2. Requisitos y creación del proyecto

### 2.1 Requisitos

- Python 3.12+ (tu venv actual tiene 3.15.2)
- MySQL 8+
- Redis (opcional al inicio)
- Git

> **Nota sobre Python 3.15:** si algún driver todavía no publica wheels para 3.15 en tu sistema, crea el proyecto con 3.13 o 3.14. `uv` te permite fijar la versión sin complicaciones.

### 2.2 Instalar `uv` (recomendado)

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

`uv` gestiona Python, el entorno virtual y las dependencias mucho más rápido que pip.

### 2.3 Crear el proyecto

```powershell
uv init fast-api
cd fast-api
uv python pin 3.13
```

Si ya tienes la carpeta y el `venv`, puedes saltar la creación y solo añadir dependencias:

```powershell
uv venv
.\.venv\Scripts\Activate.ps1
```

> Si tu entorno actual se llama `venv` (no `.venv`), actívalo con `.\\venv\\Scripts\\Activate.ps1`. `uv` crea y usa `.venv` por convención; mantén uno solo para evitar confusiones.

### 2.4 Dependencias

```powershell
uv add "fastapi[standard]" sqlalchemy pymysql cryptography alembic pydantic-settings pyjwt "pwdlib[argon2]" email-validator redis
uv add --dev pytest pytest-cov httpx ruff ty
```

| Paquete | Motivo |
|---|---|
| `fastapi[standard]` | Incluye el CLI `fastapi`, Uvicorn y utilidades |
| `pymysql` | Driver MySQL puro Python |
| `cryptography` | Necesario para autenticación `caching_sha2_password` de MySQL 8 |
| `pydantic-settings` | Leer configuración desde `.env` |
| `email-validator` | Validar `EmailStr` |
| `redis` | Cliente Redis (sync y async) |
| `httpx` | Cliente HTTP para tests |

### 2.5 `pyproject.toml` de referencia

```toml
[project]
name = "fast-api"
version = "0.1.0"
description = "API REST profesional con FastAPI"
requires-python = ">=3.12"
dependencies = [
    "fastapi[standard]>=0.162",
    "sqlalchemy>=2.0",
    "pymysql>=1.1",
    "cryptography>=44",
    "alembic>=1.14",
    "pydantic-settings>=2.6",
    "pyjwt>=2.10",
    "pwdlib[argon2]>=0.2",
    "email-validator>=2.2",
    "redis>=5.2",
]

[dependency-groups]
dev = [
    "pytest>=8",
    "pytest-cov>=6",
    "httpx>=0.28",
    "ruff>=0.9",
    "ty>=0.0.1",
]

[tool.fastapi]
entrypoint = "app.main:app"

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q"
```

Con `[tool.fastapi]` puedes arrancar simplemente con:

```powershell
uv run fastapi dev
```

### 2.6 Archivos base del repositorio

`.gitignore`:

```gitignore
.venv/
__pycache__/
*.py[cod]
.env
.pytest_cache/
.ruff_cache/
.coverage
htmlcov/
dist/
build/
*.egg-info/
```

`.env.example`:

```dotenv
APP_NAME="FastAPI API"
ENVIRONMENT=local
DEBUG=true

SECRET_KEY=cambia-esta-clave-por-una-larga-y-aleatoria
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

DATABASE_URL=mysql+pymysql://fastapi:fastapi@localhost:3306/fastapi_db?charset=utf8mb4
REDIS_URL=redis://localhost:6379/0

CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
```

> Nunca subas `.env` al repositorio. Genera la clave con:
> `python -c "import secrets; print(secrets.token_urlsafe(64))"`

---

## 3. Estructura de carpetas

```text
fast-api/
├── app/
│   ├── __init__.py
│   ├── main.py                  # Creación de la app, middlewares, routers
│   ├── core/
│   │   ├── config.py            # Settings desde .env
│   │   ├── security.py          # Hash de passwords y JWT
│   │   └── exceptions.py        # Errores de dominio
│   ├── db/
│   │   ├── base.py              # DeclarativeBase + naming conventions
│   │   └── session.py           # Engine, SessionLocal, get_db
│   ├── models/                  # Tablas SQLAlchemy
│   │   ├── __init__.py          # Importa todos los modelos
│   │   ├── user.py
│   │   └── post.py
│   ├── schemas/                 # Pydantic: entrada/salida
│   │   ├── common.py            # Paginación y respuestas comunes
│   │   ├── user.py
│   │   ├── auth.py
│   │   └── post.py
│   ├── repositories/            # Acceso a datos (queries)
│   │   ├── user.py
│   │   └── post.py
│   ├── services/                # Reglas de negocio y transacciones
│   │   ├── user.py
│   │   └── auth.py
│   ├── api/
│   │   ├── deps.py              # Dependencias reutilizables
│   │   └── v1/
│   │       ├── router.py        # Router principal de la v1
│   │       └── endpoints/
│   │           ├── auth.py
│   │           ├── users.py
│   │           └── posts.py
│   └── middleware/
│       └── request_context.py   # Request ID + tiempo de respuesta
├── alembic/
│   └── versions/
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   └── test_users.py
├── alembic.ini
├── pyproject.toml
├── .env.example
├── .gitignore
└── README.md
```

### Responsabilidad de cada capa

| Capa | Responsabilidad | No debe hacer |
|---|---|---|
| `api/endpoints` | Recibir HTTP, validar entrada, devolver salida | Consultas SQL ni reglas de negocio |
| `services` | Reglas de negocio y transacciones | Conocer `Request`/`Response` |
| `repositories` | Consultas y persistencia | Decidir códigos HTTP |
| `models` | Mapeo de tablas | Serialización pública |
| `schemas` | Contratos de entrada/salida | Lógica de negocio |

> **Para empezar** puedes permitir que un endpoint sencillo use el repositorio directamente. Cuando aparezca lógica repetida o varias operaciones por caso de uso, añade el servicio. La estructura ya está preparada.

---

## 4. Configuración con Pydantic Settings

`app/core/config.py`:

```python
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "FastAPI API"
    environment: str = "local"
    debug: bool = False

    secret_key: str = "dev-only-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    database_url: str = "mysql+pymysql://fastapi:fastapi@localhost:3306/fastapi_db?charset=utf8mb4"
    redis_url: str = "redis://localhost:6379/0"

    cors_origins: list[str] = Field(default_factory=list)

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

Uso:

```python
from app.core.config import get_settings

settings = get_settings()
```

`@lru_cache` evita reconstruir la configuración en cada llamada. En tests puedes limpiar la caché con `get_settings.cache_clear()`.

> `pydantic-settings` interpreta las variables de tipo lista como JSON. Por eso `CORS_ORIGINS` va entre corchetes en el `.env`.

---

## 5. Base de datos con SQLAlchemy 2.0

### 5.1 Crear la base de datos en MySQL

```sql
CREATE DATABASE fastapi_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER 'fastapi'@'localhost' IDENTIFIED BY 'fastapi';
GRANT ALL PRIVILEGES ON fastapi_db.* TO 'fastapi'@'localhost';
FLUSH PRIVILEGES;
```

> Si la contraseña tiene caracteres especiales (`@`, `:`, `/`, `#`), codifícala con `urllib.parse.quote_plus` antes de ponerla en `DATABASE_URL`.

### 5.2 `app/db/base.py`

```python
from datetime import datetime

from sqlalchemy import DateTime, MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Nombres predecibles para que Alembic genere migraciones limpias
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
```

> MySQL guarda `DATETIME` sin zona horaria. Configura el servidor en UTC y guarda siempre UTC para evitar ambigüedades.

### 5.3 `app/db/session.py`

```python
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,   # detecta conexiones muertas
    pool_recycle=1800,    # recicla antes del timeout de MySQL
    echo=settings.debug,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise
```

### 5.4 Tipo reutilizable de sesión

`app/api/deps.py`:

```python
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db

SessionDep = Annotated[Session, Depends(get_db)]
```

Así los endpoints quedan limpios:

```python
def list_users(db: SessionDep) -> list[UserRead]:
    ...
```

---

## 6. Migraciones con Alembic

### 6.1 Inicializar

```powershell
uv run alembic init alembic
```

### 6.2 Configurar `alembic/env.py`

Reemplaza la configuración de URL y el `target_metadata`:

```python
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import get_settings
from app.db.base import Base
import app.models  # noqa: F401  # registra todos los modelos en Base.metadata

config = context.config
settings = get_settings()

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", settings.database_url)
target_metadata = Base.metadata
```

Y en `run_migrations_online()` asegúrate de pasar las opciones:

```python
context.configure(
    connection=connection,
    target_metadata=target_metadata,
    compare_type=True,
    compare_server_default=True,
)
```

### 6.3 Flujo de trabajo

```powershell
# 1. Crear/editar modelos
# 2. Generar la migración
uv run alembic revision --autogenerate -m "create users table"

# 3. Revisar SIEMPRE el archivo generado en alembic/versions/
# 4. Aplicar
uv run alembic upgrade head

# 5. Revertir una migración
uv run alembic downgrade -1
```

> **Regla:** nunca uses `Base.metadata.create_all()` en producción. Las tablas se crean y evolucionan con Alembic. `create_all()` solo es aceptable en tests con SQLite.

> **Contraseñas con `%`:** `alembic.ini` usa interpolación de configuración. Si la contraseña de MySQL contiene `%`, escápalo como `%%` o pasa la URL con `settings.database_url.replace("%", "%%")`.

---

## 7. Modelos, schemas y validaciones

### 7.1 Modelo `User`

`app/models/user.py`:

```python
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, false, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.post import Post


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str | None] = mapped_column(String(150))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())

    posts: Mapped[list["Post"]] = relationship(
        back_populates="author",
        cascade="all, delete-orphan",
    )
```

`app/models/__init__.py`:

```python
from app.models.post import Post
from app.models.user import User

__all__ = ["Post", "User"]
```

> Importar todos los modelos aquí es lo que permite que Alembic los descubra. Si todavía no has creado `Post` (Fase 5), importa solo `User` y añade el resto después.

### 7.2 Schemas de usuario

`app/schemas/user.py`:

```python
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = Field(default=None, max_length=150)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = Field(default=None, max_length=150)
    password: str | None = Field(default=None, min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def email_not_null(cls, value: EmailStr | None) -> EmailStr | None:
        if value is None:
            raise ValueError("El email no puede ser nulo")
        return value


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
```

### 7.3 Validaciones personalizadas

Pydantic 2 permite validar reglas de negocio simples. Si tu frontend envía confirmación de contraseña, añade esta variante (o incorpora los validadores a `UserCreate`):

```python
from pydantic import Field, field_validator

# En app/schemas/user.py, después de UserBase


class UserRegister(UserBase):
    password: str = Field(min_length=8, max_length=128)
    password_confirm: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        if not any(c.isdigit() for c in value):
            raise ValueError("La contraseña debe incluir al menos un número")
        return value

    @field_validator("password_confirm")
    @classmethod
    def passwords_match(cls, value: str, info):
        if "password" in info.data and value != info.data["password"]:
            raise ValueError("Las contraseñas no coinciden")
        return value
```

> No uses `...` como valor por defecto. En Pydantic 2 y FastAPI, un campo sin default ya es obligatorio.

### 7.4 Schemas de autenticación

`app/schemas/auth.py`:

```python
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
```

---

## 8. Autenticación JWT

### 8.1 Hash de contraseñas

`app/core/security.py`:

```python
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.core.config import get_settings

settings = get_settings()
password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    payload = {
        "sub": subject,
        "iat": now,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    return jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.jwt_algorithm],
    )
```

### 8.2 Servicio de autenticación

`app/services/auth.py`:

```python
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.security import create_access_token, verify_password
from app.repositories.user import UserRepository
from app.schemas.auth import TokenResponse


class AuthService:
    def __init__(self, db: Session) -> None:
        self.repository = UserRepository(db)

    def login(self, email: str, password: str) -> TokenResponse:
        user = self.repository.get_by_email(email)

        if user is None or not verify_password(password, user.hashed_password):
            raise AppError(
                status_code=401,
                code="invalid_credentials",
                message="Email o contraseña incorrectos",
            )

        if not user.is_active:
            raise AppError(
                status_code=403,
                code="inactive_user",
                message="La cuenta está desactivada",
            )

        settings = get_settings()
        token = create_access_token(subject=str(user.id))
        return TokenResponse(
            access_token=token,
            expires_in=settings.access_token_expire_minutes * 60,
        )
```

### 8.3 Endpoints de registro y login

`app/api/v1/endpoints/auth.py`:

```python
from fastapi import APIRouter, status

from app.api.deps import SessionDep
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserCreate, UserRead
from app.services.auth import AuthService
from app.services.user import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: SessionDep) -> UserRead:
    return UserService(db).create(payload)


@router.post("/login")
def login(payload: LoginRequest, db: SessionDep) -> TokenResponse:
    return AuthService(db).login(payload.email, payload.password)
```

> **Alternativa con formulario:** si prefieres el botón *Authorize* de Swagger con `OAuth2PasswordRequestForm`, añade `python-multipart` y usa `username` como email. Para un frontend React, el login JSON de arriba es más cómodo.

### 8.4 Proteger rutas

`app/api/deps.py`:

```python
from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User

SessionDep = Annotated[Session, Depends(get_db)]

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    db: SessionDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User:
    if credentials is None:
        raise AppError(
            status_code=401,
            code="not_authenticated",
            message="Falta el token de acceso",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(credentials.credentials)
    except jwt.ExpiredSignatureError:
        raise AppError(401, "token_expired", "El token ha expirado") from None
    except jwt.InvalidTokenError:
        raise AppError(401, "invalid_token", "Token inválido") from None

    if payload.get("type") != "access":
        raise AppError(401, "invalid_token", "Tipo de token inválido")

    subject = payload.get("sub")
    if subject is None or not str(subject).isdigit():
        raise AppError(401, "invalid_token", "Token inválido")

    user = db.get(User, int(subject))
    if user is None:
        raise AppError(401, "invalid_token", "Usuario no encontrado")

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_active_user(current_user: CurrentUser) -> User:
    if not current_user.is_active:
        raise AppError(403, "inactive_user", "La cuenta está desactivada")
    return current_user


ActiveUser = Annotated[User, Depends(get_current_active_user)]


def require_superuser(current_user: ActiveUser) -> User:
    if not current_user.is_superuser:
        raise AppError(403, "forbidden", "No tienes permisos para esta acción")
    return current_user


SuperuserDep = Annotated[User, Depends(require_superuser)]
```

Uso:

```python
@router.get("/me")
def read_me(current_user: CurrentUser) -> UserRead:
    return current_user
```

> El token viaja como `Authorization: Bearer <token>`. En Swagger, pulsa **Authorize** y pega solo el token.

> **Refresh tokens (siguiente paso):** añade un token con `type="refresh"`, expiración más larga y un endpoint `/auth/refresh` que valide ese tipo. Para revocarlos, guarda su `jti` en Redis o en una tabla de sesiones.

---

## 9. Dependencias, permisos y middleware

### 9.1 Dependencias: la idea clave

Una dependencia es una función que FastAPI ejecuta antes de tu endpoint y cuyo resultado inyecta como parámetro. Sirve para:

- Sesión de base de datos
- Usuario autenticado
- Permisos
- Paginación
- Servicios compartidos

Siempre usa `Annotated`:

```python
from typing import Annotated
from fastapi import Depends


def get_pagination(page: int = 1, size: int = 20) -> dict:
    return {"page": page, "size": size}


PaginationDep = Annotated[dict, Depends(get_pagination)]
```

### 9.2 Permisos por endpoint

```python
@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: int, db: SessionDep, _: SuperuserDep) -> None:
    UserService(db).delete(user_id)
```

### 9.3 Permisos por router

Si todo un router requiere autenticación:

```python
router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(get_current_active_user)],
)
```

### 9.4 Middleware para concerns transversales

Los middlewares son para cosas que aplican a **todas** las peticiones: request ID, logging, CORS, timing, compresión. **No** los uses para permisos por ruta.

`app/middleware/request_context.py`:

```python
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.2f}"
        return response
```

Registro en `main.py`:

```python
app.add_middleware(RequestContextMiddleware)
```

> El orden importa: el último middleware añadido es el primero en ejecutarse.

### 9.5 CORS para React

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

> Con `allow_credentials=True` no puedes usar `allow_origins=["*"]`. Declara los orígenes exactos.

---

## 10. CRUD de usuarios

### 10.1 Repositorio

`app/repositories/user.py`:

```python
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email.lower()))

    def create(self, payload: UserCreate, hashed_password: str) -> User:
        user = User(
            email=payload.email.lower(),
            full_name=payload.full_name,
            hashed_password=hashed_password,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(self, user: User, payload: UserUpdate) -> User:
        data = payload.model_dump(exclude_unset=True, exclude={"password"})
        if data.get("email"):
            data["email"] = data["email"].lower()
        for field, value in data.items():
            setattr(user, field, value)
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete(self, user: User) -> None:
        self.db.delete(user)
        self.db.commit()
```

### 10.2 Servicio

`app/services/user.py`:

```python
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.core.security import hash_password
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate, UserRead, UserUpdate


class UserService:
    def __init__(self, db: Session) -> None:
        self.repository = UserRepository(db)

    def get_or_404(self, user_id: int) -> User:
        user = self.repository.get(user_id)
        if user is None:
            raise AppError(404, "user_not_found", "Usuario no encontrado")
        return user

    def create(self, payload: UserCreate) -> UserRead:
        if self.repository.get_by_email(payload.email) is not None:
            raise AppError(409, "email_already_exists", "El email ya está registrado")

        try:
            user = self.repository.create(payload, hash_password(payload.password))
        except IntegrityError:
            # Protege contra dos registros simultáneos con el mismo email
            raise AppError(409, "email_already_exists", "El email ya está registrado") from None

        return UserRead.model_validate(user)

    def update(self, user_id: int, payload: UserUpdate) -> UserRead:
        user = self.get_or_404(user_id)

        new_email = payload.email.lower() if payload.email else None
        if new_email and new_email != user.email:
            existing = self.repository.get_by_email(new_email)
            if existing is not None:
                raise AppError(409, "email_already_exists", "El email ya está registrado")

        if payload.password:
            user.hashed_password = hash_password(payload.password)

        user = self.repository.update(user, payload)
        return UserRead.model_validate(user)

    def delete(self, user_id: int) -> None:
        user = self.get_or_404(user_id)
        self.repository.delete(user)
```

### 10.3 Endpoints

`app/api/v1/endpoints/users.py`:

```python
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.deps import ActiveUser, SessionDep, SuperuserDep
from app.core.exceptions import AppError
from app.schemas.common import Page
from app.schemas.user import UserCreate, UserFilters, UserRead, UserUpdate
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
def read_me(current_user: ActiveUser) -> UserRead:
    return current_user


@router.get("")
def list_users(
    db: SessionDep,
    _: ActiveUser,
    filters: Annotated[UserFilters, Query()],
) -> Page[UserRead]:
    return UserService(db).list(filters)


@router.get("/{user_id}")
def read_user(user_id: int, db: SessionDep, _: ActiveUser) -> UserRead:
    return UserService(db).get_or_404(user_id)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: SessionDep,
    _: SuperuserDep,
) -> UserRead:
    return UserService(db).create(payload)


@router.patch("/{user_id}")
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: SessionDep,
    current_user: ActiveUser,
) -> UserRead:
    if user_id != current_user.id and not current_user.is_superuser:
        raise AppError(403, "forbidden", "Solo puedes editar tu propio perfil")
    return UserService(db).update(user_id, payload)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: SessionDep, _: SuperuserDep) -> None:
    UserService(db).delete(user_id)
```

> `UserFilters` se define en la sección de paginación.

> **Primer superusuario:** como `POST /users` exige `SuperuserDep`, crea el primero con un script de seed o desde una consola de Python. Por ejemplo: `UserService(db).create(UserCreate(email="admin@example.com", password="cambiar123"))` y luego marca `is_superuser = True`.

### 10.4 Router principal

`app/api/v1/router.py`:

```python
from fastapi import APIRouter

from app.api.v1.endpoints import auth, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)

# Cuando implementes la Fase 5:
# from app.api.v1.endpoints import posts
# api_router.include_router(posts.router)
```

---

## 11. Relaciones entre tablas

Ejemplo: un usuario tiene muchos posts.

`app/models/post.py`:

```python
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class Post(Base, TimestampMixin):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    content: Mapped[str] = mapped_column(Text)
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )

    author: Mapped["User"] = relationship(back_populates="posts")
```

Puntos importantes:

- `ForeignKey` define la relación en la base de datos.
- `relationship` la define a nivel de ORM.
- `back_populates` conecta ambos lados.
- `ondelete="CASCADE"` en la FK y `cascade="all, delete-orphan"` en la relación mantienen el comportamiento coherente.
- `TYPE_CHECKING` evita importaciones circulares.

### Relación muchos-a-muchos (roles)

Para permisos más finos, el patrón es una tabla asociativa:

```python
from sqlalchemy import Column, ForeignKey, Table

user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)


class User(Base):
    # ...
    roles: Mapped[list[Role]] = relationship(secondary=user_roles, lazy="selectin")
```

Con `lazy="selectin"` evitas el problema N+1 al cargar permisos en cada petición.

### Eager loading explícito

Para devolver un post con su autor:

```python
from sqlalchemy.orm import joinedload

post = db.scalar(
    select(Post).options(joinedload(Post.author)).where(Post.id == post_id)
)
```

> Evita `lazy="joined"` global. Sé explícito según el caso de uso.

---

## 12. Paginación, filtros y búsqueda

### 12.1 Schemas comunes

`app/schemas/common.py`:

```python
from math import ceil
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PageParams(BaseModel):
    page: int = Field(default=1, ge=1, description="Número de página")
    size: int = Field(default=20, ge=1, le=100, description="Elementos por página")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int
    pages: int

    @classmethod
    def build(cls, items: list[T], total: int, params: PageParams) -> "Page[T]":
        return cls(
            items=items,
            total=total,
            page=params.page,
            size=params.size,
            pages=ceil(total / params.size) if total else 0,
        )
```

### 12.2 Filtros como modelo de query

`app/schemas/user.py`:

```python
from typing import Literal

from pydantic import Field

from app.schemas.common import PageParams


class UserFilters(PageParams):
    q: str | None = Field(default=None, min_length=1, max_length=100)
    is_active: bool | None = None
    sort_by: Literal["id", "email", "created_at"] = "id"
    order: Literal["asc", "desc"] = "asc"
```

FastAPI convierte este modelo en parámetros de query automáticamente. El endpoint de la sección 10.3 ya lo usa con `Annotated[UserFilters, Query()]`.

### 12.3 Consulta con filtros y paginación

En `UserRepository`:

```python
from sqlalchemy import asc, desc, func, or_, select

from app.schemas.user import UserFilters

# Añade este método dentro de class UserRepository


def list(self, filters: UserFilters) -> tuple[list[User], int]:
    conditions = []

    if filters.q:
        pattern = f"%{filters.q}%"
        conditions.append(
            or_(User.email.ilike(pattern), User.full_name.ilike(pattern))
        )
    if filters.is_active is not None:
        conditions.append(User.is_active == filters.is_active)

    total = self.db.scalar(
        select(func.count()).select_from(User).where(*conditions)
    ) or 0

    sort_column = getattr(User, filters.sort_by)
    order_by = asc(sort_column) if filters.order == "asc" else desc(sort_column)

    items = list(
        self.db.scalars(
            select(User)
            .where(*conditions)
            .order_by(order_by)
            .offset((filters.page - 1) * filters.size)
            .limit(filters.size)
        ).all()
    )
    return items, total
```

Y en el servicio:

```python
from app.schemas.common import Page
from app.schemas.user import UserFilters, UserRead

# Añade este método dentro de class UserService


def list(self, filters: UserFilters) -> Page[UserRead]:
    items, total = self.repository.list(filters)
    return Page.build(
        items=[UserRead.model_validate(user) for user in items],
        total=total,
        params=filters,
    )
```

> `ilike` funciona en MySQL porque el collation por defecto es case-insensitive. Si usas un collation `_bin` o `_cs`, normaliza con `func.lower()`.

### 12.4 Búsqueda full-text (siguiente nivel)

Para tablas grandes, un `LIKE '%texto%'` no usa índices. Opciones:

- Índice `FULLTEXT` en MySQL y `MATCH ... AGAINST`.
- Meilisearch o Typesense para búsqueda real.
- Elasticsearch/OpenSearch si ya forma parte de la infraestructura.

Empieza simple y mide antes de optimizar.

---

## 13. Manejo de errores

### 13.1 Error de dominio

`app/core/exceptions.py`:

```python
from typing import Any


class AppError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: Any = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details
        self.headers = headers
        super().__init__(message)
```

### 13.2 Handlers globales

`app/core/error_handlers.py`:

```python
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import AppError


def error_body(code: str, message: str, details=None) -> dict:
    return {"error": {"code": code, "message": message, "details": details}}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(exc.code, exc.message, exc.details),
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        _: Request, exc: RequestValidationError
    ) -> JSONResponse:
        details = [
            {
                "field": ".".join(str(part) for part in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
            for error in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=error_body("validation_error", "Datos inválidos", details),
        )

    @app.exception_handler(IntegrityError)
    async def handle_integrity_error(_: Request, __: IntegrityError) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content=error_body("conflict", "El recurso entra en conflicto con datos existentes"),
        )
```

Respuesta de error uniforme:

```json
{
  "error": {
    "code": "user_not_found",
    "message": "Usuario no encontrado",
    "details": null
  }
}
```

> Un contrato de error estable es tan importante como el contrato de éxito: el frontend puede reaccionar por `code`, no por el texto del mensaje.

### 13.3 No filtrar detalles internos

Nunca devuelvas `str(exc)` de errores de base de datos al cliente. Registra el error completo en logs y devuelve un mensaje genérico.

---

## 14. Pruebas automatizadas

### 14.1 `tests/conftest.py`

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401  # registra los modelos
from app.db.base import Base
from app.db.session import get_db
from app.main import app

engine = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def db():
    with TestingSessionLocal() as session:
        yield session


@pytest.fixture
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
```

### 14.2 `tests/test_auth.py`

```python
def test_register_and_login(client):
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "ana@example.com",
            "password": "secreto123",
            "full_name": "Ana",
        },
    )
    assert register_response.status_code == 201
    assert register_response.json()["email"] == "ana@example.com"
    assert "hashed_password" not in register_response.json()

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "ana@example.com", "password": "secreto123"},
    )
    assert login_response.status_code == 200
    assert login_response.json()["token_type"] == "bearer"


def test_login_with_wrong_password(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "ana@example.com", "password": "secreto123"},
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "ana@example.com", "password": "incorrecta"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_credentials"
```

### 14.3 `tests/test_users.py`

```python
def auth_headers(client, email="ana@example.com", password="secreto123"):
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_read_me(client):
    headers = auth_headers(client)
    response = client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == "ana@example.com"


def test_read_me_without_token(client):
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "not_authenticated"
```

### 14.4 SQLite vs MySQL en tests

SQLite es rápido y suficiente para la mayoría de tests de API, pero no reproduce:

- Tipos específicos de MySQL
- Restricciones y collations
- Comportamiento de transacciones y locks
- `FULLTEXT`

Para tests de integración reales, usa **Testcontainers** con MySQL o una base de datos de test dedicada.

### 14.5 Ejecutar

```powershell
uv run pytest
uv run pytest -k auth -v
uv run pytest --cov=app
```

---

## 15. Redis: caché y tareas

Redis entra cuando la API ya funciona. Casos típicos:

| Caso | Patrón |
|---|---|
| Caché de lecturas | Cache-aside con TTL |
| Rate limiting | Contador por IP/usuario |
| Sesiones/revocación de tokens | Lista negra de `jti` |
| Colas de tareas | `arq`, `rq` o Celery |
| Datos efímeros | Verificación de email, reset de password |

Cliente síncrono (coherente con SQLAlchemy síncrono):

`app/core/redis.py`:

```python
from redis import Redis

from app.core.config import get_settings

redis = Redis.from_url(get_settings().redis_url, decode_responses=True)
```

En el `lifespan` de `main.py`:

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.redis import redis
from app.db.session import engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    redis.close()
    engine.dispose()
```

Ejemplo de caché en un endpoint síncrono:

```python
from app.core.redis import redis


@router.get("/{user_id}")
def read_user(user_id: int, db: SessionDep) -> UserRead:
    cache_key = f"user:{user_id}"
    cached = redis.get(cache_key)
    if cached:
        return UserRead.model_validate_json(cached)

    user = UserService(db).get_or_404(user_id)
    result = UserRead.model_validate(user)
    redis.set(cache_key, result.model_dump_json(), ex=60)
    return result
```

Invalida la caché al actualizar o borrar:

```python
redis.delete(f"user:{user_id}")
```

> Si algún día migras a SQLAlchemy async, usa `redis.asyncio` y `await redis.aclose()`. No mezcles I/O bloqueante dentro de `async def`: si necesitas combinar ambos mundos, usa `run_sync` de Asyncer.

---

## 16. Roadmap por fases

### Fase 0 — Base del proyecto

- [ ] Crear el proyecto con `uv`
- [ ] Configurar `pyproject.toml`, `.env.example`, `.gitignore`
- [ ] Implementar `Settings` con `pydantic-settings`
- [ ] Crear `main.py` con `/health` y metadatos OpenAPI
- [ ] Verificar `fastapi dev` y `/docs`

### Fase 1 — Base de datos

- [ ] Crear base de datos MySQL
- [ ] Configurar engine y `get_db`
- [ ] Definir `Base` y `TimestampMixin`
- [ ] Crear modelo `User`
- [ ] Inicializar Alembic y generar la primera migración
- [ ] Aplicar `alembic upgrade head`

### Fase 2 — CRUD de usuarios

- [ ] Schemas `UserCreate`, `UserUpdate`, `UserRead`
- [ ] Repositorio y servicio de usuario
- [ ] Endpoints `GET /users`, `GET /users/{id}`, `POST /users`, `PATCH /users/{id}`, `DELETE /users/{id}`
- [ ] Manejo de errores uniforme
- [ ] Probar todo desde `/docs`

### Fase 3 — Autenticación

- [ ] Hash con Argon2
- [ ] Crear y validar JWT
- [ ] `POST /auth/register`
- [ ] `POST /auth/login`
- [ ] `GET /users/me`
- [ ] Dependencias `CurrentUser`, `ActiveUser`, `SuperuserDep`

### Fase 4 — Permisos y middleware

- [ ] Middleware de request ID y timing
- [ ] CORS para el frontend
- [ ] Restringir endpoints por rol
- [ ] Proteger edición de perfil (solo dueño o superuser)
- [ ] Roles N-N (opcional)

### Fase 5 — Relaciones

- [ ] Modelo `Post` con FK a `User`
- [ ] Endpoints de posts
- [ ] Carga del autor con `joinedload`
- [ ] Reglas: solo el autor o un admin puede editar/borrar

### Fase 6 — Listados profesionales

- [ ] Paginación con `Page[T]`
- [ ] Filtros por estado
- [ ] Búsqueda por email/nombre
- [ ] Ordenamiento validado con `Literal`
- [ ] Índices en columnas filtradas

### Fase 7 — Calidad

- [ ] Tests de auth y usuarios
- [ ] Tests de permisos
- [ ] Cobertura de errores 404/409/422
- [ ] Ruff + ty en CI
- [ ] Logs estructurados con request ID

### Fase 8 — Producción

- [ ] Redis para caché o rate limiting
- [ ] Rate limiting en login
- [ ] Variables de entorno seguras
- [ ] Migraciones en el pipeline de despliegue
- [ ] `fastapi run` detrás de un proxy inverso
- [ ] Health check y métricas
- [ ] Despliegue gestionado opcional: `uv run fastapi deploy` (FastAPI Cloud)

---

## 17. Reglas de oro y convenciones

1. **Un endpoint, una operación HTTP.** No mezcles GET y POST en la misma función.
2. **`def` para SQLAlchemy síncrono.** `async def` solo cuando todo el interior sea async y no bloquee.
3. **Nunca devuelvas modelos ORM directamente.** Usa `UserRead` y `response_model`/tipo de retorno para filtrar campos sensibles.
4. **Nunca expongas `hashed_password`.** El schema de salida no lo incluye.
5. **Valida en los bordes.** Pydantic en entrada; la base de datos como última defensa.
6. **Transacciones fuera del endpoint.** En esta guía el repositorio cierra operaciones simples con `commit`; cuando un caso de uso tenga varias escrituras, mueve el control de la transacción al servicio. Nunca hagas `commit` en el endpoint.
7. **Errores con contrato estable.** Código, mensaje y detalles; el frontend reacciona al `code`.
8. **Migraciones siempre revisadas.** `--autogenerate` es una ayuda, no una verdad absoluta.
9. **Secretos fuera del código.** `.env` local, gestor de secretos en producción.
10. **Índices con intención.** Indexa lo que filtras y ordenas, no todo.
11. **Evita N+1.** Usa `selectinload`/`joinedload` según el caso.
12. **Nombra en inglés el código, documenta en español si el equipo lo necesita.** La consistencia importa más que la preferencia.
13. **Rutas en plural y sustantivos.** `/users`, `/posts`, no `/getUsers`.
14. **Versiona la API.** `/api/v1` desde el primer día.
15. **No optimices sin medir.** Primero correcto, luego rápido.

### Convenciones de nombres

| Elemento | Convención | Ejemplo |
|---|---|---|
| Tablas | snake_case, plural | `users`, `user_roles` |
| Modelos | PascalCase, singular | `User`, `Post` |
| Schemas | `Entidad` + `Create/Update/Read` | `UserCreate`, `UserRead` |
| Endpoints | snake_case | `list_users`, `read_me` |
| Variables de entorno | UPPER_SNAKE_CASE | `DATABASE_URL` |
| Migraciones | verbo + entidad | `create_users_table` |

---

## 18. Comandos útiles

```powershell
# Desarrollo
uv run fastapi dev

# Producción
uv run fastapi run

# Dependencias
uv add <paquete>
uv add --dev <paquete>
uv sync

# Migraciones
uv run alembic revision --autogenerate -m "descripcion"
uv run alembic upgrade head
uv run alembic downgrade -1
uv run alembic history

# Tests
uv run pytest
uv run pytest -k users -v
uv run pytest --cov=app

# Calidad
uv run ruff check .
uv run ruff format .
uv run ty check

# JWT secret
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

### `app/main.py` de referencia

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.error_handlers import register_error_handlers
from app.db.session import engine
from app.middleware.request_context import RequestContextMiddleware

settings = get_settings()

if settings.is_production and settings.secret_key == "dev-only-change-me":
    raise RuntimeError("Configura una SECRET_KEY segura antes de desplegar")


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="API REST profesional con FastAPI",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestContextMiddleware)

register_error_handlers(app)
app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
```

### Docker Compose opcional para MySQL + Redis

`compose.yaml`:

```yaml
services:
  mysql:
    image: mysql:8.4
    environment:
      MYSQL_ROOT_PASSWORD: root
      MYSQL_DATABASE: fastapi_db
      MYSQL_USER: fastapi
      MYSQL_PASSWORD: fastapi
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  mysql_data:
  redis_data:
```

```powershell
docker compose up -d
```

---

## Siguiente paso

Cuando tengas la Fase 0 y la Fase 1 funcionando, el orden más productivo es:

1. **Usuario + migración + CRUD** (sin auth todavía).
2. **Registro/login + JWT**.
3. **Permisos y `/users/me`**.
4. **Relaciones con posts**.
5. **Paginación, filtros y errores uniformes**.
6. **Tests y Redis**.

Con eso tendrás una base real, no un ejemplo de tutorial: capas separadas, migraciones versionadas, contrato de errores estable y autenticación lista para un frontend React.
