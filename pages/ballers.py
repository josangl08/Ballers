# pages/ballers.py
import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL
from models.player_model import Player
from models.session_model import Session, SessionStatus
from models.test_model import TestResult
import matplotlib.pyplot as plt

# Conexión a la base de datos
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def show():
    st.title("Ballers - Perfiles de Jugadores")
    with SessionLocal() as db:
        # Para jugadores, sólo su propio perfil; sino, lista completa
        if st.session_state['user_type'] == 'player':
            players = db.query(Player).filter_by(user_id=st.session_state['user_id']).all()
        else:
            players = db.query(Player).all()
        names = [p.user.name for p in players]
    # Selección de jugador (los jugadores verán por defecto su nombre)
    selected = st.selectbox("Selecciona un jugador", names)
    if not selected:
        return

    # Obtener detalle de player
    with SessionLocal() as db:
        if st.session_state['user_type'] == 'player':
            p = db.query(Player).filter_by(user_id=st.session_state['user_id']).first()
        else:
            p = db.query(Player).join(Player.user).filter(Player.user.has(name=selected)).first()

    if not p:
        st.error("Jugador no encontrado")
        return

    # Datos personales y físicos
    st.subheader("Datos Personales y Físicos")
    st.write({
        "Nombre": p.user.name,
        "Email": p.user.email,
        "Teléfono": p.user.phone,
        "Fecha Nacimiento": p.user.date_of_birth,
        # Asumiendo que peso y altura se guardan en atributos adicionales
        **({"Peso": getattr(p, "weight", None), "Altura": getattr(p, "height", None)})
    })

    # Datos de servicio
    st.subheader("Datos de Servicio")
    st.write({"Servicio": p.service, "Sesiones inscritas": p.enrolment, "Notas": p.notes})

    # Resultados de tests y gráfica de progresión
    st.subheader("Resultados de Tests y Progresión")
    tests = db.query(TestResult).filter_by(player_id=p.player_id).all()
    if tests:
        # Tabla de resultados
        for t in tests:
            st.write(f"{t.date.date()} - {t.test_name}: {t.value}")
        # Gráfica de ejemplo: evolución de un test (p.ej., sprint)
        dates = [t.date for t in tests if t.test_name == 'sprint']
        values = [t.sprint for t in tests if t.test_name == 'sprint']
        if dates and values:
            plt.figure()
            plt.plot(dates, values)
            plt.title('Progresión Sprint')
            plt.xlabel('Fecha')
            plt.ylabel('Tiempo (s)')
            st.pyplot(plt)
    else:
        st.write("No hay resultados de tests para este jugador.")

    # Calendario de sesiones
    st.subheader("Sesiones de Entrenamiento")
    sessions = db.query(Session).filter_by(player_id=p.player_id).all()
    for s in sessions:
        st.write(f"{s.start_time} - {s.status.value}")