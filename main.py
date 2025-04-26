import streamlit as st
from config import SECRET_KEY

# Configuración de la página
st.set_page_config(
    page_title="Ballers",
    page_icon="assets/logo.png",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.image("assets/logo.png", width=200)
st.title("Ballers")

# Función de logout
def logout():
    for key in ["user_id", "user_type", "permit_level"]:
        if key in st.session_state:
            del st.session_state[key]
    st.experimental_rerun()

# Comprobar si el usuario está logeado
if "user_id" not in st.session_state:
    import pages.login as login_page
    login_page.show()
    st.stop()

# Sidebar personalizado por rol
st.sidebar.title("Menú")
st.sidebar.write(f"Usuario: {st.session_state['user_type'].capitalize()}")
st.sidebar.button("Logout", on_click=logout)

# Opciones básicas
menu_items = []
if st.session_state['user_type'] == 'admin':
    menu_items = ['Ballers', 'Administración']
elif st.session_state['user_type'] == 'coach':
    menu_items = ['Ballers']
elif st.session_state['user_type'] == 'player':
    menu_items = ['Mi Perfil']

selection = st.sidebar.radio("Ir a", menu_items)

# Carga dinámica de páginas
if selection == 'Ballers':
    import pages.ballers as ballers_page
    ballers_page.show()
elif selection == 'Administración':
    import pages.admin as admin_page
    admin_page.show()