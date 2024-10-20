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

st.markdown(
    """
    <style>
    .radio-horizontal .stRadio > div {
        flex-direction: row;
    }
    </style>
    """,
    unsafe_allow_html=True
)

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

# CSS for Apple-inspired simple and elegant style
st.markdown("""
<style>
    .main {
        background-color: #f5f5f7;
    }
    .stApp {
        margin: 0 auto;
    }
    .card {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    .card-title {
        font-size: 18px;
        font-weight: 500;
        margin-bottom: 20px;
        color: #1d1d1f;
    }
    .stSlider > div > div > div {
        background-color: #0071e3;
    }
    .stSlider > div > div > div > div {
        background-color: #0077ed;
    }
    .stNumberInput > div > div > input {
        border-radius: 5px;
        border: 1px solid #d2d2d7;
    }
    .delete-button {
        background-color: #ff3b30;
        color: white;
        border: none;
        padding: 5px 10px;
        border-radius: 5px;
        cursor: pointer;
        float: right;
    }
    .delete-button:hover {
        background-color: #ff453a;
    }
    .action-button {
        background-color: #0071e3;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 20px;
        cursor: pointer;
        transition: background-color 0.3s;
    }
    .action-button:hover {
        background-color: #0077ed;
    }
</style>
""", unsafe_allow_html=True)

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

# Style personnalisé
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        border-radius: 20px;
    }
    .stTextInput>div>div>input {
        border-radius: 20px;
    }
    .stSlider>div>div>div>div {
        background-color: #f0f2f6;
    }
    .stSlider>div>div>div>div>div {
        background-color: #4e8cff;
    }
    .streamlit-expanderHeader {
        font-size: 1em;
        color: #31333F;
    }
</style>
""", unsafe_allow_html=True)



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

# CSS pour un design épuré et élégant
st.markdown("""
<style>
    .main {
        background-color: #f5f5f7;
        padding: 2rem;
        border-radius: 20px;
    }
    h1 {
        color: #1d1d1f;
        font-weight: 700;
        font-size: 2.5rem;
        margin-bottom: 2rem;
    }
    .stTextInput > div > div > input {
        border-radius: 10px;
        border: 1px solid #d2d2d7;
        padding: 0.5rem 1rem;
        font-size: 1rem;
    }
    .stSlider > div > div > div {
        background-color: #0071e3;
    }
    .stExpander {
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
        padding: 1rem;
        transition: all 0.3s ease;
    }
    .stExpander:hover {
        box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15);
    }
    .stButton > button {
        background-color: #0071e3;
        color: white;
        border-radius: 20px;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #0077ed;
    }
    .delete-button {
        color: #ff3b30;
        background: none;
        border: none;
        cursor: pointer;
        font-size: 1.2rem;
        transition: all 0.3s ease;
    }
    .delete-button:hover {
        color: #F1B8A2;
    }
</style>
""", unsafe_allow_html=True)


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





params = input_simulateur()
duree_totale = calculer_duree_totale(objectifs)

# Calcul du tableau avec les paramètres actuels et intégration des rachats
resultats_df = optimiser_objectifs(params, objectifs)

# Affichage des résultats avec les rachats
st.header("📊 Résultats de la simulation avec rachats")
st.dataframe(resultats_df)





def create_financial_chart(df: pd.DataFrame):
    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add traces
    fig.add_trace(
        go.Scatter(
            x=df['Année'],
            y=df['Capital fin d\'année (NET)'].str.replace(' €', '').astype(float),
            name='Capital fin d\'année',
            line=dict(color='#007AFF', width=3),
            mode='lines'
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(
            x=df['Année'],
            y=df['Épargne investie'].str.replace(' €', '').astype(float),
            name='Épargne investie',
            line=dict(color='#34C759', width=3),
            mode='lines'
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Bar(
            x=df['Année'],
            y=df['Rachat'].str.replace(' €', '').astype(float),
            name='Rachats',
            marker_color='#FF3B30',
            opacity=0.7
        ),
        secondary_y=True,
    )

    # Customize the layout
    fig.update_layout(
        title={
            'text': 'Évolution du placement financier',
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=24, color='#1D1D1F')
        },
        font=dict(family="SF Pro Display, Arial, sans-serif", size=14, color="#1D1D1F"),
        plot_bgcolor='white',
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=60, r=30, t=100, b=50),
    )

    # Update axes
    fig.update_xaxes(
        title_text="Année",
        showgrid=True,
        gridcolor='#E5E5EA',
        tickfont=dict(size=12)
    )

    fig.update_yaxes(
        title_text="Montant (€)",
        showgrid=True,
        gridcolor='#E5E5EA',
        tickfont=dict(size=12),
        secondary_y=False
    )

    fig.update_yaxes(
        title_text="Rachats (€)",
        showgrid=False,
        tickfont=dict(size=12),
        secondary_y=True
    )

    # Add range slider
    fig.update_layout(
        xaxis=dict(
            rangeslider=dict(visible=True),
            type="linear"
        )
    )

    # Use a template inspired by Apple's design
    pio.templates["apple"] = go.layout.Template(
        layout=go.Layout(
            colorway=['#007AFF', '#34C759', '#FF3B30', '#FF9500', '#AF52DE', '#000000'],
            font={'color': '#1D1D1F'},
        )
    )
    fig.update_layout(template="apple")

    return fig
st.plotly_chart(create_financial_chart(resultats_df), use_container_width=True)







def create_waterfall_chart(df: pd.DataFrame):
    # Traitement des données
    capital_fin_annee = df['Capital fin d\'année (NET)'].str.replace(' €', '').str.replace(',', '.').astype(float)
    yearly_change = capital_fin_annee.diff()
    yearly_change = yearly_change.fillna(capital_fin_annee.iloc[0])
    final_capital = capital_fin_annee.iloc[-1]

    # Création du graphique
    fig = go.Figure(go.Waterfall(
        name = "Evolution du capital",
        orientation = "v",
        measure = ["relative"] * len(df) + ["total"],
        x = df['Année'].tolist() + ["Total"],
        textposition = "outside",
        text = [f"{val:,.0f} €" for val in yearly_change] + [f"{final_capital:,.0f} €"],
        y = yearly_change.tolist() + [0],
        connector = {"line":{"color":"rgba(63, 63, 63, 0.2)"}},
        increasing = {"marker":{"color":"#34C759"}},
        decreasing = {"marker":{"color":"#FF3B30"}},
        totals = {"marker":{"color":"#007AFF"}},
    ))

    # Personnalisation du layout
    fig.update_layout(
        title = {
            'text': "Évolution du capital année par année",
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=24, color='#1D1D1F')
        },
        font=dict(family="SF Pro Display, Arial, sans-serif", size=14, color="#1D1D1F"),
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(
            title="Année",
            tickfont=dict(size=12),
            gridcolor='#E5E5EA'
        ),
        yaxis=dict(
            title="Variation du capital (€)",
            tickfont=dict(size=12),
            gridcolor='#E5E5EA',
            tickformat=',.0f'
        ),
        margin=dict(l=60, r=30, t=100, b=50),
        hoverlabel=dict(
            bgcolor="white",
            font_size=14,
            font_family="SF Pro Display, Arial, sans-serif"
        )
    )

    # Ajout d'un range slider
    fig.update_layout(
        xaxis=dict(
            rangeslider=dict(visible=True),
            type="linear"
        )
    )

    # Utilisation d'un template personnalisé inspiré d'Apple
    pio.templates["apple"] = go.layout.Template(
        layout=go.Layout(
            colorway=['#007AFF', '#34C759', '#FF3B30', '#FF9500', '#AF52DE', '#000000'],
            font={'color': '#1D1D1F'},
        )
    )
    fig.update_layout(template="apple")

    return fig

# Dans votre application Streamlit
st.plotly_chart(create_waterfall_chart(resultats_df), use_container_width=True)



import plotly.graph_objects as go
import plotly.io as pio
import pandas as pd

def create_donut_chart(df: pd.DataFrame, duree_capi_max: int):
    # Trouver l'année correspondant à duree_capi_max
    target_year = df[df['Année'] == duree_capi_max].iloc[0]

    # Calculer les valeurs nécessaires
    capital_final = float(target_year['Capital fin d\'année (NET)'].replace(' €', '').replace(',', ''))
    pourcentage_plus_value = float(target_year['%'].replace('%', '')) / 100  # Convertir le pourcentage en décimal
    plus_values = capital_final * pourcentage_plus_value
    versements = capital_final - plus_values

    if capital_final == 0:
        # Si le capital final est 0, afficher un message au lieu du graphique
        fig = go.Figure()
        fig.add_annotation(
            x=0.5, y=0.5,
            text="Pas de données à afficher",
            font=dict(size=20, family="SF Pro Display, Arial, sans-serif", color='#1D1D1F'),
            showarrow=False
        )
    else:
        # Créer le graphique en donut
        colors = ['#007AFF', '#34C759']
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
            textfont=dict(size=14, family="SF Pro Display, Arial, sans-serif"),
        )])

        # Calcul du pourcentage de croissance
        growth_percentage = (plus_values / versements * 100) if versements != 0 else 0
        growth_text = f"+{growth_percentage:.1f}%"

        fig.update_layout(
            annotations=[
                dict(text=f'<b>{capital_final:,.0f} €</b><br>Capital final', x=0.5, y=0.5, font_size=16, showarrow=False),
                dict(text=f'<b>{growth_text}</b><br>Plus-values', x=0.5, y=0.35, font_size=14, showarrow=False, font_color='#34C759')
            ]
        )

    fig.update_layout(
        title={
            'text': f"Composition du capital en année {duree_capi_max}",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=24, family="SF Pro Display, Arial, sans-serif", color='#1D1D1F')
        },
        font=dict(family="SF Pro Display, Arial, sans-serif", size=14, color='#1D1D1F'),
        paper_bgcolor='white',
        plot_bgcolor='white',
        showlegend=False,
    )

    pio.templates["apple"] = go.layout.Template(
        layout=go.Layout(
            colorway=['#007AFF', '#34C759', '#FF3B30', '#FF9500', '#AF52DE', '#000000'],
            font={'color': '#1D1D1F'},
        )
    )
    fig.update_layout(template="apple")

    return fig


# Dans votre application Streamlit
objectif_annee_max = calculer_duree_capi_max(objectifs)
duree_capi_max = objectif_annee_max  # Remplacez cette valeur par la durée capi max réelle
st.plotly_chart(create_donut_chart(resultats_df, duree_capi_max), use_container_width=True)



def create_historical_performance_chart():
        fig = go.Figure()
        years = [2019, 2020, 2021, 2022, 2023]
        performances = [22.69, -0.80, 25.33, -12.17, 11.91]
    
        fig.add_trace(go.Bar(
            x=years,
            y=performances,
            text=[f"{p:+.2f}%" for p in performances],
            textposition='outside',
            marker_color=['#34C759' if p >= 0 else '#FF3B30' for p in performances],  # Apple green and red
            marker_line_color='rgba(0,0,0,0.5)',
            marker_line_width=1.5,
            opacity=0.8,
            name='Performance annuelle'
        ))
    
        cumulative_performance = np.cumprod(1 + np.array(performances) / 100) * 100 - 100
        fig.add_trace(go.Scatter(
            x=years,
            y=cumulative_performance,
            mode='lines+markers',
            name='Performance cumulée',
            line=dict(color='#007AFF', width=3),  # Apple blue
            marker=dict(size=8, symbol='diamond', line=dict(width=2, color='#1D1D1F')),
            yaxis='y2'
        ))
    
        fig.update_layout(
            title={
                'text': 'Performances historiques',
                'y':0.95,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': dict(size=24, family="SF Pro Display, Arial, sans-serif", color='#1D1D1F')
            },
            font=dict(family="SF Pro Display, Arial, sans-serif", size=14, color='#1D1D1F'),
            xaxis_title='Année',
            yaxis_title='Performance annuelle (%)',
            yaxis2=dict(
                title='Performance cumulée (%)',
                overlaying='y',
                side='right',
                showgrid=False
            ),
            plot_bgcolor='rgba(240,240,240,0.5)',
            paper_bgcolor='white',
            yaxis=dict(gridcolor='rgba(0,0,0,0.1)', zeroline=True, zerolinecolor='#1D1D1F', zerolinewidth=1.5),
            xaxis=dict(gridcolor='rgba(0,0,0,0.1)'),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(l=50, r=50, t=100, b=50),  # Increased top margin
            hovermode="x unified"
        )
    
        total_cumulative_performance = cumulative_performance[-1]
        fig.add_annotation(
            x=0.5, y=1.12,
            xref='paper', yref='paper',
            text=f"Performance cumulée sur 5 ans : {total_cumulative_performance:.2f}%",
            showarrow=False,
            font=dict(size=16, family="SF Pro Display, Arial, sans-serif", color='#1D1D1F', weight='bold')
        )
    
        fig.update_traces(
            hovertemplate="<b>Année:</b> %{x}<br><b>Performance:</b> %{text}<extra></extra>",
            selector=dict(type='bar')
        )
        fig.update_traces(
            hovertemplate="<b>Année:</b> %{x}<br><b>Performance cumulée:</b> %{y:.2f}%<extra></extra>",
            selector=dict(type='scatter')
        )
    
        return fig



def fig_to_img_buffer(fig):
    img_bytes = pio.to_image(fig, format="png", width=1000, height=600, scale=2)
    return io.BytesIO(img_bytes)





































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



class PDF(FPDF):
    def __init__(self, logo_path=None):
        super().__init__()
       
        self.is_custom_font_loaded = False
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.logo_path = logo_path or os.path.join(current_dir, "assets", "Logo1.png")
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
        apple_blue = (0, 122, 255)
        apple_gray = (128, 128, 128)
        
        if os.path.exists(self.logo_path):
            self.image(self.logo_path, 10, 8, 25)
        
        self.set_font_safe('Inter', 'B', 24)
        self.set_text_color(*apple_blue)
        self.cell(0, 10, 'Rapport Financier', 0, 1, 'R')
        
        self.set_font_safe('Inter', '', 12)
        self.set_text_color(*apple_gray)
        self.cell(0, 10, f'Généré le {datetime.now().strftime("%d/%m/%Y")}', 0, 1, 'R')
        
        self.set_draw_color(229, 229, 234)
        self.line(10, 35, self.w - 10, 35)
        
        self.ln(20)

    def footer(self):
        apple_gray = (128, 128, 128)
        apple_blue = (0, 122, 255)
        
        self.set_y(-25)
        
        self.set_draw_color(229, 229, 234)
        self.line(10, self.get_y(), self.w - 10, self.get_y())
        
        self.set_font_safe('Inter', '', 8)
        self.set_text_color(*apple_gray)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
        
        self.set_y(-15)
        self.cell(0, 5, '© 2023 Votre Entreprise. Tous droits réservés.', 0, 0, 'C')
        self.set_y(-10)
        self.set_text_color(*apple_blue)
        self.cell(0, 5, 'www.votreentreprise.com', 0, 0, 'C', link="https://www.votreentreprise.com")

    def add_warning(self):
        # Sauvegarder la page actuelle
        current_page = self.page
        
        # Aller à la première page
        self.page = 1
        
        # Définir les couleurs
        warning_bg_color = (255, 247, 237)  # Couleur de fond légèrement orangée
        warning_border_color = (255, 149, 0)  # Couleur de bordure orange
        warning_text_color = (0, 0, 0)  # Texte en noir
    
        # Positionner l'avertissement en bas de la page
        self.set_y(-80)
    
        # Dessiner le rectangle arrondi
        self.set_fill_color(*warning_bg_color)
        self.set_draw_color(*warning_border_color)
        self.rounded_rect(10, self.get_y(), self.w - 20, 60, 5, 'FD')
    
        # Ajouter le texte d'avertissement
        self.set_xy(15, self.get_y() + 5)
        self.set_font('Inter', 'B', 12)
        self.set_text_color(*warning_text_color)
        self.cell(0, 10, 'AVERTISSEMENT', 0, 1)
        
        self.set_font('Inter', '', 9)
        self.multi_cell(self.w - 30, 4, "La simulation de votre investissement est non contractuelle. L'investissement sur les supports "
                        "en unités de compte supporte un risque de perte en capital puisque leur valeur est sujette à "
                        "fluctuation à la hausse comme à la baisse dépendant notamment de l'évolution des marchés "
                        "financiers. L'assureur s'engage sur le nombre d'unités de compte et non sur leur valeur qu'il "
                        "ne garantit pas. Les performances passées ne préjugent pas des performances futures et ne "
                        "sont pas stables dans le temps.", align='J')
        
        # Retourner à la page où nous étions
        self.page = current_page

    def add_recap(self, params, objectives):
        self.add_page()
        self.set_font_safe('Inter', 'B', 24)
        self.set_text_color(0, 0, 0)
        self.cell(0, 15, 'Récapitulatif de votre projet', 0, 1, 'C')
        self.ln(5)
        
        self.add_info_section("Informations du client", [
            f"Capital initial : {params['capital_initial']} €",
            f"Versement mensuel : {params['versement_mensuel']} €",
            f"Rendement annuel : {params['rendement_annuel']*100:.2f}%"
        ])
        
        versements = []
        if 'versements_libres' in params and params['versements_libres']:
            versements.append("Versements libres :")
            for vl in params['versements_libres']:
                versements.append(f"Année {vl['annee']} : {vl['montant']} €")
        if 'modifications_versements' in params and params['modifications_versements']:
            versements.append("Modifications de versements :")
            for mv in params['modifications_versements']:
                if mv['montant'] == 0:
                    versements.append(f"Versements arrêtés de l'année {mv['debut']} à {mv['fin']}")
                else:
                    versements.append(f"Versements modifiés à {mv['montant']} € de l'année {mv['debut']} à {mv['fin']}")
        if not versements:
            versements = ["Aucun versement libre ou modification de versement défini"]
        self.add_info_section("Versements", versements)
        
        self.add_info_section("Vos objectifs", [
            f"Objectif : {obj['nom']}\n  Montant annuel : {obj['montant_annuel']} €\n  Durée : {obj['duree_retrait']} ans\n  Année de réalisation : {obj['annee']}"
            for obj in objectives
        ])

    def add_info_section(self, title, content):
        apple_blue = (0, 122, 255)
        apple_dark_gray = (60, 60, 67)
        
        self.set_font_safe('Inter', 'B', 18)
        self.set_text_color(*apple_blue)
        self.cell(0, 12, title, 0, 1, 'L')
        
        self.set_font_safe('Inter', '', 12)
        self.set_text_color(*apple_dark_gray)
        for item in content:
            self.multi_cell(0, 8, item, 0, 'L')
        self.ln(10)

    def colored_table(self, headers, data, col_widths):
        header_color = (247, 247, 247)
        row_colors = [(255, 255, 255), (250, 250, 250)]
        self.set_fill_color(*header_color)
        self.set_text_color(60, 60, 67)
        self.set_draw_color(229, 229, 234)
        self.set_line_width(0.3)
        self.set_font_safe('Inter', 'B', 10)
        
        total_width = sum(col_widths)
        table_x = (self.w - total_width) / 2
        self.set_x(table_x)
        
        for i, (header, width) in enumerate(zip(headers, col_widths)):
            self.cell(width, 12, header, 1, 0, 'C', 1)
        self.ln()
        
        self.set_font_safe('Inter', '', 10)
        row_height = 8
        fill_index = 0
        for row in data:
            self.set_x(table_x)
            self.set_fill_color(*row_colors[fill_index % 2])
            for i, (value, width) in enumerate(zip(row, col_widths)):
                align = 'C' if i == 0 else 'R'
                self.cell(width, row_height, str(value), 1, 0, align, 1)
            self.ln()
            fill_index += 1

    def rounded_rect(self, x, y, w, h, r, style=''):
        '''Draw a rounded rectangle'''
        k = self.k
        hp = self.h
        if style == 'F':
            op = 'f'
        elif style == 'FD' or style == 'DF':
            op = 'B'
        else:
            op = 'S'
        
        # Approximate the curve with 8 line segments per corner
        nCorners = 8
        
        self._out('%.2F %.2F m' % ((x+r)*k, (hp-y)*k))
        
        for i in range(4):
            if i == 0:
                xc, yc = x+w-r, y+r
            elif i == 1:
                xc, yc = x+w-r, y+h-r
            elif i == 2:
                xc, yc = x+r, y+h-r
            else:
                xc, yc = x+r, y+r
            
            self._out('%.2F %.2F l' % ((xc + r)*k, (hp-yc)*k))
            
            for j in range(nCorners):
                angle = (j+1) * (pi/2) / nCorners
                self._out('%.2F %.2F l' % ((xc + r*cos(angle))*k, (hp-(yc + r*sin(angle)))*k))
        
        self._out(op)


    def add_nalo_page(self):
        self.add_page()
    
        margin = 20  # Consistent margin for the entire page
        self.set_left_margin(margin)
        self.set_right_margin(margin)
        effective_width = self.w - 2*margin
    
        text_color = (29, 29, 31)
        title_color = (0, 0, 0)
        warning_bg_color = (230, 230, 250)

        self.set_font_safe('Inter', '', 10)
        self.set_text_color(*text_color)
        self.multi_cell(effective_width, 5, "Nalo est un service d'investissements financiers innovant. En investissant avec Nalo, vous profitez de nombreux avantages :")
        self.ln(3)

        def add_section(title, content, x, y, width, max_height):
            self.set_xy(x, y)
            self.set_font_safe('Inter', 'B', 11)
            self.set_text_color(*title_color)
            self.cell(width, 6, title, ln=True)
            self.set_font_safe('Inter', '', 9)
            self.set_text_color(*text_color)
            
            # Ajuster la position x pour le contenu
            self.set_x(x)
            
            self.multi_cell(width, 4, content)
            return self.get_y()

        col_width = (effective_width - 20) / 2  # -20 pour tenir compte de l'espace entre les colonnes

        self.line(margin, self.get_y(), self.w - margin, self.get_y())
        self.ln(3)

        start_y = self.get_y()
        max_height = 50

        # Section 1
        y1 = add_section("UN INVESTISSEMENT SUR-MESURE", 
                    "Nalo vous permet d'investir en fonction de votre situation patrimoniale et de l'ensemble de vos objectifs financiers (achat immobilier, retraite, études des enfants, ou tout autre objectif). Pour chaque projet, vous disposez d'un investissement dédié et personnalisé au sein du même contrat d'assurance-vie.",
                    margin, start_y, col_width, max_height)

        # Section 2 (déplacée vers la droite)
        y2 = add_section("UNE SÉCURISATION PROGRESSIVE", 
                    "Pour mieux gérer votre prise de risque, nous opérons une sécurisation progressive de vos investissements au cours du temps. En fonction de vos projets, nous faisons en sorte que la proportion d'actifs peu risqués soit importante au moment où vous avez besoin de récupérer votre argent.",
                    margin + col_width + 20, start_y, col_width, max_height)

        next_y = max(y1, y2) + 5
        self.set_y(next_y)

        self.line(margin, self.get_y(), self.w - margin, self.get_y())
        self.ln(3)
        start_y = self.get_y()

        # Section 3
        y3 = add_section("UN CONSEIL INDÉPENDANT", 
                    "Nalo est une société de conseil en investissement financier, qui accompagne ses clients de manière indépendante. Nous ne touchons pas de rétrocessions en fonction des fonds d'investissement choisis, cela nous permet de vous conseiller sans conflit d'intérêts.",
                    margin, start_y, col_width, max_height)

        # Section 4 (déplacée vers la droite)
        y4 = add_section("UNE MÉTHODE EFFICACE", 
                    "Notre méthode d'investissement est le résultat de plusieurs décennies de recherches économiques, financières et mathématiques. Elle tire son efficacité des travaux de plusieurs prix Nobel d'économie. Nous optimisons vos allocations et nous adaptons vos investissements aux conditions économiques et financières.",
                    margin + col_width + 20, start_y, col_width, max_height)

        next_y = max(y3, y4) + 5
        self.set_y(next_y)

        # Avertissement
        warning_width = effective_width  # Use full width instead of 90%
        warning_x = margin  # Set to left margin
        warning_y = self.get_y() + 20  # Increased gap before warning
        warning_height = 35  # Reduced from 45

        self.set_fill_color(*warning_bg_color)
        self.rect(warning_x, warning_y, warning_width, warning_height, 'F')
        self.set_xy(warning_x + 10, warning_y + 2)  # Reduced from +3
        self.set_font_safe('Inter', 'B', 11)  # Slightly larger font
        self.cell(0, 4, "AVERTISSEMENT", ln=True)  # Reduced from 5
        self.set_xy(warning_x + 10, self.get_y())  # Removed +1 spacing
        self.set_font_safe('Inter', '', 9)
        self.multi_cell(warning_width - 20, 3, "La simulation de votre investissement est non contractuelle. L'investissement sur les supports en unités de compte supporte un risque de perte en capital puisque leur valeur est sujette à fluctuation à la hausse comme à la baisse dépendant notamment de l'évolution des marchés financiers. L'assureur s'engage sur le nombre d'unités de compte et non sur leur valeur qu'il ne garantit pas. Les performances passées ne préjugent pas des performances futures et ne sont pas stables dans le temps.")

    
    def add_performance_historique(self):
        self.add_page()
    
        margin = 15
        self.set_left_margin(margin)
        self.set_right_margin(margin)
        effective_width = self.w - 2*margin
    
        text_color = (29, 29, 31)
        title_color = (0, 0, 0)
    
        self.set_font_safe('Inter', 'B', 18)
        self.set_text_color(*title_color)
        self.cell(effective_width, 10, 'Performances historiques', 0, 1, 'L')
        self.ln(5)
    
        # Ajouter le divider ici
        self.set_draw_color(200, 200, 200)  # Couleur gris clair pour le divider
        self.line(margin, self.get_y(), self.w - margin, self.get_y())
        self.ln(10)  # Espace après le divider
    
        # Après avoir ajouté le titre "Performances historiques"
        #self.ln(5)  # Petit espace après le titre
        #self.set_draw_color(200, 200, 200)  # Couleur gris clair pour le divider
        #self.line(margin, self.get_y(), self.w - margin, self.get_y())
        #self.ln(10)  # Espace après le divider
    
        # Données de performance (5 dernières années)
        data = [
            (2019, 22.69),
            (2020, -0.80),
            (2021, 25.33),
            (2022, -12.17),
            (2023, 11.91),
        ]
    
        # Calcul de la performance cumulée
        cumulative_performance = 1
        for _, perf in data:
            cumulative_performance *= (1 + perf / 100)
        cumulative_performance = (cumulative_performance - 1) * 100
    
        # Section de commentaire (côté gauche)
        comment_width = effective_width * 0.45
        self.set_font_safe('Inter', '', 10)
        self.set_text_color(*text_color)
        self.multi_cell(comment_width, 5, "Rendement sur les 5 dernières années")
        self.ln(2)
        self.set_font_safe('Inter', 'B', 14)
        self.cell(comment_width, 8, f"Performance cumulée : {cumulative_performance:.2f}%", 0, 1)
        self.ln(2)
        self.set_font_safe('Inter', '', 11) # Update 1: Increased font size
        self.multi_cell(comment_width, 4, "Performance historique de la stratégie conseillée pour votre projet. C'est la performance que vous auriez eue en créant ce projet en 2019 : prenant en compte les changements d'allocation conseillés par Nalo.")
        self.ln(2)
        self.set_font_safe('Inter', '', 8)
        self.set_text_color(128, 128, 128)
        self.cell(comment_width, 4, "Source : Nalo", 0, 1)
    
        # Ajouter un divider
        self.ln(10)  # Espace avant le divider
        self.set_draw_color(200, 200, 200)  # Couleur gris clair pour le divider
        self.line(margin, self.get_y(), self.w - margin, self.get_y())
        self.ln(10)  # Espace après le divider
    
    
        # Graphique (côté droit)
        chart_width = effective_width * 0.55
        chart_height = 80
        chart_x = self.w - margin - chart_width
        chart_y = self.get_y() - 50  # Ajuster cette valeur pour aligner avec le texte
    
        # Dessiner le graphique
        bar_width = chart_width / len(data)
        max_performance = max(abs(perf) for _, perf in data)
        scale_factor = (chart_height / 2) / max_performance
    
        for i, (year, performance) in enumerate(data):
            x = chart_x + i * bar_width
            if performance >= 0:
                y = chart_y + chart_height / 2 - performance * scale_factor
                height = performance * scale_factor
                self.set_fill_color(140, 192, 132)  # Vert pour les performances positives
            else:
                y = chart_y + chart_height / 2
                height = -performance * scale_factor
                self.set_fill_color(255, 59, 48)  # Rouge pour les performances négatives
            
            self.rect(x, y, bar_width * 0.8, height, 'F')
            
            # Ajouter les étiquettes de performance
            self.set_font_safe('Inter', '', 8)
            self.set_text_color(0, 0, 0)
            perf_text = f"{'+' if performance > 0 else ''}{performance:.1f}%"
            text_width = self.get_string_width(perf_text)
            self.text(x + (bar_width - text_width) / 2, y - 2 if performance >= 0 else y + height + 8, perf_text)
            
            # Ajouter les années
            self.text(x + (bar_width - self.get_string_width(str(year))) / 2, chart_y + chart_height + 5, str(year))
    
        # Ajouter une ligne de base
        self.line(chart_x, chart_y + chart_height / 2, chart_x + chart_width, chart_y + chart_height / 2)

    
    def add_last_page(self):
        self.add_page()
        margin = 20
        self.set_left_margin(margin)
        self.set_right_margin(margin)
        effective_width = self.w - 2*margin
        
        self.set_font_safe('Inter', '', 11)
        self.set_text_color(60, 60, 67)
        
        content = [
            "Avec notre service, vos investissements sont réalisés au sein d'un contrat d'assurance-vie. Vous profitez ainsi de nombreux avantages, parmi lesquels :",
            "• Une fiscalité avantageuse durant la vie et à votre succession",
            "• La disponibilité de votre épargne : vous pouvez effectuer des retraits à tout moment",
            "• La possibilité d'effectuer des versements quand vous le souhaitez"
        ]
        
        for paragraph in content:
            self.multi_cell(effective_width, 6, paragraph, 0, 'L')
            self.ln(4)
        
        self.add_info_box(
            "Fiscalité de l'assurance-vie",
            [
                "• Contrat de moins de 8 ans : 12,80 % ou barème progressif de l'IR",
                "• Contrat de plus de 8 ans : 7,5 % ou 12,8 % selon les versements, avec abattements",
                "• Prélèvements sociaux : 17,2 % sur les plus-values"
            ]
        )
        
        self.set_y(-30)
        self.set_font_safe('Inter', 'B', 11)
        self.set_text_color(60, 60, 67)
        self.cell(effective_width / 2, 10, 'Contact: 01 23 45 67 89 | contact@votreentreprise.com', 0, 0, 'L')
        
        if os.path.exists(self.logo_path):
            self.image(self.logo_path, x=self.w - margin - 20, y=self.h - 30, w=20)

    def add_info_box(self, title, content):
        apple_blue = (0, 122, 255)
        apple_light_gray = (247, 247, 247)
        apple_dark_gray = (60, 60, 67)
        
        self.set_fill_color(*apple_light_gray)
        self.rect(self.l_margin, self.get_y(), self.w - self.l_margin - self.r_margin, 50, 'F')
        
        self.set_xy(self.l_margin + 5, self.get_y() + 5)
        self.set_font_safe('Inter', 'B', 14)
        self.set_text_color(*apple_blue)
        self.cell(0, 10, title, 0, 1)
        
        self.set_font_safe('Inter', '', 10)
        self.set_text_color(*apple_dark_gray)
        for item in content:
            self.set_x(self.l_margin + 5)
            self.multi_cell(self.w - self.l_margin - self.r_margin - 10, 5, item, 0, 'L')
        
        self.ln(10)


def format_value(value):
    if isinstance(value, (int, float)):
        formatted = f"{value:,.2f}".replace(",", " ").replace(".", ",")
        return f"{formatted} €"
    elif isinstance(value, str):
        try:
            num_value = float(value.replace(" ", "").replace(",", ".").replace("€", "").strip())
            return format_value(num_value)
        except ValueError:
            return value
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
    img_buffer4 = fig_to_img_buffer(create_historical_performance_chart())


    # Créer le PDF
    pdf_bytes = create_pdf(data, [img_buffer1, img_buffer2, img_buffer3, img_buffer4], resultats_df, params, objectives)

    return pdf_bytes



def format_value(value):
    if isinstance(value, (int, float)):
        formatted = f"{value:,.2f}".replace(",", " ").replace(".", ",")
        return f"{formatted} €"
    elif isinstance(value, str):
        try:
            num_value = float(value.replace(" ", "").replace(",", ".").replace("€", "").strip())
            return format_value(num_value)
        except ValueError:
            return value
    return str(value)


def create_detailed_table(pdf, resultats_df):
    pdf.add_page()
    pdf.set_font_safe('Inter', 'B', 14)
    pdf.cell(0, 10, 'Détails année par année', 0, 1, 'C')
    pdf.ln(5)
    col_widths = [12, 25, 20, 20, 20, 20, 20, 20, 25]
    headers = ['Année', 'Capital initial', 'Versements', 'Rendement', 'Frais', 'Rachats', 'Fiscalité', 'Rachat net', 'Capital final']
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
    pdf.colored_table(headers, data, col_widths)



import tempfile
import os
from PIL import Image
import io
from fpdf import FPDF

def create_pdf(data, img_buffers, resultats_df, params, objectives):
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=20)

    # Couleurs inspirées d'Apple
    apple_blue = (0, 122, 255)
    apple_gray = (142, 142, 147)
    apple_light_gray = (242, 242, 247)

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

    # Sommaire
    pdf.add_page()
    pdf.set_font('Inter', 'B', 24)
    pdf.set_text_color(*apple_blue)
    pdf.cell(0, 20, 'Sommaire', 0, 1, 'L')
    pdf.set_font('Inter', '', 14)
    pdf.set_text_color(*apple_gray)
    sommaire_items = [
        "1. Évolution du placement financier",
        "2. Composition du capital",
        "3. Analyse en cascade de l'évolution du capital",
        "4. Performances historiques",
        "5. Récapitulatif du projet",
        "6. Détails année par année"
    ]
    for item in sommaire_items:
        pdf.cell(0, 10, item, 0, 1, 'L')

    # Graphiques

    # Définition des titres et descriptions des graphiques
    graph_titles = [
        "Évolution du placement financier",
        "Composition du capital",
        "Analyse en cascade de l'évolution du capital",
        "Performances historiques"
    ]
    
    graph_descriptions = [
        "Ce graphique illustre l'évolution de votre capital, de l'épargne investie et des rachats au fil du temps. "
        "Il vous permet de visualiser la croissance de votre investissement et l'impact des retraits.",
        
        "Ce graphique en donut montre la répartition entre vos versements et les plus-values générées. "
        "Il met en évidence la croissance de votre capital au fil du temps.",
        
        "Ce graphique en cascade illustre les différentes étapes de l'évolution de votre capital, "
        "montrant l'impact de chaque facteur sur la valeur finale de votre investissement.",
        
        "Ce graphique présente les performances historiques de votre investissement. "
        "Il montre les variations annuelles ainsi que la performance cumulée sur la période."
    ]
    
    graph_width = 180
    graph_height = 100
    for i, (img_buffer, title) in enumerate(zip(img_buffers, graph_titles), start=1):
        pdf.add_page()
        pdf.set_font('Inter', 'B', 24)
        pdf.set_text_color(*apple_blue)
        pdf.cell(0, 20, f"{i}. {title}", 0, 1, 'L')
        add_image_to_pdf(pdf, img_buffer, x=15, y=pdf.get_y(), w=graph_width, h=graph_height)
        pdf.ln(graph_height + 15)
        pdf.set_font('Inter', '', 12)
        pdf.set_text_color(*apple_gray)
        pdf.multi_cell(0, 6, graph_descriptions[i-1], 0, 'L')

    # Récapitulatif du projet
    pdf.add_page()
    pdf.set_font('Inter', 'B', 24)
    pdf.set_text_color(*apple_blue)
    pdf.cell(0, 20, '5. Récapitulatif du projet', 0, 1, 'L')
    pdf.ln(10)
    pdf.set_fill_color(*apple_light_gray)
    pdf.rect(10, pdf.get_y(), 190, 100, 'F')
    pdf.set_xy(15, pdf.get_y() + 5)
    pdf.set_font('Inter', '', 12)
    pdf.set_text_color(*apple_gray)
    for key, value in params.items():
        pdf.cell(0, 8, f"{key}: {value}", 0, 1)
    pdf.ln(10)
    pdf.set_font('Inter', 'B', 14)
    pdf.cell(0, 10, 'Objectifs:', 0, 1)
    for obj in objectives:
        pdf.set_font('Inter', '', 12)
        for key, value in obj.items():
            pdf.cell(0, 8, f"{key}: {value}", 0, 1)
        pdf.ln(5)

    # Tableau détaillé
    pdf.add_page()
    pdf.set_font('Inter', 'B', 24)
    pdf.set_text_color(*apple_blue)
    pdf.cell(0, 20, '6. Détails année par année', 0, 1, 'L')
    create_detailed_table(pdf, resultats_df)

    # Note de bas de page
    pdf.set_y(-30)
    pdf.set_font('Inter', 'I', 10)
    pdf.set_text_color(*apple_gray)
    pdf.multi_cell(0, 5, "Note : Ce rapport est généré automatiquement et ne constitue pas un conseil financier. "
                         "Veuillez consulter un professionnel pour des conseils personnalisés.")

    pdf.add_nalo_page()

    pdf.add_performance_historique()  # Ajoutez cette ligne ici

    # Ajouter l'avertissement sur la page de couverture
    pdf.add_warning()

    # Ajouter la dernière page
    pdf.add_last_page()

    return pdf.output(dest='S').encode('latin-1', errors='replace')
    

def main():
    global resultats_df, params

    # Exemple de bouton pour générer le PDF
    if st.button("Générer le rapport PDF"):
        try:
            pdf_bytes = generate_pdf_report(resultats_df, params, st.session_state.objectifs)
            
            # Créer un lien de téléchargement pour le PDF
            b64 = base64.b64encode(pdf_bytes).decode()
            href = f'<a href="data:application/pdf;base64,{b64}" download="rapport_simulation_financiere.pdf">Télécharger le rapport PDF</a>'
            st.markdown(href, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Une erreur s'est produite lors de la génération du PDF : {str(e)}")
            print(f"Detailed error: {e}")

if __name__ == "__main__":
    main()





