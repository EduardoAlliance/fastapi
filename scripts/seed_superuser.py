import argparse
import getpass

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User


def seed_superuser(email: str, password: str, full_name: str | None = None) -> None:
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email.lower()))

        if user is None:
            user = User(
                email=email.lower(),
                hashed_password=hash_password(password),
                full_name=full_name,
                is_active=True,
                is_superuser=True,
            )
            db.add(user)
            action = "creado"
        else:
            user.is_active = True
            user.is_superuser = True
            user.hashed_password = hash_password(password)
            if full_name is not None:
                user.full_name = full_name
            action = "actualizado"

        db.commit()
        db.refresh(user)
        print(f"Superusuario {action}: {user.email} (id={user.id})")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Crea o actualiza un superusuario en la base de datos",
    )
    parser.add_argument("--email", required=True, help="Email del superusuario")
    parser.add_argument(
        "--password",
        help="Contraseña. Si se omite, se solicita de forma interactiva",
    )
    parser.add_argument("--full-name", default=None, help="Nombre completo opcional")
    args = parser.parse_args()

    password = args.password or getpass.getpass("Contraseña: ")
    if len(password) < 8:
        parser.error("La contraseña debe tener al menos 8 caracteres")

    seed_superuser(args.email, password, args.full_name)


if __name__ == "__main__":
    main()
