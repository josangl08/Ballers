# pages/login.py
import streamlit as st
from controllers.db_controller import get_session_local
from config import DATABASE_URL
from models.user_model import User
import bcrypt

# Conexión a BD
SessionLocal = get_session_local()

def show():
    st.title("Login")
    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    if st.button("Login"):
        if not username or not password:
            st.error("Completa ambos campos.")
            return

        with SessionLocal() as db:
            user = db.query(User).filter_by(username=username).first()
            if user and bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
                # Guardar sesión
                st.session_state["user_id"] = user.user_id
                st.session_state["user_type"] = user.user_type.value
                st.session_state["permit_level"] = user.permit_level
                st.success(f"¡Bienvenido {user.name}!")
                st.experimental_rerun()
            else:
                st.error("Credenciales inválidas.")