import pathlib, time, streamlit as st
from common import login
from common.menu import generar_menu

# ---------- helpers ----------
def logout():
    for k in ("user_id", "user_type", "permit_level", "selected_page"):
        st.session_state.pop(k, None)
    st.rerun()

def loading(msg="Cargando...", sec=1):
    with st.spinner(msg):
        time.sleep(sec)

# ---------- page config (primera llamada Streamlit) ----------
st.set_page_config(
    page_title="Ballers",
    page_icon="assets/logo_white.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- CSS global ----------
css_path = pathlib.Path("styles/base.css")
st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

# ---------- header con logo centrado ----------
_, c, _ = st.columns([1, 2, 1])
with c:
    st.image("assets/logo_white.png", width=150)

# ---------- flujo principal ----------
if "user_id" not in st.session_state:
    # Sin sesión → ocultamos completamente el sidebar y lanzamos login
    st.markdown(
        "<style>[data-testid='stSidebar'],"
        "[data-testid='stSidebarCollapseButton']{display:none!important;}</style>",
        unsafe_allow_html=True,
    )
    login.show()
    st.stop()

# ---------- usuario logeado → menú dinámico ----------
selected = generar_menu(logout_cb=logout)

# ---------- router ----------
if selected:
    loading(f"Cargando {selected}...", 1)

    if selected == "Ballers":
        import pages.ballers as page
    elif selected == "Administración":
        import pages.admin as page
    else:  # "Mi Perfil"
        import pages.ballers as page  # misma vista por ahora

    page.show()
