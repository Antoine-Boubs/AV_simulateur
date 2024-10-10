import streamlit as st
import pandas as pd
import numpy_financial as npf
import numpy as np
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import uuid
from datetime import date


st.set_page_config(
    layout="centered", 
    page_title="Simulateur Assurance-Vie", 
    page_icon="📊", 
    initial_sidebar_state="expanded", 
)

with open("assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.markdown(f"""
<div class="title-container">
    <h1 class="main-title">Simulateur Assurance-Vie</h1>
    <div class="separator"></div>
    <p class="subtitle">Atteignez vos objectifs et plus encore</p>
    <div class="info-container">
        <div class="update-info">Dernière mise à jour : 09/10/2024</div>
        <div class="author-info">Par Antoine Berjoan</div>
    </div>
</div>
""", unsafe_allow_html=True)
