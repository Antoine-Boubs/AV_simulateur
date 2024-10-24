import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import math
from streamlit_extras.card import card
from plotly.subplots import make_subplots
import plotly.io as pio
import os
import tempfile
from datetime import datetime
from PIL import Image
import plotly.graph_objects as go
import io
import urllib.parse
import numpy as np
import uuid




st.set_page_config(
    layout="centered", 
    page_title="Simulateur de placement simplifié", 
    page_icon="📊", 
    initial_sidebar_state="expanded", 
    menu_items={
        'Get help': 'https://www.antoineberjoan.com',
    }
)


def load_css():
    with open("assets/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()


def input_simulateur():
    with st.sidebar:
        st.header("📊 Paramètres de l'investissement")

        with st.container():
            capital_initial = st.number_input("💵 Capital initial (CI)", min_value=0.0, max_value=1000000.0, value=2000.0, step=100.0, key="capital_initial_key")
            frais_entree_ci = st.slider("💸 Frais d'entrée CI (%)", min_value=0.0, max_value=10.0, value=4.5, key="frais_entree_ci_key") / 100
            versement_mensuel = st.number_input("📅 Versement mensuel (VP)", min_value=0.0, max_value=20000.0, value=400.0, step=50.0, key="versement_mensuel_key")
            frais_entree_vp = st.slider("💸 Frais d'entrée VP (%)", min_value=0.0, max_value=10.0, value=4.5, key="frais_entree_vp_key") / 100

        with st.container():
            rendement_annuel = st.slider("📈 Rendement annuel (%)", min_value=0.0, max_value=20.0, value=5.0, step=0.1, key="rendement_annuel_key") / 100
            frais_gestion = st.slider("🛠️ Frais de gestion (%)", min_value=0.0, max_value=5.0, value=0.8, step=0.1, key="frais_gestion_key") / 100

        rendement_phase_rachat = st.slider("📉 Rendement phase de rachat (%)", min_value=0.0, max_value=20.0, value=3.0, step=0.1, key="rendement_phase_rachat_key", help="Dépend de votre degré de sécurisation en phase de rachat") / 100

        option_fiscalite = st.radio(
            "Durée de vie de votre contrat",
            ("− 8 ans", "﹢ 8 ans"),
            key="option_fiscalite_key",
            horizontal=True,
            help="Avantage fiscal à partir de la 8ème année"
        )

        # Sélection du statut (Solo ou Couple) sur la même ligne
        statut = st.radio(
            "Êtes-vous seul ou en couple ?",
            ("Seul", "Couple"),
            key="statut_key",
            horizontal=True,
            help="Vous bénéficiez d'un abattement fiscal doublé pour le couple (⚠️ c'est un plafond commun)"
        )

        # Déterminer l'abattement en fonction du statut
        abattement = 4600 if statut == "Seul" else 9200

    # Retourner tous les paramètres sous forme de dictionnaire
    return {
        "capital_initial": capital_initial,
        "frais_entree_ci": frais_entree_ci,
        "versement_mensuel": versement_mensuel,
        "frais_entree_vp": frais_entree_vp,
        "rendement_annuel": rendement_annuel,
        "frais_gestion": frais_gestion,
        "rendement_phase_rachat": rendement_phase_rachat,
        "option_fiscalite": option_fiscalite,
        "abattement": abattement
    }

import streamlit as st



# Initialisation des variables de session
if "versements_libres" not in st.session_state:
    st.session_state.versements_libres = []
if "modifications_versements" not in st.session_state:
    st.session_state.modifications_versements = []
if "show_stopper_interface" not in st.session_state:
    st.session_state.show_stopper_interface = False
if "show_modifier_interface" not in st.session_state:
    st.session_state.show_modifier_interface = False

# Fonctions (inchangées)
def ajouter_versement_libre():
    st.session_state.versements_libres.append({
        "annee": 5,
        "montant": 1000.0
    })

def supprimer_versement_libre(index):
    st.session_state.versements_libres.pop(index)

def ajouter_modification_versement(debut, fin, montant):
    st.session_state.modifications_versements.append({
        "debut": debut,
        "fin": fin,
        "montant": montant
    })

def supprimer_modification_versement(index):
    st.session_state.modifications_versements.pop(index)

def toggle_stopper_interface():
    st.session_state.show_stopper_interface = not st.session_state.show_stopper_interface
    st.session_state.show_modifier_interface = False

def toggle_modifier_interface():
    st.session_state.show_modifier_interface = not st.session_state.show_modifier_interface
    st.session_state.show_stopper_interface = False

def verifier_chevauchements():
    chevauchements = []
    for i, modif1 in enumerate(st.session_state.modifications_versements):
        for j, modif2 in enumerate(st.session_state.modifications_versements):
            if i != j:
                if (modif1['debut'] <= modif2['fin'] and modif2['debut'] <= modif1['fin']):
                    chevauchements.append((i, j))
    return chevauchements



# Boutons pour gérer les versements
col1, col2, col3 = st.columns(3)
with col1:
    st.button("➕ Ajouter un versement", on_click=ajouter_versement_libre, key="add_free_payment")
with col2:
    st.button("🛑 Stopper les versements", on_click=toggle_stopper_interface, key="stop_payments")
with col3:
    st.button("📊 Modifier les versements", on_click=toggle_modifier_interface, key="modify_payments")

# Affichage de tous les versements libres avec option de suppression
if st.session_state.versements_libres:
    for i, versement in enumerate(st.session_state.versements_libres):
        with st.expander(f"💰 Versement libre de {versement['montant']}€ à l'année {versement['annee']}", expanded=True):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                versement["annee"] = st.slider(f"Année", min_value=1, max_value=60, value=versement["annee"], key=f"year_slider_{i}")
            with col2:
                versement["montant"] =  st.number_input(f"Montant (€)", min_value=0.0, value=versement["montant"], step=100.0, format="%.2f", key=f"amount_input_{i}")
            with col3:
                st.button("❌", key=f"delete_free_{i}", on_click=supprimer_versement_libre, args=(i,))

# Interface pour stopper les versements
if st.session_state.show_stopper_interface:
    with st.form(key="stop_form"):
        debut, fin = st.slider("Période d'arrêt des versements", 1, 60, (1, 5), key="stop_slider")
        submit_stop = st.form_submit_button("Confirmer l'arrêt des versements")
        if submit_stop:
            ajouter_modification_versement(debut, fin, 0)
            st.session_state.show_stopper_interface = False
            st.success("Arrêt des versements confirmé!")
            st.rerun()

# Interface pour modifier les versements
if st.session_state.show_modifier_interface:
    with st.form(key="modify_form"):
        debut, fin = st.slider("Période de modification des versements", 1, 60, (1, 5), key="modify_slider")
        nouveau_montant = st.number_input("Nouveau montant mensuel (€)", min_value=0.0, value=400.0, step=100.0, format="%.2f", key="new_amount")
        submit_modify = st.form_submit_button("Confirmer la modification")
        if submit_modify:
            ajouter_modification_versement(debut, fin, nouveau_montant)
            st.session_state.show_modifier_interface = False
            st.success("Modification des versements confirmée!")
            st.rerun()

# Affichage des modifications de versements
if st.session_state.modifications_versements:
    chevauchements = verifier_chevauchements()
    if chevauchements:
        st.warning("⚠️ Attention : Certaines périodes de modifications se chevauchent. Veuillez vérifier vos saisies.")   

    for i, modification in enumerate(st.session_state.modifications_versements):
        if modification['montant'] == 0:
            emoji = "🔴 "
            etat = "Versements arrêtés"
        elif modification['montant'] > 0:
            emoji = "💰 "
            etat = "Versements modifiés"
        else:
            emoji = ""
            etat = "État inconnu"
        
        with st.expander(f"{emoji}Versements de {modification['debut']} à {modification['fin']} ans : {modification['montant']}€ / mois", expanded=True):
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
            with col1:
                st.markdown(f"**Années** : {modification['debut']} - {modification['fin']}")
            with col2:
                st.markdown(f"**Montant** : {modification['montant']} €")
            with col3:
                st.markdown(f"**État** : {etat}")
            with col4:
                st.button("❌", key=f"delete_modif_{i}", on_click=supprimer_modification_versement, args=(i,))

        if any(i in chevauchement for chevauchement in chevauchements):
            st.warning(f"⚠️ Cette modification chevauche une autre période.")

import streamlit as st
import pandas as pd
import math


# Initialisation de la liste des objectifs dans la session state
if "objectifs" not in st.session_state:
    st.session_state.objectifs = []

# Fonction pour mettre à jour les valeurs des sliders
def mettre_a_jour_slider(cle):
    st.session_state[cle] = st.session_state[cle]


# Affichage de tous les objectifs
for i, objectif in enumerate(st.session_state.objectifs):
    with st.expander(f"Objectif {i + 1}: {objectif['nom']}", expanded=True):
        col_delete, col_nom = st.columns([1, 11])
        with col_delete:
            if st.button("🗑️", key=f"delete_button_{i}", help="Supprimer cet objectif", on_click=lambda i=i: st.session_state.objectifs.pop(i)):
                st.rerun()
        with col_nom:
            objectif["nom"] = st.text_input("Nom de l'objectif", value=objectif["nom"], key=f"nom_objectif_{i}")
        
        col_montant, col_annee, col_duree = st.columns(3)
        with col_montant:
            objectif["montant_annuel"] = st.number_input(
                "Montant annuel (€)",
                min_value=0,
                value=objectif["montant_annuel"],
                step=100,
                key=f"montant_annuel_{i}"
            )
        with col_annee:
            objectif["annee"] = st.slider(
                "Année de réalisation",
                min_value=1,
                max_value=60,
                value=objectif["annee"],
                key=f"annee_realisation_{i}",
                on_change=mettre_a_jour_slider,
                args=(f"annee_realisation_{i}",)
            )
        with col_duree:
            objectif["duree_retrait"] = st.slider(
                "Durée (années)",
                min_value=1,
                max_value=60,
                value=objectif["duree_retrait"],
                key=f"duree_retrait_{i}",
                on_change=mettre_a_jour_slider,
                args=(f"duree_retrait_{i}",)
            )

# Bouton pour ajouter un nouvel objectif
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("➕ Ajouter un objectif", key="ajouter_objectif"):
        st.session_state.objectifs.append({
            "nom": f"Nouvel objectif",
            "annee": 10,
            "montant_annuel": 5000,
            "duree_retrait": 4
        })
        st.rerun()

# Utilisation des objectifs dans le reste de votre code
objectifs = st.session_state.objectifs

# Exemple de DataFrame pour les rachats
df_test = pd.DataFrame({
    "Année": range(1, 61),
    "Capital début année": [math.nan] * 60,
    "Rendement": [math.nan] * 60,
    "Frais de gestion": [math.nan] * 60,
    "Capital fin année": [math.nan] * 60,
    "Rachat": [0.0] * 60  # Initialisé à 0 pour l'instant
})

# Ajout automatique des montants de rachat aux années concernées
for objectif in objectifs:
    annee = objectif["annee"] 
    montant_rachat_annuel = objectif["montant_annuel"]
    
    # Ajouter le montant annuel de l'objectif au rachat pour les années concernées
    for j in range(objectif["duree_retrait"]):
        if annee + j <= 60:
            df_test.at[annee + j - 1, "Rachat"] += montant_rachat_annuel





def calculer_duree_capi_max(objectifs):
    if not objectifs:  # Vérifie si la liste est vide
        return 60  # Durée par défaut si aucun objectif n'est défini
    return max(obj["annee"] for obj in objectifs)

def calcul_rendement_versements_mensuels(versement_mensuel_investi, rendement_annuel):
    rendement_versements = 0
    for mois in range(12):
        prorata = (12 - mois) / 12  # Le mois de janvier est investi 12 mois, février 11 mois, etc.
        rendement_versements += (versement_mensuel_investi * prorata) * rendement_annuel
    return rendement_versements

def calculer_duree_totale(objectifs):
    if not objectifs:  # Vérifie si la liste est vide
        return 60  # Durée par défaut si aucun objectif n'est défini
    # Calculer la durée maximale en fonction des objectifs
    return max(obj["annee"] + obj["duree_retrait"] for obj in objectifs)

# ... (autre code)

if not objectifs:
    st.warning("Aucun objectif n'a été défini. Une durée par défaut de 60 ans sera utilisée pour la simulation.")

# Calcul des valeurs dynamiques pour le tableau
def optimiser_objectifs(params, duree_totale):
    capital_initial = params["capital_initial"]
    duree_totale = calculer_duree_totale(objectifs)
    frais_entree_ci = params["frais_entree_ci"]
    versement_mensuel_initial = params["versement_mensuel"]
    frais_entree_vp = params["frais_entree_vp"]
    rendement = params["rendement_annuel"]
    frais_gestion = params["frais_gestion"]
    option_fiscalite = params["option_fiscalite"]
    abattement = params["abattement"]
    rendement_phase_rachat = params["rendement_phase_rachat"]
    objectif_annee_max = calculer_duree_capi_max(objectifs)

    capital_initial_investi = capital_initial * (1 - frais_entree_ci)
    
    capital_debut_annee = capital_initial_investi
    epargne_investie = capital_initial
    pourcentage_plus_value_precedent = 0

    data = []

    # Création d'une colonne 'Rachat' initialement à 0 pour toutes les années
    rachats = [0.0] * (duree_totale + 1)
    for objectif in objectifs:
        annee_debut = objectif["annee"] + 1
        duree_retrait = int(objectif["duree_retrait"])
        montant_annuel_retrait = objectif["montant_annuel"]
        
        for annee in range(annee_debut, min(annee_debut + duree_retrait, duree_totale + 1)):
            rachats[annee - 1] += montant_annuel_retrait

    for annee in range(1, duree_totale + 1):
        # Déterminer le versement mensuel pour l'année en cours
        versement_mensuel_courant = versement_mensuel_initial
        modifications = st.session_state.get('modifications_versements', [])
        for modification in modifications:
            if modification["debut"] <= annee <= modification["fin"]:
                versement_mensuel_courant = modification["montant"]
                break
        
        versement_mensuel_investi = versement_mensuel_courant * (1 - frais_entree_vp)
        versements_actifs = annee <= objectif_annee_max and versement_mensuel_courant > 0
        
        # Traitement du rachat pour l'année en cours
        rachat_annee = min(rachats[annee - 1], capital_debut_annee)
        
        # Déduire le rachat du capital de début d'année
        capital_debut_annee -= rachat_annee

        if rachat_annee > 0:
            part_plus_value = pourcentage_plus_value_precedent * rachat_annee
            part_capital = rachat_annee - part_plus_value
            
            # Calcul de la fiscalité
            fiscalite = 0
            if part_plus_value > 0:
                fiscalite = part_plus_value * 0.172
                if option_fiscalite == "+ 8 ans":
                    if part_plus_value > abattement:
                        plus_value_taxable = part_plus_value - abattement
                        pourcentage_epargne_sup_150k = max(0, 1 - (150000 / epargne_investie)) if epargne_investie > 150000 else 0
                        part_sup_150k = pourcentage_epargne_sup_150k * rachat_annee
                        part_inf_150k = rachat_annee - part_sup_150k
                        part_plus_value_inf_150k = plus_value_taxable * (part_inf_150k / rachat_annee)
                        fiscalite += part_plus_value_inf_150k * 0.075
                        part_plus_value_sup_150k = plus_value_taxable * (part_sup_150k / rachat_annee)
                        fiscalite += part_plus_value_sup_150k * 0.128
                elif option_fiscalite == "− 8 ans":
                    fiscalite += part_plus_value * 0.128
            
            rachat_net = rachat_annee - fiscalite
            
            # Mise à jour de l'épargne investie après le rachat
            epargne_investie = max(0, epargne_investie - part_capital)
        else:
            part_plus_value, part_capital, fiscalite, rachat_net = 0, 0, 0, 0


        if annee > objectif_annee_max:
            rendement_annuel_total = capital_debut_annee * rendement_phase_rachat
        else:
            rendement_annuel_total = capital_debut_annee * rendement

        rendement_versements_net = calcul_rendement_versements_mensuels(versement_mensuel_investi, rendement) if versements_actifs else 0
        
        frais_gestion_total = (capital_debut_annee * frais_gestion)
        if versements_actifs:
            frais_gestion_total += sum([(versement_mensuel_investi * (12 - mois) / 12) * frais_gestion for mois in range(12)])

        versement_libre_exceptionnel = sum(versement["montant"] for versement in st.session_state.versements_libres if versement["annee"] == annee)
        
        capital_fin_annee = (
            capital_debut_annee
            + (versement_mensuel_investi * 12 if versements_actifs else 0)
            + rendement_annuel_total
            + rendement_versements_net
            - frais_gestion_total
            + versement_libre_exceptionnel * (1 - frais_entree_vp)
        )

        # Mise à jour de l'épargne investie pour l'année en cours
        if versements_actifs:
            epargne_investie += versement_mensuel_courant * 12
        epargne_investie += versement_libre_exceptionnel

        # Calcul du nouveau pourcentage de plus-value
        pourcentage_plus_value = 1 - (epargne_investie / capital_fin_annee) if epargne_investie > 0 and capital_fin_annee > 0 else 0

        data.append([
            annee, 
            f"{capital_debut_annee:.2f} €",
            f"{versement_mensuel_investi * 12 if versements_actifs else 0:.2f} €",
            f"{rendement_annuel_total + rendement_versements_net:.2f} €",
            f"{frais_gestion_total:.2f} €",
            f"{capital_fin_annee:.2f} €",
            f"{rachat_annee:.2f} €",
            f"{epargne_investie:.2f} €",
            f"{versement_libre_exceptionnel:.2f} €",
            f"{part_capital:.2f} €",
            f"{part_plus_value:.2f} €",
            f"{fiscalite:.2f} €",
            f"{pourcentage_plus_value*100:.2f}%",
            f"{rachat_net:.2f} €"
        ])
        
        # Préparation pour l'année suivante
        capital_debut_annee = capital_fin_annee
        pourcentage_plus_value_precedent = pourcentage_plus_value

    return pd.DataFrame(data, columns=[
        "Année", "Capital initial (NET)", "VP NET", "Rendement", "Frais de gestion", 
        "Capital fin d'année (NET)", "Rachat", "Épargne investie", "VP exceptionnel", 
        "Part capital", "Part intérêt", "Fiscalite", "%", "Rachat net"
    ])


def color_alternating_rows(s):
    return ['background-color: #EEEFF1' if i % 2 == 0 else 'background-color: #FBFBFB' for i in range(len(s))]

def format_currency(val):
    if pd.isna(val) or not isinstance(val, (int, float)):
        return ""
    return f"{val:,.2f} €".replace(",", " ").replace(".", ",")

def format_percentage(val):
    if pd.isna(val) or not isinstance(val, (int, float)):
        return ""
    try:
        return f"{val:.2f}%".replace(".", ",")
    except ValueError:
        return str(val)

def color_alternating_rows(s):
    return ['background-color: #EEEFF1' if i % 2 == 0 else 'background-color: #FBFBFB' for i in range(len(s))]

def style_dataframe(df):
    return df.style.format({
        col: format_currency for col in df.columns if col not in ['Année', '%']
    }).format({
        '%': format_percentage
    }).set_properties(**{
        'color': '#202021',
        'font-family': 'Inter, sans-serif',
        'font-size': '14px',
    }).apply(color_alternating_rows).set_table_styles([
        {'selector': 'th',
         'props': [('font-weight', 'bold'),
                   ('background-color', '#284264'),
                   ('color', 'white'),
                   ('font-family', 'Inter, sans-serif'),
                   ('font-size', '14px')]},
        {'selector': 'table',
         'props': [('width', '100%'),
                   ('table-layout', 'fixed')]},
    ])



params = input_simulateur()
duree_totale = calculer_duree_totale(objectifs)

# Calcul du tableau avec les paramètres actuels et intégration des rachats

# Affichage des résultats avec les rachats
st.header("📊 Résultats de la simulation avec rachats")
resultats_df = optimiser_objectifs(params, objectifs)

resultats_df.set_index('Année', inplace=True)

# Appliquez le style au DataFrame
styled_df = style_dataframe(resultats_df)

# Affichez le DataFrame stylisé
st.dataframe(styled_df, use_container_width=True)




import plotly.graph_objs as go
import pandas as pd
import streamlit as st

def create_financial_chart(df: pd.DataFrame):
    # Définir les couleurs
    couleur_principal = '#16425B'
    couleur_principal_aire = 'rgba(141, 179, 197, 0.3)'
    couleur_secondaire = '#CBA325'
    couleur_secondaire_aire = 'rgba(241, 216, 122, 0.5)'
    couleur_tertiaire = '#FF3B30'

    # Create figure
    fig = go.Figure()

    # Fonction pour convertir les valeurs en float de manière sûre
    def safe_float_convert(x):
        if pd.isna(x):
            return 0.0
        if isinstance(x, str):
            return float(x.replace(' €', '').replace(',', '.'))
        return float(x)

    # Convertir les colonnes en float de manière sûre
    capital_fin_annee = df['Capital fin d\'année (NET)'].apply(safe_float_convert)
    epargne_investie = df['Épargne investie'].apply(safe_float_convert)
    rachat = df['Rachat'].apply(safe_float_convert)

    # Add traces
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=capital_fin_annee,
            name='Capital fin d\'année',
            line=dict(color=couleur_principal, width=3),
            fill='tozeroy',
            fillcolor=couleur_principal_aire,
            mode='lines',
            hovertemplate='<span style="color:' + couleur_principal + ';">●</span> Capital fin d\'année <br>Montant: <b>%{y:.0f} €</b><extra></extra>'
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=epargne_investie,
            name='Épargne investie',
            line=dict(color=couleur_secondaire, width=3),
            fill='tozeroy',
            fillcolor=couleur_secondaire_aire,
            mode='lines',
            hovertemplate='<span style="color:' + couleur_secondaire + ';">●</span> Épargne investie <br>Montant: <b>%{y:.0f} €</b><extra></extra>'
        )
    )

    # Ajouter les rachats en dernier pour qu'ils soient au premier plan
    fig.add_trace(
        go.Bar(
            x=df.index,
            y=rachat,
            name='Rachats',
            marker_color=couleur_tertiaire,
            opacity=0.7,
            hovertemplate='<span style="color:' + couleur_tertiaire + ';">●</span> Rachats <br>Montant: <b>%{y:.0f} €</b><extra></extra>'
        )
    )

    # Customize the layout
    fig.update_layout(
        xaxis=dict(
            title="<b>Années</b>",
            tickmode='linear',
            dtick=5,
            ticksuffix=" ",
            showgrid=False,
            zeroline=False,
            showline=True,
            linewidth=3,
            linecolor='#CBA325',
        ),
        yaxis=dict(
            title="<b>Montant (€)</b>",
            tickmode='auto',
            nticks=6,
            ticksuffix=" €",
            tickformat=",",
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(200,200,200,0.2)',
            zeroline=False,
            showline=True,
            linewidth=3,
            linecolor='#CBA325',
        ),
        font=dict(family="Inter", size=14),
        margin=dict(t=60, b=60, l=60, r=60),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(size=14),
        ),
        hovermode="x unified",
        autosize=True,  # Permet au graphique de s'adapter à la taille du conteneur
    )

    return fig

# Utilisation de la fonction
st.markdown("""
<h2 style='
    text-align: center; 
    color: #16425B; 
    font-size: 20px; 
    font-weight: 700; 
    margin-top: 30px; 
    margin-bottom: 0px; 
    background-color: rgba(251, 251, 251, 1); 
    padding: 20px 15px; 
    border-radius: 15px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.6);
    '> Parcours de votre investissement : de l'épargne aux rachats
</h2>
""", unsafe_allow_html=True)

# Utiliser toute la largeur disponible
st.plotly_chart(create_financial_chart(resultats_df), use_container_width=True, config={'displayModeBar': False})







import plotly.graph_objs as go
import pandas as pd
import streamlit as st

def create_waterfall_chart(df: pd.DataFrame):
    # Traitement des données
    def safe_float(value):
        if pd.isna(value):
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            return float(value.replace(' €', '').replace(',', '.'))
        return 0.0

    capital_fin_annee = df['Capital fin d\'année (NET)'].apply(safe_float)
    yearly_change = capital_fin_annee.diff()
    yearly_change = yearly_change.fillna(capital_fin_annee.iloc[0])
    final_capital = capital_fin_annee.iloc[-1]

    # Création des icônes pour le hover
    def get_triangle_icon(val):
        return "▲" if val >= 0 else "▼"

    # Définition des couleurs personnalisées
    color_increasing = "#16425B"
    color_decreasing = "#CBA325"

    hover_text = [
        f"<b>Année {year}</b><br><br>" +
        f"<span style='color:{color_increasing if val >= 0 else color_decreasing};'>{get_triangle_icon(val)}</span> " +
        f"Variation: <b>{val:,.0f} €</b><br>" +
        f"Capital fin d'année: <b>{cap:,.0f} €</b>"
        for year, val, cap in zip(df.index, yearly_change, capital_fin_annee)
    ]
    hover_text.append(f"<b>Total</b><br>Capital final: <b>{final_capital:,.0f} €</b>")

    # Création du graphique
    fig = go.Figure(go.Waterfall(
        name = "Evolution du capital",
        orientation = "v",
        measure = ["relative"] * len(df) + ["total"],
        x = df.index.tolist() + ["Total"],
        textposition = "outside",
        text = [f"{val:,.0f} €" for val in yearly_change] + [f"{final_capital:,.0f} €"],
        y = yearly_change.tolist() + [0],
        connector = {"line":{"color":"rgba(63, 63, 63, 0.2)"}},
        increasing = {"marker":{"color":color_increasing}},
        decreasing = {"marker":{"color":color_decreasing}},
        totals = {"marker":{"color":color_increasing}},
        hoverinfo = "text",
        hovertext = hover_text,
        showlegend = False  # Ajoutez cette ligne pour supprimer la légende
    ))

    # Personnalisation du layout
    fig.update_layout(
        font=dict(family="Inter", size=14, color='#16425B'),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            title="<b>Années</b>",
            tickfont=dict(size=12),
            gridcolor='rgba(200,200,200,0.2)',
            showline=True,
            linewidth=3,
            linecolor='#CBA325',
            tickmode='linear',
            dtick=5,
            ticksuffix=" ",
            showgrid=False,
            zeroline=False,
        ),
        yaxis=dict(
            title="<b>Variation du capital (€)</b>",
            tickfont=dict(size=12),
            gridcolor='rgba(200,200,200,0.2)',
            tickformat=',.0f',
            showline=True,
            linewidth=3,
            linecolor='#CBA325',
            tickmode='auto',
            nticks=6,
            ticksuffix=" €",
            showgrid=True,
            zeroline=False,
        ),
        margin=dict(l=60, r=60, t=60, b=60),
        hoverlabel=dict(
            bgcolor="white",
            font_size=14,
            font_family="Inter"
        ),
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(size=14),
        ),
        showlegend=True  # Changé de False à True pour afficher la légende
    )

    return fig

# Création du titre stylisé en dehors du graphique
title = """
<h2 style='
    text-align: center; 
    color: #16425B; 
    font-size: 20px; 
    font-weight: 700; 
    margin-top: 30px; 
    margin-bottom: 0px; 
    background-color: rgba(251, 251, 251, 1); 
    padding: 20px 15px; 
    border-radius: 15px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.6);
    '> Évolution de votre capital année par année
</h2>
"""

# Dans votre application Streamlit
st.markdown(title, unsafe_allow_html=True)
st.plotly_chart(create_waterfall_chart(resultats_df), use_container_width=True, config={'displayModeBar': False})



import pandas as pd
import plotly.graph_objs as go
import streamlit as st

def create_donut_chart(df: pd.DataFrame, duree_capi_max: int, objectifs=None, chart_id="donut_chart_1"):
    # Vérifier si des objectifs sont définis et non vides
    if objectifs and len(objectifs) > 0:
        try:
            objectif_max = max(objectifs, key=lambda obj: obj.get("annee", 0))
            objectif_name = objectif_max.get("nom", "Objectif sans nom")
        except ValueError:
            objectif_name = "Objectif indéfini"
    else:
        objectif_name = "sans objectif spécifique"
    
    # Vérifier si le DataFrame est vide
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            x=0.5, y=0.5,
            text="Pas de données à afficher",
            font=dict(size=20, family="Inter", color='#16425B'),
            showarrow=False
        )
        return fig, f"<h2>Aucune donnée disponible pour : {objectif_name}</h2>"

    # Trouver l'année correspondant à duree_capi_max
    target_year = df.loc[duree_capi_max] if duree_capi_max in df.index else df.iloc[-1]

    # Fonction pour convertir en float de manière sûre
    def safe_float(value):
        if pd.isna(value):
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value.replace(' €', '').replace(',', '.').replace('%', ''))
            except ValueError:
                st.warning(f"Impossible de convertir la valeur '{value}' en nombre. Utilisation de 0.")
                return 0.0
        st.warning(f"Type de données inattendu: {type(value)}. Utilisation de 0.")
        return 0.0

    # Calculer les valeurs nécessaires
    capital_final = safe_float(target_year.get('Capital fin d\'année (NET)', 0))
    pourcentage_plus_value = safe_float(target_year.get('%', 0)) / 100
    plus_values = capital_final * pourcentage_plus_value
    versements = capital_final - plus_values

    if capital_final == 0:
        # Si le capital final est 0, afficher un message au lieu du graphique
        fig = go.Figure()
        fig.add_annotation(
            x=0.5, y=0.5,
            text="Pas de données à afficher",
            font=dict(size=20, family="Inter", color='#16425B'),
            showarrow=False
        )
    else:
        # Créer le graphique en donut
        colors = ['#16425B', '#CBA325']
        fig = go.Figure(data=[go.Pie(
            labels=['Versements', 'Plus-values'],
            values=[versements, plus_values],
            hole=.7,
            textinfo='label+value',
            texttemplate='%{label}<br>%{value:,.0f} €',
            textposition='outside',
            insidetextorientation='horizontal',
            marker=dict(colors=colors, line=dict(color='#ffffff', width=2)),
            direction='clockwise',
            sort=False,
            pull=[0, 0.1],
            textfont=dict(size=14, family="Inter"),
            hovertemplate='<span style="color:%{marker.color};">●</span> %{label}<br>%{percent:.2f}%<extra></extra>'
        )])

        # Calcul du pourcentage de croissance
        growth_percentage = (plus_values / versements * 100) if versements != 0 else 0
        growth_text = f"+{growth_percentage:.1f}%"

        fig.update_layout(
            annotations=[
                dict(text=f'<b>{capital_final:,.0f} €</b><br>Capital final', x=0.5, y=0.5, font_size=20, showarrow=False),
                dict(text=f'<b>{growth_text}</b><br>Plus-values', x=0.5, y=0.35, font_size=16, showarrow=False, font_color='#CBA325'),
            ]
        )

    fig.update_layout(
        font=dict(family="Inter", size=14, color='#16425B'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        margin=dict(t=60, b=60, l=60, r=60),
    )

    # Créer le titre dynamiquement
    title = f"""
    <h2 style='
        text-align: center; 
        color: #16425B; 
        font-size: 20px; 
        font-weight: 700; 
        margin-top: 30px; 
        margin-bottom: 0px; 
        background-color: rgba(251, 251, 251, 1); 
        padding: 20px 15px; 
        border-radius: 15px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.6);
        '> Votre capital pour : {objectif_name}
    </h2>
    """

    return fig, title

# Utilisation de la fonction
objectif_annee_max = calculer_duree_capi_max(objectifs)
duree_capi_max = objectif_annee_max  # Remplacez cette valeur par la durée capi max réelle

fig1, title1 = create_donut_chart(resultats_df, duree_capi_max, objectifs, chart_id=f"donut_chart_{uuid.uuid4()}")
st.markdown(title1, unsafe_allow_html=True)
st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False}, key=f"plot_{uuid.uuid4()}")





import pandas as pd
import plotly.graph_objs as go
import streamlit as st

import plotly.graph_objs as go
import pandas as pd
import streamlit as st
import uuid

def create_donut_chart2(df: pd.DataFrame, objectifs=None, chart_id="donut_chart_2"):
    # Vérifier si des objectifs sont définis et non vides
    if objectifs and len(objectifs) > 0:
        try:
            objectif_max = max(objectifs, key=lambda obj: obj.get("annee", 0))
            objectif_name = objectif_max.get("nom", "Objectif sans nom")
        except ValueError:
            objectif_name = "Objectif indéfini"
    else:
        objectif_name = "sans objectif spécifique"
    
    # Vérifier si le DataFrame est vide
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            x=0.5, y=0.5,
            text="Pas de données à afficher",
            font=dict(size=20, family="Inter", color='#16425B'),
            showarrow=False
        )
        return fig, f"<h2>Aucune donnée disponible pour : {objectif_name}</h2>"

    # Utiliser la dernière ligne du DataFrame
    target_year = df.iloc[-1]

    # Fonction pour convertir en float de manière sûre
    def safe_float(value):
        if pd.isna(value):
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value.replace(' €', '').replace(',', '.').replace('%', ''))
            except ValueError:
                st.warning(f"Impossible de convertir la valeur '{value}' en nombre. Utilisation de 0.")
                return 0.0
        st.warning(f"Type de données inattendu: {type(value)}. Utilisation de 0.")
        return 0.0

    # Calculer les valeurs nécessaires
    capital_final = safe_float(target_year.get('Capital fin d\'année (NET)', 0))
    pourcentage_plus_value = safe_float(target_year.get('%', 0)) / 100
    plus_values = capital_final * pourcentage_plus_value
    versements = capital_final - plus_values

    if capital_final == 0:
        # Si le capital final est 0, afficher un donut vide gris clair
        fig = go.Figure(data=[go.Pie(
            labels=['Capital épuisé'],
            values=[1],
            hole=.7,
            textinfo='none',
            marker=dict(colors=['#E0E0E0']),
            hoverinfo='none'
        )])
        fig.update_layout(
            annotations=[
                dict(text='<b>0 €</b><br>Capital épuisé', x=0.5, y=0.5, font_size=20, showarrow=False, font=dict(color='#16425B'))
            ]
        )
    else:
        # Créer le graphique en donut
        colors = ['#16425B', '#CBA325']
        fig = go.Figure(data=[go.Pie(
            labels=['Versements', 'Plus-values'],
            values=[versements, plus_values],
            hole=.7,
            textinfo='label+value',
            texttemplate='%{label}<br>%{value:,.0f} €',
            textposition='outside',
            insidetextorientation='horizontal',
            marker=dict(colors=colors, line=dict(color='#ffffff', width=2)),
            direction='clockwise',
            sort=False,
            pull=[0, 0.1],
            textfont=dict(size=14, family="Inter"),
            hovertemplate='<span style="color:%{marker.color};">●</span> %{label}<br>%{percent:.2f}%<extra></extra>'
        )])

        # Calcul du pourcentage de croissance
        growth_percentage = (plus_values / versements * 100) if versements != 0 else 0
        growth_text = f"+{growth_percentage:.1f}%"

        fig.update_layout(
            annotations=[
                dict(text=f'<b>{capital_final:,.0f} €</b><br>Capital final', x=0.5, y=0.5, font_size=20, showarrow=False),
                dict(text=f'<b>{growth_text}</b><br>Plus-values', x=0.5, y=0.35, font_size=16, showarrow=False, font_color='#CBA325'),
            ]
        )

    fig.update_layout(
        font=dict(family="Inter", size=14, color='#16425B'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        margin=dict(t=60, b=60, l=60, r=60),
    )

    # Créer le titre dynamiquement
    title = f"""
    <h2 style='
        text-align: center; 
        color: #16425B; 
        font-size: 20px; 
        font-weight: 700; 
        margin-top: 30px; 
        margin-bottom: 0px; 
        background-color: rgba(251, 251, 251, 1); 
        padding: 20px 15px; 
        border-radius: 15px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.6);
        '> Votre capital au terme de vos projets
    </h2>
    """

    return fig, title

# Utilisation de la fonction
fig2, title2 = create_donut_chart2(resultats_df, objectifs, chart_id=f"donut_chart_{uuid.uuid4()}")
st.markdown(title2, unsafe_allow_html=True)
st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False}, key=f"plot_{uuid.uuid4()}")


def fig_to_img_buffer(fig_or_tuple):
    if isinstance(fig_or_tuple, tuple):
        fig = fig_or_tuple[0]  # Prendre la figure si c'est un tuple
    else:
        fig = fig_or_tuple
    img_bytes = fig.to_image(format="png", width=800, height=400, scale=2)
    return io.BytesIO(img_bytes)

































import tempfile
import os
from PIL import Image
import io
from fpdf import FPDF
import os
from fpdf import FPDF
import numpy as np 
from datetime import datetime
import base64
import os
from fpdf import FPDF
import numpy as np 
from datetime import datetime
import tempfile
from PIL import Image
import io
from math import sqrt
from math import pi, sin, cos
import streamlit as st
from io import BytesIO
import datetime




class PDF(FPDF):
    def __init__(self, logo_path=None):
        super().__init__()

        self.current_year = datetime.datetime.now().year

        self.is_custom_font_loaded = False
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.logo_path = logo_path or os.path.join(current_dir, "assets", "Logo.png")
        self.track_record_path = os.path.join(os.path.dirname(__file__), "assets", "Track_record.png") 

        self.linkedin_icon = 'assets/linkedin_icon.png'
        self.email_icon = 'assets/email_icon.png'
        self.whatsapp_icon = 'assets/whatsapp_icon.png'
        self.email = 'antoineberjoan@gmail.com'
        self.phone = '33686514317'
        self.whatsapp_message = "Bonjour, j'aimerais en savoir plus sur vos services."  # Message par défaut pour le SMS


        self.current_section = 'Votre simulation personnalisée'  # Titre par défaut


        font_path = os.path.join(current_dir, "assets", "Fonts")
        
        font_files = {
            '': 'Inter-Regular.ttf',
            'B': 'Inter-Bold.ttf',
            'I': 'Inter-Italic.ttf'
        }

        for style, filename in font_files.items():
            full_path = os.path.join(font_path, filename)
            if os.path.exists(full_path):
                self.add_font('Inter', style, full_path, uni=True)
                self.is_custom_font_loaded = True
                print(f"Police {filename} chargée avec succès.")
            else:
                print(f"Fichier de police non trouvé : {full_path}")

        if not self.is_custom_font_loaded:
            print("Aucune police personnalisée n'a été chargée. Utilisation des polices par défaut.")


    def set_font_safe(self, family, style='', size=0):
        try:
            if self.is_custom_font_loaded and family == 'Inter':
                self.set_font('Inter', style, size)
            else:
                self.set_font('Arial', style, size)
        except Exception as e:
            print(f"Erreur lors de la définition de la police : {e}")
            self.set_font('Arial', '', 12)


    def header(self):
        # Ajouter le logo
        if self.logo_path:
            self.image(self.logo_path, 8, 7, 15)  # Ajustez les dimensions selon votre logo

        # Chemin vers l'image du bouton RDV
        rdv_path = 'assets/RDV.png'  # Assurez-vous que le chemin est correct
        
        # Titre
        self.set_font('Inter', 'B', 16)
        self.set_text_color(22, 66, 91)
        title = self.current_section
        title_width = self.get_string_width(title) + 6
        
        # Positionnement du titre (ajusté pour laisser de la place au logo)
        self.set_xy(30, 10)  # Déplacé vers la droite pour laisser de la place au logo
        self.cell(title_width, 10, title, 0, 0, 'L')
        
        # Obtenir les dimensions de l'image RDV
        try:
            with Image.open(rdv_path) as img:
                rdv_width, rdv_height = img.size
            # Ajuster la taille de l'image si elle est trop grande
            max_width, max_height = 50, 25  # Tailles maximales souhaitées
            if rdv_width > max_width or rdv_height > max_height:
                rdv_width, rdv_height = self.scale_image_size(rdv_width, rdv_height, max_width, max_height)
        except Exception as e:
            print(f"Erreur lors de l'ouverture de l'image {rdv_path}: {e}")
            rdv_width, rdv_height = 30, 15  # Valeurs par défaut
        
        # Positionnement du bouton RDV (à droite)
        rdv_x = self.w - rdv_width - 10
        rdv_y = 5
        self.image(rdv_path, rdv_x, rdv_y, rdv_width, rdv_height, link='https://app.lemcal.com/@antoineberjoan')
        
        # Explicitly set the color and width for the divider
        self.set_draw_color(203, 163, 37)  # CBA325
        self.set_line_width(0.5)  # Set the line width to 0.5
        
        self.line(10, 25, self.w - 10, 25)
        self.ln(30)
        self.set_y(35)

    def scale_image_size(self, width, height, max_width, max_height):
        """Redimensionne proportionnellement l'image pour qu'elle rentre dans les dimensions maximales."""
        if width > max_width:
            height = int(height * (max_width / width))
            width = max_width
        if height > max_height:
            width = int(width * (max_height / height))
            height = max_height
        return width, height

    def footer(self):
        # Position initiale du footer
        self.set_y(-25)  # 25 mm du bas de la page

        # Dessiner le divider
        self.set_draw_color(0, 0, 0)  # Couleur noire
        self.line(10, self.get_y(), self.w - 10, self.get_y())

        # Positionner les icônes juste en dessous du divider
        self.set_y(self.get_y() + 2)  # 2 mm d'espace après le divider

        # Calcul des positions pour centrer les icônes
        icon_size = 7  # Taille réduite des icônes
        spacing = 5
        total_width = (3 * icon_size) + (2 * spacing)
        start_x = (self.w - total_width) / 2

        icons = [
            (self.linkedin_icon, 'https://www.linkedin.com/in/antoine_berjoan'),
            (self.email_icon, f'mailto:{self.email}'),
            (self.whatsapp_icon, f'https://wa.me/{self.phone}?text={urllib.parse.quote(self.whatsapp_message)}')
        ]

        for i, (icon_path, link) in enumerate(icons):
            if os.path.exists(icon_path):
                x = start_x + i * (icon_size + spacing)
                self.image(icon_path, x, self.get_y(), icon_size, icon_size, link=link)

        # Texte de copyright et URL
        self.set_y(self.get_y() + icon_size + 2)  # Espace après les icônes
        self.set_font('Inter', '', 8)
        self.set_text_color(128, 128, 128)  # Gris
        self.cell(0, 4, f'© {self.current_year} Antoine Berjoan. Tous droits réservés.', 0, 1, 'C')
        self.cell(0, 4, 'www.antoineberjoan.com', 0, 0, 'C', link="https://www.antoineberjoan.com")


    
    def set_section(self, section_name):
        """Définit le nom de la section actuelle."""
        self.current_section = section_name
        

    def add_track_record_image(self, image_path):
        self.set_section("Prenez en main votre avenir")

        # Obtenir les dimensions de l'image
        img_width, img_height = self.get_image_dimensions(image_path)
        
        # Calculer la largeur et la hauteur proportionnelles
        page_width = self.w - 20  # 10 mm de marge de chaque côté
        img_height = (page_width / img_width) * img_height
        
        # Déplacer le curseur un peu plus haut sur la page
        self.set_y(self.get_y() - 10)  # Ajustez cette valeur selon vos besoins
        
        # Ajouter l'image
        self.image(image_path, x=10, y=self.get_y(), w=page_width, h=img_height)
        
        # Déplacer le curseur après l'image
        self.set_y(self.get_y() + img_height + 5)


    def add_objectives_image(self, image_path):
        # Obtenir les dimensions de l'image
        img_width, img_height = self.get_image_dimensions(image_path)
    
        # Calculer la largeur et la hauteur proportionnelles
        page_width = self.w - 20  # 10 mm de marge de chaque côté
        img_height = (page_width / img_width) * img_height
    
        # Déplacer le curseur un peu plus haut sur la page
        self.set_y(self.get_y() - 10)  # Ajustez cette valeur selon vos besoins
    
        # Ajouter l'image
        self.image(image_path, x=10, y=self.get_y(), w=page_width, h=img_height)
    
        # Ajouter un lien cliquable dans la zone en bas à droite
        link_width = 60
        link_height = 20
        link_x = self.w - 10 - link_width
        link_y = self.get_y() + img_height - link_height
    
        self.link(link_x, link_y, link_width, link_height, 'https://app.lemcal.com/@antoineberjoan')
    
        # Déplacer le curseur après l'image
        self.set_y(self.get_y() + img_height + 5)

    
    def add_warning(self):
        self.add_page()
        
        warning_image_path = 'assets/Avertissement.png'  
        
        # Vérifier si le fichier existe
        if not os.path.exists(warning_image_path):
            print(f"Erreur : L'image '{warning_image_path}' n'a pas été trouvée.")
            return
        
        # Définir la position et la taille de l'image
        x = 20  # position x de l'image
        y = 50  # position y de l'image
        w = 170  # largeur de l'image
        
        # Obtenir les dimensions de l'image
        img_width, img_height = self.get_image_dimensions(warning_image_path)
        
        # Calculer la hauteur proportionnelle
        h = (w / img_width) * img_height
        
        # Insérer l'image
        self.image(warning_image_path, x, y, w, h)
            
    def get_image_dimensions(self, image_path):
        with Image.open(image_path) as img:
            return img.size


    def add_objectives_section(self, objectives):
        self.set_section("Vos objectifs")
        self.add_page()
        
        # Colors
        blue = (0, 122, 255)
        light_gray = (245, 245, 247)
        dark_gray = (60, 60, 60)
        
        # Margins and effective width
        left_margin = 20
        right_margin = 20
        self.set_left_margin(left_margin)
        self.set_right_margin(right_margin)
        effective_width = self.w - left_margin - right_margin
        
        # Section title
        self.set_font('Inter', 'B', 24)
        self.set_text_color(*blue)
        self.cell(effective_width, 15, 'Vos objectifs', 0, 1, 'L')
        self.ln(5)
        
        def add_objective(obj):
            # Background
            self.set_fill_color(*light_gray)
            self.rect(left_margin, self.get_y(), effective_width, 40, 'F')
            
            # Add a colored top border to simulate the gradient
            self.set_draw_color(*blue)
            self.set_line_width(2)
            self.line(left_margin, self.get_y(), left_margin + effective_width, self.get_y())
            
            # Objective name
            self.set_font('Inter', 'B', 14)
            self.set_text_color(*dark_gray)
            self.set_xy(left_margin + 10, self.get_y() + 5)
            self.cell(effective_width - 20, 10, obj['nom'], 0, 1)
            
            # Objective details
            self.set_font('Inter', '', 10)
            details = [
                f"Durée de rachat : {obj['duree_retrait']} ans",
                f"Horizon d'investissement : {obj['annee']}",
                f"Montant de rachat annuel : {format_value(obj['montant_annuel'])} €/an"
            ]
            
            for i, detail in enumerate(details):
                self.set_xy(left_margin + 10, self.get_y() + 2)
                self.cell(effective_width - 20, 6, detail, 0, 1)
            
            self.ln(10)  # Space between objectives
        
        # Add each objective
        for obj in objectives:
            add_objective(obj)
        
        self.ln(10)  # Extra space at the bottom
    
    
    
    def format_value(value):
        if isinstance(value, (int, float)):
            return f"{value:,.2f}".replace(",", " ").replace(".", ",")
        return str(value)


    def create_detailed_table(self, resultats_df):
        self.set_section("Tableau détaillé des résultats")
        self.add_page()

        col_widths = [10, 28, 24, 24, 20, 20, 20, 20, 28]
        headers = ['Année', 'Capital au 01/01', 'Versements', 'Rendement', 'Frais', 'Rachat', 'Fiscalité', 'Rachat net', 'Capital au 31/12']
        
        data = [
            [row['Année'], 
             format_value(row['Capital initial (NET)']),
             format_value(row['VP NET']),
             format_value(row['Rendement']),
             format_value(row['Frais de gestion']),
             format_value(row.get('Rachat', 0)),
             format_value(row.get('Fiscalite', 0)),
             format_value(row.get('Rachat net', 0)),
             format_value(row['Capital fin d\'année (NET)'])]
            for _, row in resultats_df.iterrows()
        ]

        # Nouvelle palette de couleurs
        header_color = (22, 66, 91)  # 16425b
        odd_row_color = (209, 225, 232)  # Bleu transparent
        even_row_color = (251, 251, 251)  # Alabaster
        text_color = (60, 60, 60)  # Gris foncé pour le texte
        border_color = (203, 163, 37,)  # CBA
        header_text_color = (251, 251, 251) #Alabaster

        def add_table_header():
            self.set_font_safe('Inter', 'B', 9)
            self.set_fill_color(*header_color)
            self.set_text_color(*header_text_color)
            self.set_draw_color(*border_color)
            self.set_line_width(0.4)  # Set the line width to 0.5

            for i, (header, width) in enumerate(zip(headers, col_widths)):
                self.cell(width, 10, header, 1, 0, 'C', 1)
            self.ln()

        def add_table_row(row, fill_color):
            self.set_font_safe('Inter', '', 9)
            self.set_fill_color(*fill_color)
            self.set_text_color(*text_color)
            for i, (value, width) in enumerate(zip(row, col_widths)):
                align = 'C' if i == 0 else 'R'
                self.cell(width, 8, str(value), 1, 0, align, 1)
            self.ln()

        rows_per_page = 25
        total_width = sum(col_widths)

        for i, row in enumerate(data):
            if i % rows_per_page == 0:
                if i != 0:
                    self.add_page()
                self.set_x((self.w - total_width) / 2)
                add_table_header()

            self.set_x((self.w - total_width) / 2)
            row_color = even_row_color if i % 2 == 0 else odd_row_color
            add_table_row(row, row_color)

        self.add_page()

    

    def add_simulation_parameters(self, params, resultats_df, objectifs):
        self.set_section("Paramètres de simulation")
        self.add_page()
        
        # Marges et largeur effective
        left_margin = 20
        right_margin = 15
        self.set_left_margin(left_margin)
        self.set_right_margin(right_margin)
        effective_width = self.w - left_margin - right_margin
    
        # Couleurs
        text_color = (32, 32, 33)
        title_color = (22, 66, 91)
        blue_color = (22, 66, 91)
        gold_color = (203, 163, 37)
    
        # Titre principal
        self.set_font_safe('Inter', 'B', 18)
        self.set_text_color(*title_color)
        self.cell(effective_width, 10, 'Les paramètres de votre simulation', 0, 1, 'L')
        self.ln(5)
    
        # Texte d'introduction
        self.set_font_safe('Inter', '', 10)
        self.set_text_color(*text_color)
        self.multi_cell(effective_width, 5, "La simulation suivante vous permet d'avoir une illustration des évolutions possibles de votre investissement. En aucun cas, les informations présentées dans ce document ne constituent une offre ou une sollicitation pour acheter ou vendre des instruments financiers. Elles ne doivent pas être considérées comme un conseil financier personnalisé ni comme un contrat ou une garantie de résultats futurs.")
        self.ln(5)
    
        # Paramètres & détails du projet
        self.set_font_safe('Inter', 'B', 14)
        self.cell(effective_width, 10, 'Paramètres & détails du projet', 0, 1, 'L')
        self.ln(2)
    
        # Informations du client sur 3 colonnes
        self.set_font_safe('Inter', '', 10)
        col_width = effective_width / 3
        self.cell(col_width, 6, "Capital initial :", 0, 0)
        self.cell(col_width, 6, "Versement mensuel :", 0, 0)
        self.cell(col_width, 6, "Rendement annuel :", 0, 1)
    
        self.set_font_safe('Inter', 'B', 10)
        self.cell(col_width, 6, f"{format_value(params['capital_initial'])}", 0, 0)
        self.cell(col_width, 6, f"{format_value(params['versement_mensuel'])}", 0, 0)
        self.cell(col_width, 6, f"{params['rendement_annuel']*100:.2f}%", 0, 1)
        self.ln(10)

        
        # Projection
        self.set_font_safe('Inter', 'B', 14)
        self.cell(effective_width, 10, 'Projection', 0, 1, 'L')
        self.ln(2)

        # Informations de projection sur 3 colonnes
        self.set_font_safe('Inter', '', 9)
        col_width = effective_width / 3
        # En-têtes
        self.cell(col_width, 5, "Capital à la fin de votre", 0, 0, 'L')
        self.cell(col_width, 5, "Capital restant après", 0, 0, 'L')
        self.cell(col_width, 5, "Pour des versements totaux", 0, 1, 'L')
        self.cell(col_width, 5, "phase d'épargne", 0, 0, 'L')
        self.cell(col_width, 5, "vos projets", 0, 0, 'L')
        self.cell(col_width, 5, "de", 0, 1, 'L')
        self.ln(2)
        self.ln(3)  # Reduced space before values
        
        def get_value_safely(df, year, column):
            try:
                value = df[df['Année'] == year][column].iloc[0]
                return value if pd.notna(value) else 0
            except IndexError:
                print(f"Attention : Aucune donnée trouvée pour l'année {year} dans la colonne {column}")
                return df[column].iloc[-1] if not df.empty and column in df.columns else 0
        
        duree_capi_max = self.calculer_duree_capi_max(objectifs, resultats_df)
        capital_fin_annee_duree_capi_max = parse_value(get_value_safely(resultats_df, duree_capi_max, 'Capital fin d\'année (NET)'))
        capital_fin_annee_derniere_ligne = parse_value(resultats_df['Capital fin d\'année (NET)'].iloc[-1] if not resultats_df.empty else 0)
        epargne_investie = parse_value(get_value_safely(resultats_df, duree_capi_max, 'Épargne investie'))
        
        # Assurez-vous que toutes les valeurs sont des nombres
        capital_fin_annee_duree_capi_max = float(capital_fin_annee_duree_capi_max)
        capital_fin_annee_derniere_ligne = float(capital_fin_annee_derniere_ligne)
        epargne_investie = float(epargne_investie)
        
        # Affichage des valeurs
        self.set_font_safe('Inter', 'B', 10)
        self.set_text_color(*blue_color)
        self.cell(col_width, 6, f"{format_value(capital_fin_annee_duree_capi_max)}€", 0, 0, 'L')
        self.cell(col_width, 6, f"{format_value(capital_fin_annee_derniere_ligne)}€", 0, 0, 'L')
        self.set_text_color(*gold_color)
        self.cell(col_width, 6, f"{format_value(epargne_investie)}€", 0, 1, 'L')
        
        self.ln(10)

        # Dessiner les séparateurs verticaux
        separator_y1 = self.get_y() - 32  # Cette ligne définit le point de départ (haut) des séparateurs verticaux.
        separator_y2 = self.get_y() -5 # Cette ligne définit le point d'arrivée (bas) des séparateurs verticaux.
        self.set_draw_color(32, 32, 33)  # Couleur gris clair pour les séparateurs
        self.set_line_width(0.5)  # Set the line width to 0.5
        self.line(left_margin + col_width - 5, separator_y1, left_margin + col_width - 5, separator_y2)
        self.line(left_margin + 2 * col_width - 5, separator_y1, left_margin + 2 * col_width - 5, separator_y2)        

        # Vérifier s'il reste suffisamment d'espace pour le graphique
        if self.get_y() + 100 > self.h - 20:  # 100 est une estimation de la hauteur du graphique
            self.add_page()

        # Ajout du graphique en cascade
        chart_width = effective_width
        chart_height = 100  # Ajustez cette valeur selon vos besoins
        chart_x = left_margin
        chart_y = self.get_y()
    
        # Création et ajout du graphique en cascade
        try:
            waterfall_chart = create_waterfall_chart(resultats_df)
            chart_buffer = fig_to_img_buffer(waterfall_chart)
            
            # Créer un fichier temporaire pour stocker l'image
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                temp_filename = temp_file.name
                temp_file.write(chart_buffer.getvalue())
            
            # Ajoutez l'image au PDF en utilisant le fichier temporaire
            self.image(temp_filename, x=chart_x, y=chart_y, w=chart_width, h=chart_height)
            
            # Supprimez le fichier temporaire après utilisation
            os.unlink(temp_filename)
    
        except Exception as e:
            print(f"Erreur détaillée lors de la création du graphique en cascade : {e}")
            self.set_font_safe('Inter', '', 10)
            self.set_text_color(*text_color)
            self.multi_cell(effective_width, 10, f"Erreur lors de la création du graphique : {str(e)}", 0, 'C')
    
        self.ln(chart_height + 20)  # Espace après le graphique

         # Ajout du graphique financier
        self.add_page()
        financial_chart_width = effective_width
        financial_chart_height = 120  # Augmentez cette valeur si nécessaire
        financial_chart_y = self.get_y()
    
        try:
            financial_chart = create_financial_chart(resultats_df)
            financial_chart_buffer = fig_to_img_buffer(financial_chart)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                temp_filename = temp_file.name
                temp_file.write(financial_chart_buffer.getvalue())
            
            self.image(temp_filename, x=left_margin, y=financial_chart_y, w=financial_chart_width, h=financial_chart_height)
            os.unlink(temp_filename)
    
            # Ajouter un titre et un commentaire pour le graphique financier
            self.ln(financial_chart_height + 5)
            self.set_font('Inter', 'B', 14)
            self.cell(0, 10, "Évolution de votre placement financier", 0, 1, 'C')
            self.set_font('Inter', '', 10)
            self.multi_cell(0, 5, "Ce graphique illustre l'évolution de votre capital, de l'épargne investie et des rachats au fil du temps.")
            self.ln(10)
    
        except Exception as e:
            print(f"Erreur détaillée lors de la création du graphique financier : {e}")
            self.set_font_safe('Inter', '', 10)
            self.set_text_color(*text_color)
            self.multi_cell(effective_width, 10, f"Erreur lors de la création du graphique financier : {str(e)}", 0, 'C')
    
        # Ajout des graphiques donuts côte à côte
        self.add_page()
        chart_width = effective_width / 2 - 10  # La moitié de la largeur effective moins un petit espace entre les graphiques
        chart_height = 120  # Augmentez cette valeur pour agrandir les graphiques
        chart_y = self.get_y()
    
        # Titre général pour les graphiques donuts
        self.set_font('Inter', 'B', 16)
        self.cell(0, 10, "Répartition de votre capital", 0, 1, 'C')
        self.ln(5)
    
        # Création et ajout du premier graphique donut
        try:
            donut_chart1 = create_donut_chart(resultats_df, duree_capi_max)
            chart_buffer1 = fig_to_img_buffer(donut_chart1)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                temp_filename1 = temp_file.name
                temp_file.write(chart_buffer1.getvalue())
            
            self.image(temp_filename1, x=left_margin, y=chart_y, w=chart_width, h=chart_height)
            os.unlink(temp_filename1)
    
            # Titre et commentaire pour le premier graphique donut
            self.set_xy(left_margin, chart_y + chart_height + 5)
            self.set_font('Inter', 'B', 12)
            self.cell(chart_width, 10, "À la fin de la phase d'épargne", 0, 1, 'C')
            self.set_font('Inter', '', 10)
            self.multi_cell(chart_width, 5, "Répartition entre versements initiaux et plus-values à la fin de votre phase d'épargne.")
    
        except Exception as e:
            print(f"Erreur détaillée lors de la création du premier graphique donut : {e}")
            self.set_font_safe('Inter', '', 10)
            self.set_text_color(*text_color)
            self.multi_cell(chart_width, 10, f"Erreur lors de la création du graphique : {str(e)}", 0, 'C')
    
        # Création et ajout du deuxième graphique donut
        try:
            donut_chart2 = create_donut_chart2(resultats_df, objectifs)
            chart_buffer2 = fig_to_img_buffer(donut_chart2)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                temp_filename2 = temp_file.name
                temp_file.write(chart_buffer2.getvalue())
            
            self.image(temp_filename2, x=left_margin + chart_width + 20, y=chart_y, w=chart_width, h=chart_height)
            os.unlink(temp_filename2)
    
            # Titre et commentaire pour le deuxième graphique donut
            self.set_xy(left_margin + chart_width + 20, chart_y + chart_height + 5)
            self.set_font('Inter', 'B', 12)
            self.cell(chart_width, 10, "Au terme de vos projets", 0, 1, 'C')
            self.set_font('Inter', '', 10)
            self.multi_cell(chart_width, 5, "Répartition finale entre versements initiaux et plus-values après la réalisation de tous vos projets.")
    
        except Exception as e:
            print(f"Erreur détaillée lors de la création du deuxième graphique donut : {e}")
            self.set_font_safe('Inter', '', 10)
            self.set_text_color(*text_color)
            self.multi_cell(chart_width, 10, f"Erreur lors de la création du graphique : {str(e)}", 0, 'C')
    
        # Espace après les graphiques donuts
        self.ln(chart_height + 40)

    
    def set_font_safe(self, family, style='', size=0):
        try:
            self.set_font(family, style, size)
        except RuntimeError:
            # Si la police n'est pas trouvée, utilisez une police par défaut
            self.set_font('Arial', style, size)
    
    def clean_and_convert(self, value):
        if isinstance(value, str):
            cleaned = value.replace('€', '').replace(' ', '').replace(',', '.')
            try:
                return float(cleaned)
            except ValueError:
                print(f"Impossible de convertir la valeur: {value}")
                return value
        return value
    
    def calculer_duree_capi_max(self, objectifs, resultats_df):
        if not objectifs:
            return resultats_df['Année'].max() if not resultats_df.empty else 0
        max_annee_objectif = max(obj['annee'] for obj in objectifs)
        return min(max_annee_objectif, resultats_df['Année'].max()) if not resultats_df.empty else max_annee_objectif
        


import re

def parse_value(value):
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        # Supprimer le symbole € et les espaces
        value = value.replace('€', '').replace(' ', '').strip()
        # Remplacer la virgule par un point pour la décimale
        value = value.replace(',', '.')
        # Utiliser une expression régulière pour extraire le nombre
        match = re.search(r'-?\d+\.?\d*', value)
        if match:
            return float(match.group())
    return 0

def format_value(value):
    value = parse_value(value)
    if isinstance(value, (int, float)):
        return f"{value:,.2f}".replace(",", " ").replace(".", ",")
    return str(value)


def generate_pdf_report(resultats_df, params, objectives):
    data = [
        ["Paramètre", "Valeur"],
        ["Capital initial", f"{params['capital_initial']} €"],
        ["Versement mensuel", f"{params['versement_mensuel']} €"],
        ["Rendement annuel", f"{params['rendement_annuel']*100:.2f}%"],
    ]

    # Ajouter les informations des objectifs à data
    for i, obj in enumerate(objectives, start=1):
        data.extend([
            [f"Objectif {i} - Nom", obj['nom']],
            [f"Objectif {i} - Montant annuel", f"{obj['montant_annuel']} €"],
            [f"Objectif {i} - Année de réalisation", str(obj['annee'])],
            [f"Objectif {i} - Durée", f"{obj['duree_retrait']} ans"]
        ])

    # Générer les graphiques
    img_buffer1 = fig_to_img_buffer(create_financial_chart(resultats_df))
    img_buffer2 = fig_to_img_buffer(create_waterfall_chart(resultats_df))
    img_buffer3 = fig_to_img_buffer(create_donut_chart(resultats_df, duree_capi_max))
    img_buffer4 = fig_to_img_buffer(create_donut_chart2(resultats_df))
    
    
    # Créer le PDF
    pdf_bytes = create_pdf(data, [img_buffer1, img_buffer2, img_buffer3, img_buffer4], resultats_df, params, objectives)
    
    return pdf_bytes






def create_pdf(data, img_buffers, resultats_df, params, objectives):
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=20)

    # Couleurs inspirées d'Apple
    apple_blue = (0, 122, 255)
    apple_gray = (142, 142, 147)
    apple_light_gray = (242, 242, 247)
    blue_one = (22, 66, 91)

    def add_image_to_pdf(pdf, img_buffer, x, y, w, h):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
            img = Image.open(img_buffer)
            img = img.resize((int(w * 300 / 25.4), int(h * 300 / 25.4)), Image.LANCZOS)
            img.save(temp_file.name, format='PNG')
            pdf.image(temp_file.name, x=x, y=y, w=w, h=h)
        os.unlink(temp_file.name)

    # Page de couverture
    pdf.add_page()
    pdf.set_font('Inter', 'B', 32)
    pdf.set_text_color(*apple_blue)
    pdf.cell(0, 60, 'Rapport Financier', 0, 1, 'C')
    pdf.set_font('Inter', '', 18)
    pdf.set_text_color(*apple_gray)
    pdf.cell(0, 10, 'Analyse personnalisée de votre investissement', 0, 1, 'C')

    pdf.add_warning()

    pdf.add_objectives_section(objectives)


    # Génération des résultats
    resultats_df = optimiser_objectifs(params, objectifs)
    # Appel de la méthode avec les arguments requis
    pdf.add_simulation_parameters(params, resultats_df, objectives)

    
    
    
    # Tableau détaillé
    pdf.create_detailed_table(resultats_df)
    
    pdf.add_page()
    pdf.add_track_record_image('assets/Track_record.png')
    pdf.add_objectives_image('assets/Autres_objectifs.png')
    
    

    return pdf.output(dest='S').encode('latin-1', errors='replace')
    

def main():
    global resultats_df, params

    # Exemple de bouton pour générer le PDF
    if st.button("Générer le rapport PDF"):
        try:
            pdf_bytes = generate_pdf_report(resultats_df, params, st.session_state.objectifs)
            
            # Créer un lien de téléchargement pour le PDF
            b64 = base64.b64encode(pdf_bytes).decode()
            href = f'<a href="data:application/pdf;base64,{b64}" download="Votre simulation personnalisée">Télécharger le rapport PDF</a>'
            st.markdown(href, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Une erreur s'est produite lors de la génération du PDF : {str(e)}")
            print(f"Detailed error: {e}")

if __name__ == "__main__":
    main()





