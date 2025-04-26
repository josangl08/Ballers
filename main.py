import streamlit as st
from config import SECRET_KEY

st.set_page_config(
    page_title="Centro Entrenamiento",
    page_icon="assets/logo.png",
    layout="wide"
)
st.image("assets/logo.png", width=200)
st.title("Ballers")