import streamlit as st

def generar_menu():
    st.sidebar.image("assets/logo.png", width=180)

    role = st.session_state.get("user_type")

    if role == "admin":
        options = {"Ballers": "ballers", "Administración": "admin"}
    elif role == "coach":
        options = {"Ballers": "ballers"}
    else:                    # player
        options = {"Mi Perfil": "ballers"}

    choice = st.sidebar.radio("Menú", list(options.keys()))
    return options[choice]