# data/seed_db.py
from __future__ import annotations
# ─── PYTHONPATH raíz ─────────────────────────────────────────
import sys, pathlib, random
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))


from datetime import datetime, timedelta, timezone
from faker import Faker      
import bcrypt
from sqlalchemy   import create_engine
from sqlalchemy.orm import sessionmaker

from config                   import DATABASE_URL
from models.base              import Base
from models.user_model        import User, UserType
from models.coach_model       import Coach
from models.player_model      import Player
from models.session_model     import Session, SessionStatus
from models.test_model        import TestResult


fake = Faker("es_ES")
rng  = random.Random(42)          # semilla reproducible

engine       = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


# ─────────────────────────────────────────────────────────────
def hash_pw(clear: str) -> str:
    return bcrypt.hashpw(clear.encode(), bcrypt.gensalt()).decode()


def create_coaches(sess) -> list[Coach]:
    licenses = ["UEFA Pro", "UEFA A", "UEFA B", "UEFA C", "Diploma Nacional"]
    coaches: list[Coach] = []

    for i in range(5):
        user = User(
            username      = f"coach{i+1}",
            name          = fake.name(),
            password_hash = hash_pw("coachpass"),
            email         = f"coach{i+1}@ballers.com",
            phone         = fake.phone_number(),
            user_type     = UserType.coach,
            permit_level  = 5,
        )
        sess.add(user)
        sess.flush()                       # obtiene user_id

        coach = Coach(user_id=user.user_id, license=rng.choice(licenses))
        sess.add(coach)
        coaches.append(coach)

    return coaches


def create_players(sess) -> list[Player]:
    services = ["Individual", "Grupo reducido", "Plan fuerza", "Plan técnico"]

    players: list[Player] = []
    for i in range(20):
        user = User(
            username      = f"player{i+1}",
            name          = fake.name(),
            password_hash = hash_pw("playerpass"),
            email         = f"player{i+1}@ballers.com",
            phone         = fake.phone_number(),
            user_type     = UserType.player,
            permit_level  = 1,
        )
        sess.add(user)
        sess.flush()

        player = Player(
            user_id   = user.user_id,
            service   = rng.choice(services),
            enrolment = rng.randint(10, 30),
            notes     = fake.sentence(nb_words=8),
        )
        sess.add(player)
        sess.flush()
        players.append(player)

    return players


def create_sessions(sess, players: list[Player], coaches: list[Coach]) -> None:
    now = datetime.now(timezone.utc)

    def random_date() -> datetime:
        bucket = rng.choice(["past", "present", "future"])
        if bucket == "past":
            base = now - timedelta(days=30)
        elif bucket == "future":
            base = now + timedelta(days=30)
        else:
            base = now
        shift = timedelta(days=rng.randint(0, 29),
                          hours=rng.randint(6, 20),
                          minutes=rng.choice([0, 30]))
        return (base + shift).replace(tzinfo=timezone.utc)

    status_pool = (
        [SessionStatus.CANCELED]   * 10 +
        [SessionStatus.SCHEDULED]  * 40 +
        [SessionStatus.COMPLETED]  * 50
    )

    for _ in range(100):
        player = rng.choice(players)
        coach  = rng.choice(coaches)
        start  = random_date()
        end    = start + timedelta(hours=1)

        sess.add(Session(
            coach_id   = coach.coach_id,
            player_id  = player.player_id,
            start_time = start,
            end_time   = end,
            status     = rng.choice(status_pool),
            notes      = fake.sentence(nb_words=6),
        ))


def create_tests(sess, players: list[Player]) -> None:
    for p in players:
        n_tests = rng.randint(3, 4)
        base_date = datetime.now(timezone.utc) - timedelta(days=90)
        sprint    = rng.uniform(5.0, 6.0)           # peor tiempo primero

        for k in range(n_tests):
            date = base_date + timedelta(days=k*30 + rng.randint(0,5))
            sprint -= rng.uniform(0.05, 0.15)       # mejora progresiva

            sess.add(TestResult(
                player_id      = p.player_id,
                test_name      = "battery",
                date           = date,
                weight         = rng.randint(60, 90),
                height         = rng.randint(160, 200),
                ball_control   = rng.uniform(6, 10),
                control_pass   = rng.uniform(6, 10),
                receive_scan   = rng.uniform(6, 10),
                dribling_carriying = rng.uniform(6, 10),
                shooting       = rng.uniform(6, 10),
                crossbar       = rng.randint(0, 10),
                sprint         = round(sprint, 2),
                t_test         = rng.uniform(9, 11),
                jumping        = rng.uniform(40, 55),
            ))


# ─────────────────────────────────────────────────────────────
def seed():
    Base.metadata.create_all(engine)   # por si no se han creado

    with SessionLocal() as sess:
        # Evitar duplicados si ejecutas varias veces
        if sess.query(Player).count() > 0:
            print("La BD ya contiene datos; abortando.")
            return

        coaches  = create_coaches(sess)
        players  = create_players(sess)

        create_sessions(sess, players, coaches)
        create_tests(sess, players)

        sess.commit()
        print("BD rellenada con datos ficticios ✔︎")


if __name__ == "__main__":
    seed()
