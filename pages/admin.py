# pages/admin.py
import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL
from models.coach_model import Coach
from models.session_model import Session
from controllers.sheets_controller import get_financials

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def show():
    st.title("Administración")
    user_type = st.session_state['user_type']

    with SessionLocal() as db:
        if user_type == 'coach':
            # Perfil y sesiones del coach
            coach = db.query(Coach).filter_by(user_id=st.session_state['user_id']).first()
            if coach:
                st.subheader("Mi Perfil - Coach")
                st.write({
                    "Nombre": coach.user.name,
                    "Email": coach.user.email,
                    "Licencia": coach.license
                })
                st.subheader("Mis Sesiones")
                sessions = db.query(Session).filter_by(coach_id=coach.coach_id).all()
                for s in sessions:
                    st.write(f"{s.start_time} - {s.status.value}")
            else:
                st.error("Perfil de coach no encontrado.")
        elif user_type == 'admin':
            # Gestión de gastos e ingresos desde Google Sheets
            st.subheader("Informe Financiero")
            df = get_financials()
            st.dataframe(df)
        else:
            st.error("No tienes permiso para acceder a esta sección.")