# controllers/db.py
import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL

@st.cache_resource
def get_db_engine():
    """
    Devuelve una única instancia de SQLAlchemy Engine.
    """
    return create_engine(DATABASE_URL, echo=True)

@st.cache_resource
def get_session_local():
    """
    Devuelve un sessionmaker vinculado al engine cacheado.
    """
    engine = get_db_engine()
    return sessionmaker(bind=engine)
