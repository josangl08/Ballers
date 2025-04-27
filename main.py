# main.py
import streamlit as st
import time
from config import SECRET_KEY

# Función de logout
def logout():
    for key in ["user_id", "user_type", "permit_level"]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

# Función de animación de carga
def loading_animation(text="Cargando...", seconds=1):
    with st.spinner(text):
        time.sleep(seconds)

# Configuración de la página
st.set_page_config(
    page_title="Ballers",
    page_icon="assets/logo2-ballers.png",
    layout="wide",
    initial_sidebar_state="expanded"
)
# Crear un contenedor para el header con el logo
header = st.container()
with header:
    # Crear 3 columnas para centrar el logo
    left_col, center_col, right_col = st.columns([1, 2, 1])
    with center_col:
        # Mostrar el logo centrado
        st.image("assets/logo-ballers.png", width=150)
        
st.markdown("""
    <style>
        div[data-testid="stImage"] {
            text-align: center;
            display: block;
            margin-left: auto;
            margin-right: auto;
        }
        div.block-container {
            padding-top: 1rem;
        }
    </style>
    """, unsafe_allow_html=True)

# Sidebar para cuando el usuario no está logueado
if "user_id" not in st.session_state:
    
     # Contenido principal con el formulario de login
    import views.login as login_page
    login_page.show()  # Muestra la página de login
    st.stop()  # Detiene la ejecución aquí si el usuario no está logeado

# Estilos de sidebar dinámicos por tipo de usuario
sidebar_color = "#ffffff"  # Color por defecto

if st.session_state['user_type'] == 'admin':
    sidebar_color = "#ffe5e5"  # Rojo clarito
elif st.session_state['user_type'] == 'coach':
    sidebar_color = "#e5f0ff"  # Azul clarito
elif st.session_state['user_type'] == 'player':
    sidebar_color = "#e5ffe5"  # Verde clarito

# Inyectar CSS personalizado
st.markdown(
    f"""
    <style>
    [data-testid="stSidebar"] {{
        background-color: {sidebar_color};
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# Sidebar personalizado
with st.sidebar:

    # Logo centrado en "header visual"
    st.sidebar.image("assets/logo2-ballers.png", width=150)

    st.markdown("---")

    # Info usuario
    st.markdown(f"👤 **Usuario:** {st.session_state['user_type'].capitalize()}")

    # Menú de navegación con botones
    st.subheader("Navegación")
    selected_page = None
    if st.session_state['user_type'] == 'admin':
        if st.button("🏀 Ballers"):
            selected_page = "Ballers"
        if st.button("🛠 Administración"):
            selected_page = "Administración"
    elif st.session_state['user_type'] == 'coach':
        if st.button("🏀 Ballers"):
            selected_page = "Ballers"
    elif st.session_state['user_type'] == 'player':
        if st.button("👤 Mi Perfil"):
            selected_page = "Mi Perfil"

    if selected_page:
        st.session_state['selected_page'] = selected_page

    # Botón de logout
    if st.button("🔓 Cerrar sesión"):
        logout()

    st.markdown("---")


# Carga dinámica de página
if 'selected_page' in st.session_state:
    loading_animation(f"Cargando {st.session_state['selected_page']}...", seconds=1)
    if st.session_state['selected_page'] == 'Ballers':
        import views.ballers as ballers_page
        ballers_page.show()
    elif st.session_state['selected_page'] == 'Administración':
        import views.admin as admin_page
        admin_page.show()
    #elif st.session_state['selected_page'] == 'Mi Perfil':
        #import views.ballers as ballers_page
        #ballers_page.show()