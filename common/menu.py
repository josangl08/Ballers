# common/menu.py
import streamlit as st

_PALETTE_BG = {
    "admin":  "RGBA(0,0,0,0.9)",
    "coach":  "RGBA(0,0,0,0.9)",
    "player": "RGBA(36,222,132,1)",
}
_PALETTE_TXT = {
    "admin":  "#24DE84",   
    "coach":  "#24DE84",   
    "player": "RGBA(255,255,255,1)",   
}

def _set_sidebar_style(role: str) -> None:
    bg  = _PALETTE_BG.get(role, "RGBA(255,255,255,1)")
    txt = _PALETTE_TXT.get(role, "RGBA(255,255,255,1)")

    st.markdown(
        f"""
        <style>
        :root{{--sidebar-bg:{bg}; --menu-txt:{txt};}}
        </style>
        """,
        unsafe_allow_html=True,
    )


def generar_menu(logout_cb) -> str | None:
    """Dibuja el menú lateral y devuelve la página elegida."""
    user_type = st.session_state.get("user_type", "")
    _set_sidebar_style(user_type)

    with st.sidebar:
        st.image("assets/isotipo_white.png", width=150)
        st.markdown("---")
        st.markdown(f"👤 **Usuario:** {user_type.capitalize()}")
       


        st.subheader("Navegación")
        page = None
        if user_type == "admin":
            if st.button("⚽️ Ballers"):
                page = "Ballers"
            if st.button("🛠 Administración"):
                page = "Administración"
        elif user_type == "coach":
            if st.button("⚽️ Ballers"):
                page = "Ballers"
            if st.button("🛠 Administración"):
                page = "Administración"
        elif user_type == "player":
            if st.button("👤 Mi Perfil"):
                page = "Mi Perfil"

        if page:
            st.session_state["selected_page"] = page

        if st.button("🔓 Cerrar sesión"):
            logout_cb()

        st.markdown("---")

    return st.session_state.get("selected_page")
