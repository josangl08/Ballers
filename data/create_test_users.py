# create_test_users.py
from controllers.db_controller import get_session_local
from models.user_model import User
from models.admin_model import Admin
from models.coach_model import Coach
from models.player_model import Player
from datetime import datetime

# Conexión a la base de datos
SessionLocal = get_session_local()

def create_test_users():
    with SessionLocal() as db:
        # ---- Crear Admin ----
        admin_user = User(
            username="admin1",
            name="Admin Uno",
            password_hash="adminpass",  # OJO en real se debe encriptar
            email="admin1@example.com",
            phone="600000001",
            line="admin_line",
            fecha_registro=datetime.now(),
            date_of_birth=datetime(1980, 1, 1),
            user_type="admin",
            permit_level=10
        )
        db.add(admin_user)
        db.flush()  # Obligamos a SQLAlchemy a asignar user_id
        admin_profile = Admin(
            user_id=admin_user.user_id,
            role="Administrador Principal"
        )
        db.add(admin_profile)

        # ---- Crear Coach ----
        coach_user = User(
            username="coach1",
            name="Coach Uno",
            password_hash="coachpass",
            email="coach1@example.com",
            phone="600000002",
            line="coach_line",
            fecha_registro=datetime.now(),
            date_of_birth=datetime(1985, 5, 15),
            user_type="coach",
            permit_level=5
        )
        db.add(coach_user)
        db.flush()
        coach_profile = Coach(
            user_id=coach_user.user_id,
            license="License1234"
        )
        db.add(coach_profile)

        # ---- Crear Player ----
        player_user = User(
            username="player1",
            name="Player Uno",
            password_hash="playerpass",
            email="player1@example.com",
            phone="600000003",
            line="player_line",
            fecha_registro=datetime.now(),
            date_of_birth=datetime(2000, 3, 10),
            user_type="player",
            permit_level=1
        )
        db.add(player_user)
        db.flush()
        player_profile = Player(
            user_id=player_user.user_id,
            service="Fútbol Base",
            enrolment=10,
            notes="Jugador prometedor"
        )
        db.add(player_profile)

        # ---- Confirmar todo junto ----
        db.commit()

    print("✅ Usuarios de prueba creados correctamente.")

if __name__ == "__main__":
    create_test_users()
