# pages/admin.py
import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import DATABASE_URL
from models.coach_model import Coach
from models.player_model import Player
from models.session_model import Session, SessionStatus
from controllers.session_controller import create_session, update_session, delete_session
from controllers.calendar_controller import list_sessions_for_coach
from controllers.sheets_controller import get_financials

# Conexión a BD
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def show():
    st.title("Administración")
    user_type = st.session_state['user_type']

    # 1) Formulario de creación de sesiones (solo admin)
    if user_type == 'admin':
        st.subheader("Crear nueva sesión")
        with SessionLocal() as db:
            coaches = db.query(Coach).all()
            players = db.query(Player).all()
        coach_opts = {f"{c.user.name} (ID: {c.coach_id})": c.coach_id for c in coaches}
        player_opts = {f"{p.user.name} (ID: {p.player_id})": p.player_id for p in players}
        sel_coach = st.selectbox("Selecciona Coach", list(coach_opts.keys()))
        sel_player = st.selectbox("Selecciona Jugador", list(player_opts.keys()))
        start = st.datetime_input("Inicio de sesión", value=datetime.now())
        end = st.datetime_input("Fin de sesión", value=datetime.now())
        if st.button("Crear sesión"):
            new_sess, event_id = create_session(
                player_id=player_opts[sel_player],
                coach_id=coach_opts[sel_coach],
                start_time=start,
                end_time=end
            )
            st.success(f"Sesión creada (ID DB: {new_sess.id}, ID Calendar: {event_id})")

    # 2) Sección para coaches: ver y gestionar sus propias sesiones
    with SessionLocal() as db:
        if user_type == 'coach':
            st.subheader("Mi Perfil - Coach")
            coach = db.query(Coach).filter_by(user_id=st.session_state['user_id']).first()
            if coach:
                st.write({
                    "Nombre": coach.user.name,
                    "Email": coach.user.email,
                    "Licencia": coach.license
                })
                st.subheader("Mis Sesiones (Local DB)")
                sess_list = db.query(Session).filter_by(coach_id=coach.coach_id).all()
                for s in sess_list:
                    st.write(f"ID {s.id}: {s.start_time} - {s.end_time} [{s.status.value}]")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button(f"Completar {s.id}"):
                            update_session(s.id, status=SessionStatus.COMPLETED)
                            st.experimental_rerun()
                    with col2:
                        if st.button(f"Cancelar {s.id}"):
                            update_session(s.id, status=SessionStatus.CANCELED)
                            st.experimental_rerun()
                    with col3:
                        if st.button(f"Eliminar {s.id}"):
                            delete_session(s.id)
                            st.experimental_rerun()
            else:
                st.error("Perfil de coach no encontrado.")
        # 3) Sección para admins: gestión total de sesiones e informe financiero
        elif user_type == 'admin':
            st.subheader("Gestión de Sesiones (Local DB)")
            with SessionLocal() as db:
                all_sessions = db.query(Session).all()
            for s in all_sessions:
                st.write(f"ID {s.id}: Coach {s.coach_id} - Jugador {s.player_id} | "
                         f"{s.start_time} - {s.end_time} [{s.status.value}]")
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button(f"Completar {s.id}"):
                        update_session(s.id, status=SessionStatus.COMPLETED)
                        st.experimental_rerun()
                with col2:
                    if st.button(f"Cancelar {s.id}"):
                        update_session(s.id, status=SessionStatus.CANCELED)
                        st.experimental_rerun()
                with col3:
                    if st.button(f"Eliminar {s.id}"):
                        delete_session(s.id)
                        st.experimental_rerun()

            st.subheader("Informe Financiero")
            df = get_financials()
            st.dataframe(df)
        else:
            st.error("No tienes permiso para acceder a esta sección.")
