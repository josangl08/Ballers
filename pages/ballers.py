import streamlit as st
from controllers.db_controller import get_session_local
from datetime import datetime
from config import DATABASE_URL
from models.player_model import Player
from models.test_model import TestResult
from common.services.session_service import SessionService  # Importamos la nueva clase del servicio
import matplotlib.pyplot as plt

# Conexión a BD
SessionLocal = get_session_local()

def show():
    st.title("Ballers - Perfiles de Jugadores")

    # Filtrar lista de jugadores según rol
    with SessionLocal() as db:
        if st.session_state['user_type'] == 'player':
            players = db.query(Player).filter_by(user_id=st.session_state['user_id']).all()
        else:
            players = db.query(Player).all()
        names = [p.user.name for p in players]

    selected = st.selectbox("Selecciona un jugador", names)
    if not selected:
        return

    with SessionLocal() as db:
        if st.session_state['user_type'] == 'player':
            p = db.query(Player).filter_by(user_id=st.session_state['user_id']).first()
        else:
            p = (db.query(Player)
                 .join(Player.user)
                 .filter(Player.user.has(name=selected))
                 .first())
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
        **({"Peso": getattr(p, "weight", None), "Altura": getattr(p, "height", None)})  
    })

    # Datos de servicio
    st.subheader("Datos de Servicio")
    st.write({"Servicio": p.service, "Sesiones inscritas": p.enrolment, "Notas": p.notes})

    # Tests y progresión
    st.subheader("Resultados de Tests y Progresión")
    tests = db.query(TestResult).filter_by(player_id=p.player_id).all()
    if tests:
        for t in tests:
            st.write(f"{t.date.date()} - {t.test_name}: {getattr(t, t.test_name, t.value)}")
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
    st.subheader("Sesiones de Entrenamiento (Calendario)")
    events = SessionService.list_for_player(p.user.email)  # Usamos el servicio para obtener las sesiones
    if events:
        for e in events:
            start = e['start'].get('dateTime', e['start'].get('date'))
            status = e.get('status', 'confirmed')
            st.write(f"{start} - {status}")
    else:
        st.write("No hay sesiones en el calendario.")
