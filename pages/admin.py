import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from controllers.db_controller import get_session_local
from common.services.session_service import SessionService
from controllers.sheets_controller import get_financials
from models.coach_model import Coach
from models.player_model import Player
from models.user_model import User
from models.session_model import Session, SessionStatus

# Conexión a BD
SessionLocal = get_session_local()

def show():
    st.title("Administración")
    user_type = st.session_state['user_type']

    if user_type == 'admin':
        st.subheader("📊 Dashboard General")

        with SessionLocal() as db:
            total_players = db.query(Player).count()
            total_coaches = db.query(Coach).count()
            now = datetime.now()
            start_of_month = now.replace(day=1)
            start_of_week = now - timedelta(days=now.weekday())

            sessions_month = db.query(Session).filter(Session.start_time >= start_of_month).count()
            sessions_week = db.query(Session).filter(Session.start_time >= start_of_week).count()

        df_financial = get_financials()

        ingresos_mensuales = df_financial['Ingresos'].sum() if 'Ingresos' in df_financial.columns else 0
        gastos_mensuales = df_financial['Gastos'].sum() if 'Gastos' in df_financial.columns else 0

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🏃‍♂️ Jugadores", f"{total_players}")
            st.metric("🎯 Coaches", f"{total_coaches}")
        with col2:
            st.metric("📅 Sesiones Mes", f"{sessions_month}")
            st.metric("📆 Sesiones Semana", f"{sessions_week}")
        with col3:
            st.metric("📈 Ingresos (€)", f"{ingresos_mensuales:,.2f} €")
            st.metric("📉 Gastos (€)", f"{gastos_mensuales:,.2f} €")

    # Pestañas para navegar entre las secciones
    tabs = []
    if user_type == 'admin':
        tabs = ["Ver sesiones/CRUD sesiones", "Informe Financiero", "Usuarios"]
    elif user_type == 'coach':
        tabs = ["Mis sesiones"]

    selected_tab = st.selectbox("Selecciona una opción:", tabs)

    with SessionLocal() as db:

        if selected_tab == "Ver sesiones/CRUD sesiones" and user_type == 'admin':
            st.subheader("Gestión de Sesiones (Admin)")
            all_sessions = db.query(Session).all()
            for s in all_sessions:
                st.write(f"ID {s.id}: Coach {s.coach_id} - Jugador {s.player_id} | {s.start_time} - {s.end_time} [{s.status.value}]")
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button(f"Completar {s.id}"):
                        SessionService.update(db, s.id, status=SessionStatus.COMPLETED)
                        st.experimental_rerun()
                with col2:
                    if st.button(f"Cancelar {s.id}"):
                        SessionService.update(db, s.id, status=SessionStatus.CANCELED)
                        st.experimental_rerun()
                with col3:
                    if st.button(f"Eliminar {s.id}"):
                        SessionService.delete(db, s.id)
                        st.experimental_rerun()

        elif selected_tab == "Mis sesiones" and user_type == 'coach':
            st.subheader("Mis Sesiones (Coach)")
            coach = db.query(Coach).filter_by(user_id=st.session_state['user_id']).first()
            if coach:
                sess_list = db.query(Session).filter_by(coach_id=coach.coach_id).all()
                for s in sess_list:
                    st.write(f"ID {s.id}: {s.start_time} - {s.end_time} [{s.status.value}]")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button(f"Completar {s.id}"):
                            SessionService.update(db, s.id, status=SessionStatus.COMPLETED)
                            st.experimental_rerun()
                    with col2:
                        if st.button(f"Cancelar {s.id}"):
                            SessionService.update(db, s.id, status=SessionStatus.CANCELED)
                            st.experimental_rerun()
                    with col3:
                        if st.button(f"Eliminar {s.id}"):
                            SessionService.delete(db, s.id)
                            st.experimental_rerun()
            else:
                st.error("Perfil de coach no encontrado.")

        elif selected_tab == "Informe Financiero" and user_type == 'admin':
            st.subheader("Informe Financiero (Google Sheets)")
            df = get_financials()
            st.dataframe(df)

        elif selected_tab == "Usuarios" and user_type == 'admin':
            st.subheader("Gestión de Usuarios")
            users = db.query(User).all()
            if users:
                user_data = []
                for user in users:
                    user_data.append({
                        "ID": user.user_id,
                        "Username": user.username,
                        "Nombre": user.name,
                        "Email": user.email,
                        "Teléfono": user.phone,
                        "Fecha Nacimiento": user.date_of_birth,
                        "Tipo Usuario": user.user_type.value,
                        "Nivel Permiso": user.permit_level
                    })
                df_users = pd.DataFrame(user_data)
                st.dataframe(df_users, use_container_width=True)
            else:
                st.write("No hay usuarios registrados.")
