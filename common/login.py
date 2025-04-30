# common/login.py
import streamlit as st
from controllers.db_controller import get_session_local
from config import DATABASE_URL
from models import User
import bcrypt

# Conexión a la BD
SessionLocal = get_session_local()


def _hide_sidebar_and_button():
    st.markdown(
        """
        <style>
        /* oculta barra + botón sólo en la pantalla de login */
        [data-testid="stBaseButton-headerNoPadding"]{
            display:none !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def show():
    _hide_sidebar_and_button()
    # Diseño centrado
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        #st.image("assets/logo-ballers.png", width=200)
        st.title("Iniciar sesión")

        with st.form(key='login_form'):
            username = st.text_input("Usuario")
            password = st.text_input("Contraseña", type='password')
            submit_button = st.form_submit_button(label="Iniciar sesión")
            
            if submit_button:
                db = SessionLocal()

                try:
                    # Buscamos el usuario
                    user = db.query(User).filter(User.username == username).first()

                    if not user:
                        st.error("Usuario no encontrado.")
                        st.stop()

                    st.info(f"Usuario encontrado: {user.username}")

                    # Verificamos contraseña
                    if bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
                        st.success("Login exitoso ✅")
                        st.session_state['user_id'] = user.user_id
                        st.session_state['user_type'] = user.user_type.value
                        st.rerun()
                    else:
                        st.error("Contraseña incorrecta.")
                
                except Exception as e:
                    st.error(f"Error en login: {e}")
                finally:
                    db.close()
