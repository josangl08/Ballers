# init_db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.user_model import Base, User, UserType
from models.admin_model import Admin
from models.coach_model import Coach
from models.player_model import Player
from models.session_model import Session, SessionStatus
from models.test_model import TestResult
from config import DATABASE_URL
import bcrypt


def init_db():
    # Crear motor y sesiones
    engine = create_engine(DATABASE_URL, echo=True)
    SessionLocal = sessionmaker(bind=engine)

    # Crear todas las tablas definidas en Base
    Base.metadata.create_all(engine)

    # Inicializar datos por defecto
    with SessionLocal() as session:
        # Crear usuario admin si no existe
        admin_user = session.query(User).filter_by(username="admin").first()
        if not admin_user:
            # Generar hash de contraseña (por defecto: 'admin123')
            pw = 'admin123'.encode('utf-8')
            pw_hash = bcrypt.hashpw(pw, bcrypt.gensalt()).decode('utf-8')

            admin_user = User(
                username       = "admin",
                name           = "Administrador",
                password_hash  = pw_hash,
                email          = "admin@centro.com",
                phone          = "",
                line           = "",
                user_type      = UserType.ADMIN,
                permit_level   = 10
            )
            session.add(admin_user)
            session.flush()  # Para obtener user_id

            # Crear perfil admin asociado
            admin_profile = Admin(
                user_id = admin_user.user_id,
                role    = "superuser"
            )
            session.add(admin_profile)
            session.commit()

    print("Base de datos inicializada con éxito.")

if __name__ == "__main__":
    init_db()