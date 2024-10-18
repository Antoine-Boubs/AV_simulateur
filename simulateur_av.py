import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import math
from streamlit_extras.card import card
from plotly.subplots import make_subplots
import plotly.io as pio

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










































































import textwrap
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
import base64
from io import BytesIO
import os
from PIL import Image
import io
import numpy as np
import tempfile


class PDF(FPDF):
    def __init__(self, logo_path=None):
        super().__init__()
        self.logo_path = logo_path
        self.is_custom_font_loaded = False
        
        font_path = os.path.join(os.path.dirname(__file__), "assets/Fonts")
        logo_path = os.path.join(os.path.dirname(__file__), "assets/Logo1.png")

        
        try:
            self.add_font('Inter', '', os.path.join(font_path, 'Inter-Regular.ttf'), uni=True)
            self.add_font('Inter', 'B', os.path.join(font_path, 'Inter-Bold.ttf'), uni=True)
            self.add_font('Inter', 'I', os.path.join(font_path, 'Inter-Italic.ttf'), uni=True)
            self.is_custom_font_loaded = True
        except Exception as e:
            print(f"Error loading custom fonts: {e}")
            print("Falling back to built-in fonts.")

    def set_font_safe(self, family, style='', size=0):
        try:
            if self.is_custom_font_loaded:
                self.set_font(family, style, size)
            else:
                if family == 'Inter':
                    family = 'Arial'
                self.set_font(family, style, size)
        except Exception as e:
            print(f"Error setting font: {e}")
            print("Falling back to default font.")
            self.set_font('Arial', '', 12)

    def header(self):
        if self.logo_path and os.path.exists(self.logo_path):
            try:
                self.image(self.logo_path, 10, 10, 20)
                self.link(10, 10, 20, 20, "https://www.antoineberjoan.com")
            except Exception as e:
                print(f"Error loading logo: {e}")
        
        self.set_font_safe('Inter', 'B', 14)
        self.set_text_color(251, 191, 36)
        self.set_xy(35, 10)
        self.cell(0, 8, 'Antoine Berjoan', 0, 1, 'L')
        
        self.set_font_safe('Inter', '', 10)
        self.set_text_color(100, 100, 100)
        self.set_xy(35, 18)
        self.cell(0, 8, 'Conseiller en investissement', 0, 1, 'L')

        self.styled_button('Prendre RDV', 'https://app.lemcal.com/@antoineberjoan', self.w - 60, 10, 50, 15)

        self.set_draw_color(200, 200, 200)
        self.line(10, 35, self.w - 10, 35)

        self.ln(30)

    def styled_button(self, text, url, x, y, w, h):
        self.set_fill_color(251, 191, 36)
        self.rounded_rect(x, y, w, h, 2, 'F')

        self.set_draw_color(200, 150, 0)
        self.set_line_width(0.5)
        self.rounded_rect(x, y, w, h, 2, 'D')

        self.set_font_safe('Inter', 'B', 10)
        self.set_text_color(255, 255, 255)
        self.set_xy(x, y)
        self.cell(w, h, text, 0, 0, 'C')

        self.link(x, y, w, h, url)

    def rounded_rect(self, x, y, w, h, r, style=''):
        if style == 'F':
            self.rect(x, y, w, h, style)
        elif style == 'D' or style == '':
            self.rect(x, y, w, h)
        else:
            self.rect(x, y, w, h, 'FD')

    def footer(self):
        self.set_y(-15)
        
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), self.w - 10, self.get_y())
        
        self.set_y(self.get_y() + 1)
        
        self.set_font_safe('Inter', 'I', 7)
        
        self.set_text_color(128, 128, 128)
        
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'R')
        
        legal_text = (
            "RCS Chambéry n° 837 746 528 - Orias n° 21008012 - www.orias.fr "
            "Conseil en Investissements Financiers membre de la CNCEF, chambre agréée par l'AMF - "
            "Mandataire d'intermédiaire en assurance - Mandataire d'intermédiaire en opérations de banque et services de paiement "
            "Transactions sur Immeubles sans réception de fonds Carte n° CPI34022017000021580 délivrée par la CCI de Hérault "
            "Sous le contrôle de l'ACPR // Garantie Financière et Assurance Responsabilité Civile Professionnelle conformes au Code des Assurances"
        )
        
        line_width = self.w - 20
        
        self.set_xy(10, self.h)
        total_height = self.get_y()
        self.multi_cell(line_width, 3, legal_text, 0, 'L')
        total_height = self.get_y() - total_height
        
        self.set_y(-15 - total_height)
        self.multi_cell(line_width, 3, legal_text, 0, 'L')

    def get_string_height(self, width, txt):
        lines = self.multi_cell(width, 3, txt, 0, 'L', 0, output='text')
        return len(lines.split('\n')) * 3

    def add_warning(self):
        self.ln(10)
        
        margin = 20
        self.set_left_margin(margin)
        self.set_right_margin(margin)
        
        self.set_fill_color(240, 240, 240)
        self.rect(margin, self.get_y(), self.w - 2*margin, 50, 'F')
        
        self.set_xy(margin + 5, self.get_y() + 5)
        self.set_font_safe('Inter', 'B', 12)
        self.set_text_color(0, 0, 0)
        self.cell(0, 10, 'AVERTISSEMENT', 0, 1)
        
        self.set_xy(margin + 5, self.get_y())
        self.set_font_safe('Inter', '', 10)
        self.multi_cell(self.w - 2*margin - 10, 5, "La simulation de votre investissement est non contractuelle. L'investissement sur les supports "
                              "en unités de compte supporte un risque de perte en capital puisque leur valeur est sujette à "
                              "fluctuation à la hausse comme à la baisse dépendant notamment de l'évolution des marchés "
                              "financiers. L'assureur s'engage sur le nombre d'unités de compte et non sur leur valeur qu'il "
                              "ne garantit pas. Les performances passées ne préjugent pas des performances futures et ne "
                              "sont pas stables dans le temps.", align='J')

    def add_recap(self, params, objectives):
        self.add_page()
        self.set_font_safe('Inter', 'B', 16)
        self.cell(0, 10, 'Récapitulatif de votre projet', 0, 1, 'C')
        self.ln(5)

        self.set_font_safe('Inter', 'B', 14)
        self.cell(0, 10, 'Informations du client', 0, 1, 'L')
        self.set_font_safe('Inter', '', 12)
        self.cell(0, 8, f"Capital initial : {params['capital_initial']} €", 0, 1)
        self.cell(0, 8, f"Versement mensuel : {params['versement_mensuel']} €", 0, 1)
        self.cell(0, 8, f"Rendement annuel : {params['rendement_annuel']*100:.2f}%", 0, 1)

        self.ln(5)
        self.set_font_safe('Inter', 'B', 14)
        self.cell(0, 10, 'Versements', 0, 1, 'L')
        self.set_font_safe('Inter', '', 12)

        if 'versements_libres' in st.session_state and st.session_state.versements_libres:
            self.set_font_safe('Inter', 'B', 12)
            self.cell(0, 8, "Versements libres :", 0, 1)
            self.set_font_safe('Inter', '', 12)
            for vl in st.session_state.versements_libres:
                self.cell(0, 8, f"Année {vl['annee']} : {vl['montant']} €", 0, 1)

        if 'modifications_versements' in st.session_state and st.session_state.modifications_versements:
            self.set_font_safe('Inter', 'B', 12)
            self.cell(0, 8, "Modifications de versements :", 0, 1)
            self.set_font_safe('Inter', '', 12)
            for mv in st.session_state.modifications_versements:
                if mv['montant'] == 0:
                    self.cell(0, 8, f"Versements arrêtés de l'année {mv['debut']} à {mv['fin']}", 0, 1)
                else:
                    self.cell(0, 8, f"Versements modifiés à {mv['montant']} € de l'année {mv['debut']} à {mv['fin']}", 0, 1)

        if (not 'versements_libres' in st.session_state or not st.session_state.versements_libres) and \
           (not 'modifications_versements' in st.session_state or not st.session_state.modifications_versements):
            self.cell(0, 8, "Aucun versement libre ou modification de versement défini", 0, 1)

        self.ln(5)
        self.set_font_safe('Inter', 'B', 14)
        self.cell(0, 10, 'Vos objectifs', 0, 1, 'L')
        self.set_font_safe('Inter', '', 12)
        for obj in objectives:
            self.set_font_safe('Inter', 'B', 12)
            self.cell(0, 8, f"Objectif : {obj['nom']}", 0, 1)
            self.set_font_safe('Inter', '', 12)
            self.cell(0, 8, f"Montant annuel de retrait : {obj['montant_annuel']} €", 0, 1)
            self.cell(0, 8, f"Durée : {obj['duree_retrait']} ans", 0, 1)
            self.cell(0, 8, f"Année de réalisation : {obj['annee']}", 0, 1)
            self.ln(5)
        self.add_page()

    def colored_table(self, headers, data, col_widths):
        header_color = (240, 240, 240)
        row_colors = [(255, 255, 255), (245, 245, 245)]
        self.set_fill_color(*header_color)
        self.set_text_color(0)
        self.set_draw_color(128, 128, 128)
        self.set_line_width(0.3)
        self.set_font_safe('Inter', 'B', 8)

        total_width = sum(col_widths)
        table_x = (self.w - total_width) / 2

        self.set_x(table_x)
        for i, (header, width) in enumerate(zip(headers, col_widths)):
            self.cell(width, 10, header, 1, 0, 'C', 1)
        self.ln()

        self.set_font_safe('Inter', '', 8)
        row_height = 6
        page_rows = 0
        fill_index = 0

        for row in data:
            if page_rows == 30:
                self.add_page()
                self.set_x(table_x)
                self.set_fill_color(*header_color)
                self.set_font_safe('Inter', 'B', 8)
                for header, width in zip(headers, col_widths):
                    self.cell(width, 10, header, 1, 0, 'C', 1)
                self.ln()
                self.set_font_safe('Inter', '', 8)
                page_rows = 0
                fill_index = 0

            self.set_x(table_x)
            self.set_fill_color(*row_colors[fill_index % 2])
            for i, (value, width) in enumerate(zip(row, col_widths)):
                align = 'C' if i == 0 else 'R'
                self.cell(width, row_height, str(value), 1, 0, align, 1)
            self.ln()
            fill_index += 1
            page_rows += 1

    def add_last_page(self):
        self.add_page()
        margin = 20
        self.set_left_margin(margin)
        self.set_right_margin(margin)
        effective_width = self.w - 2*margin

        self.set_font_safe('Inter', '', 10)
        self.set_text_color(0, 0, 0)

        content = [
            "Avec Nalo, vos investissements sont réalisés au sein d'un contrat d'assurance-vie. Le contrat Nalo Patrimoine est assuré par Generali Vie. Vous profitez ainsi de la pérennité d'un acteur historique de l'assurance-vie. L'assurance-vie offre de nombreux avantages, parmi lesquels :",
            "• Une fiscalité avantageuse durant la vie et à votre succession : la fiscalité sur les gains réalisés est réduite, de plus, vous profitez d'un cadre fiscal avantageux lors de la transmission de votre patrimoine",
            "• La disponibilité de votre épargne : vous pouvez retirer (on parle de rachats), quand  vous le souhaitez, tout ou partie de l'épargne atteinte. Vous pouvez aussi effectuer des versements quand vous le souhaitez."
        ]

        for paragraph in content:
            self.multi_cell(effective_width, 5, paragraph, 0, 'L')
            self.ln(3)

        start_y = self.get_y()
        self.set_xy(margin + 5, start_y + 5)

        self.set_draw_color(200, 200, 200)
        self.rect(margin, start_y, effective_width, 0, 'D')

        self.set_font_safe('Inter', 'B', 12)
        self.cell(effective_width, 10, "Pour en savoir plus sur la fiscalité de  l'assurance-vie", 0, 1, 'L')
        self.ln(5)
        self.set_font_safe('Inter', '', 10)

        info_content = [
            "Lors d'un retrait (rachat), la somme reçue contient une part en capital et une part en plus-values. La fiscalité s'applique sur les plus-values et diffère selon l'ancienneté de votre contrat d'assurance-vie au moment du retrait. L'imposition est la suivante :",
            "• Contrat de moins de 8 ans : 12,80 % ou intégration aux revenus du foyer avec application du barème progressif de l'impôt sur le revenu.",
            "• Contrat de plus de 8 ans, et après abattement, sur les plus-values réalisées, de 4 600 €* pour les veufs ou célibataires et de 9 200 €* pour les personnes mariées ou pacsées :",
            "  ○ 7,5 % de prélèvement sur la part des versements ne dépassant pas 150 000 €* ;",
            "  ○ 12,8 % de prélèvement sur la part des versements dépassant 150 000 €* ;",
            "  ○ ou intégration aux revenus du foyer.",
            "Comptez aussi des prélèvements sociaux à hauteur de 17,2 % sur les plus-values réalisées, prélevés par l'assureur lors du rachat.",
            "* Toutes assurances - vie du foyer confondues.",
            "Par ailleurs, vous profitez d'un cadre fiscal avantageux lors de la transmission de votre patrimoine."
        ]

        for paragraph in info_content:
            self.multi_cell(effective_width, 5, paragraph, 0, 'L')
            self.ln(3)

        end_y = self.get_y()
        self.rect(margin, start_y, effective_width, end_y - start_y, 'D')

        self.set_y(end_y + 5)

        self.set_font_safe('Inter', '', 10)
        self.set_text_color(200, 80, 20)
        self.cell(0, 5, 'Pour en savoir plus, cliquez ici.', 0, 1, 'R', link="https://www.example.com")

        self.set_y(-30)
        self.set_font_safe('Inter', 'B', 10)
        self.cell(effective_width / 2, 10, 'Contact: 0183812655 | service.clients@nalo.fr', 0, 0, 'L')
        
        if self.logo_path and os.path.exists(self.logo_path):
            try:
                self.image(self.logo_path, x=self.w - margin - 20, y=self.h - 30, w=20)
            except Exception as e:
                print(f"Error adding logo to last page: {e}")
                
def generate_chart1(resultats_df):
    fig1 = go.Figure()

    years = resultats_df['Année'].tolist()
    capital_fin_annee = resultats_df['Capital fin d\'année (NET)'].str.replace(' €', '').astype(float).tolist()
    epargne_investie = resultats_df['Épargne investie'].str.replace(' €', '').astype(float).tolist()
    rachats = resultats_df['Rachat'].replace('[^\d.]', '', regex=True).astype(float).fillna(0).tolist()

    fig1.add_trace(go.Scatter(
        x=years, y=capital_fin_annee,
        mode='lines+markers',
        name='Capital fin d\'année',
        line=dict(color='#1f77b4', width=2)
    ))

    fig1.add_trace(go.Scatter(
        x=years, y=epargne_investie,
        mode='lines+markers',
        name='Épargne investie',
        line=dict(color='#2ca02c', width=2)
    ))

    fig1.add_trace(go.Bar(
        x=years, y=rachats,
        name='Rachats',
        marker_color='#d62728'
    ))

    fig1.update_layout(
        title='Évolution du placement financier',
        xaxis_title='Année',
        yaxis_title='Montant (€)',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        plot_bgcolor='white',
        yaxis=dict(
            gridcolor='lightgrey',
            zerolinecolor='lightgrey',
            tickformat='.0f',
            ticksuffix=' €'
        ),
        xaxis=dict(
            gridcolor='lightgrey',
            zerolinecolor='lightgrey'
        ),
        hovermode="x unified",
        barmode='relative'
    )

    img_bytes1 = fig1.to_image(format="png", width=800, height=500, scale=2)
    return io.BytesIO(img_bytes1)

def generate_chart2(resultats_df):
    fig2 = go.Figure(go.Waterfall(
        name="Evolution du capital",
        orientation="v",
        measure=["relative"] * len(resultats_df),
        x=resultats_df['Année'],
        y=resultats_df['Capital fin d\'année (NET)'].str.replace(' €', '').astype(float).diff(),
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        decreasing={"marker": {"color": "#CBA325"}},
        increasing={"marker": {"color": "#A33432"}},
        totals={"marker": {"color": "#F0D97A"}}
    ))
    fig2.update_layout(
        title='Évolution annuelle du capital',
        xaxis_title='Année',
        yaxis_title='Variation du capital (€)',
        plot_bgcolor='white',
        yaxis=dict(gridcolor='#8DB3C5')
    )
    
    img_bytes2 = fig2.to_image(format="png", width=700, height=400)
    return io.BytesIO(img_bytes2)

def generate_chart3():
    fig3 = go.Figure()
    years = [2019, 2020, 2021, 2022, 2023]
    performances = [22.69, -0.80, 25.33, -12.17, 11.91]

    fig3.add_trace(go.Bar(
        x=years,
        y=performances,
        text=[f"{p:+.2f}%" for p in performances],
        textposition='outside',
        marker_color=['#4CAF50' if p >= 0 else '#F44336' for p in performances],
        marker_line_color='rgba(0,0,0,0.5)',
        marker_line_width=1.5,
        opacity=0.8,
        name='Performance annuelle'
    ))

    cumulative_performance = np.cumprod(1 + np.array(performances) / 100) * 100 - 100
    fig3.add_trace(go.Scatter(
        x=years,
        y=cumulative_performance,
        mode='lines+markers',
        name='Performance cumulée',
        line=dict(color='#FFA500', width=3),
        marker=dict(size=8, symbol='diamond', line=dict(width=2, color='DarkSlateGrey')),
        yaxis='y2'
    ))

    fig3.update_layout(
        title={
            'text': 'Performances historiques',
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=24, color='#1E3A8A')
        },
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
        yaxis=dict(gridcolor='rgba(0,0,0,0.1)', zeroline=True, zerolinecolor='black', zerolinewidth=1.5),
        xaxis=dict(gridcolor='rgba(0,0,0,0.1)'),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=50, r=50, t=80, b=50),
        hovermode="x unified"
    )

    total_cumulative_performance = cumulative_performance[-1]
    fig3.add_annotation(
        x=0.5, y=1.15,
        xref='paper', yref='paper',
        text=f"Performance cumulée sur 5 ans : {total_cumulative_performance:.2f}%",
        showarrow=False,
        font=dict(size=16, color='#1E3A8A', weight='bold')
    )

    fig3.update_traces(
        hovertemplate="<b>Année:</b> %{x}<br><b>Performance:</b> %{text}<extra></extra>",
        selector=dict(type='bar')
    )
    fig3.update_traces(
        hovertemplate="<b>Année:</b> %{x}<br><b>Performance cumulée:</b> %{y:.2f}%<extra></extra>",
        selector=dict(type='scatter')
    )

    img_bytes3 = fig3.to_image(format="png", width=800, height=600, scale=2)
    return io.BytesIO(img_bytes3)

def generate_pdf_report(resultats_df, params, objectives):
    print("Entering generate_pdf_report")
    print(f"resultats_df shape: {resultats_df.shape}")
    print(f"params: {params}")
    print(f"objectives: {objectives}")

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
    img_buffer1 = generate_chart1(resultats_df)
    img_buffer2 = generate_chart2(resultats_df)
    img_buffer3 = generate_chart3()
    
    # Create the financial investment evolution chart
    fig1 = go.Figure()
    years = resultats_df['Année'].tolist()
    capital_fin_annee = resultats_df['Capital fin d\'année (NET)'].str.replace(' €', '').astype(float).tolist()
    epargne_investie = resultats_df['Épargne investie'].str.replace(' €', '').astype(float).tolist()
    rachats = resultats_df['Rachat'].replace('[^\d.]', '', regex=True).astype(float).fillna(0).tolist()

    fig1.add_trace(go.Scatter(
        x=years, y=capital_fin_annee,
        mode='lines+markers',
        name='Capital fin d\'année',
        line=dict(color='#1f77b4', width=2)
    ))

    fig1.add_trace(go.Scatter(
        x=years, y=epargne_investie,
        mode='lines+markers',
        name='Épargne investie',
        line=dict(color='#2ca02c', width=2)
    ))

    fig1.add_trace(go.Bar(
        x=years, y=rachats,
        name='Rachats',
        marker_color='#d62728'
    ))

    fig1.update_layout(
        title='Évolution du placement financier',
        xaxis_title='Année',
        yaxis_title='Montant (€)',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        plot_bgcolor='white',
        yaxis=dict(
            gridcolor='lightgrey',
            zerolinecolor='lightgrey',
            tickformat='.0f',
            ticksuffix=' €'
        ),
        xaxis=dict(
            gridcolor='lightgrey',
            zerolinecolor='lightgrey'
        ),
        hovermode="x unified",
        barmode='relative'
    )

    img_bytes1 = fig1.to_image(format="png", width=800, height=500, scale=2)
    img_buffer1 = io.BytesIO(img_bytes1)
    img_buffer1.seek(0)  # Rembobiner le buffer

    # Create the second chart (waterfall)
    fig2 = go.Figure(go.Waterfall(
        name="Evolution du capital",
        orientation="v",
        measure=["relative"] * len(resultats_df),
        x=resultats_df['Année'],
        y=resultats_df['Capital fin d\'année (NET)'].str.replace(' €', '').astype(float).diff(),
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        decreasing={"marker": {"color": "#CBA325"}},
        increasing={"marker": {"color": "#A33432"}},
        totals={"marker": {"color": "#F0D97A"}}
    ))
    fig2.update_layout(
        title='Évolution annuelle du capital',
        xaxis_title='Année',
        yaxis_title='Variation du capital (€)',
        plot_bgcolor='white',
        yaxis=dict(gridcolor='#8DB3C5')
    )

    img_bytes2 = fig2.to_image(format="png", width=700, height=400)
    img_buffer2 = io.BytesIO(img_bytes2)
    img_buffer2.seek(0)  # Rembobiner le buffer

    # Create the third chart (historical performance)
    fig3 = go.Figure()
    years = [2019, 2020, 2021, 2022, 2023]
    performances = [22.69, -0.80, 25.33, -12.17, 11.91]

    fig3.add_trace(go.Bar(
        x=years,
        y=performances,
        text=[f"{p:+.2f}%" for p in performances],
        textposition='outside',
        marker_color=['#4CAF50' if p >= 0 else '#F44336' for p in performances],
        marker_line_color='rgba(0,0,0,0.5)',
        marker_line_width=1.5,
        opacity=0.8,
        name='Performance annuelle'
    ))

    cumulative_performance = np.cumprod(1 + np.array(performances) / 100) * 100 - 100
    fig3.add_trace(go.Scatter(
        x=years,
        y=cumulative_performance,
        mode='lines+markers',
        name='Performance cumulée',
        line=dict(color='#FFA500', width=3),
        marker=dict(size=8, symbol='diamond', line=dict(width=2, color='DarkSlateGrey')),
        yaxis='y2'
    ))

    fig3.update_layout(
        title={
            'text': 'Performances historiques',
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=24, color='#1E3A8A')
        },
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
        yaxis=dict(gridcolor='rgba(0,0,0,0.1)', zeroline=True, zerolinecolor='black', zerolinewidth=1.5),
        xaxis=dict(gridcolor='rgba(0,0,0,0.1)'),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=50, r=50, t=80, b=50),
        hovermode="x unified"
    )

    total_cumulative_performance = cumulative_performance[-1]
    fig3.add_annotation(
        x=0.5, y=1.15,
        xref='paper', yref='paper',
        text=f"Performance cumulée sur 5 ans : {total_cumulative_performance:.2f}%",
        showarrow=False,
        font=dict(size=16, color='#1E3A8A', weight='bold')
    )

    fig3.update_traces(
        hovertemplate="<b>Année:</b> %{x}<br><b>Performance:</b> %{text}<extra></extra>",
        selector=dict(type='bar')
    )
    fig3.update_traces(
        hovertemplate="<b>Année:</b> %{x}<br><b>Performance cumulée:</b> %{y:.2f}%<extra></extra>",
        selector=dict(type='scatter')
    )

    img_bytes3 = fig3.to_image(format="png", width=800, height=600, scale=2)
    img_buffer3 = io.BytesIO(img_bytes3)
    img_buffer3.seek(0)  # Rembobiner le buffer

    # Créer le PDF
    pdf_bytes = create_pdf(data, [img_buffer1, img_buffer2, img_buffer3], resultats_df, params, objectives)

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
from PIL import Image

def create_pdf(data, img_buffers, resultats_df, params, objectives):
    logo_path = os.path.join(os.path.dirname(__file__), "Logo1.png")
    if not os.path.exists(logo_path):
        print(f"Warning: Logo file not found at {logo_path}")
        logo_path = None

    pdf = PDF(logo_path)
    left_margin = 20
    pdf.set_left_margin(left_margin)
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.add_warning()
    pdf.ln(20)
    pdf.set_auto_page_break(auto=True, margin=15)

    for i, img_buffer in enumerate(img_buffers):
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
                img = Image.open(img_buffer)
                img.save(tmpfile.name, format="PNG")
                tmpfile.flush()
                
                pdf.add_page()
                if i == 2:  # Pour le troisième graphique (performances historiques)
                    pdf.set_font_safe('Inter', 'B', 14)
                    pdf.cell(0, 10, 'Performances historiques', 0, 1)
                    pdf.set_font_safe('Inter', '', 12)
                    pdf.multi_cell(0, 5, 'Performance historique indicative basée sur la stratégie générale recommandée. '
                                         'Cette simulation illustre les résultats potentiels si ce projet avait été initié en 2019, '
                                         "en suivant l'allocation d'actifs standard proposée par Antoine Berjoan. "
                                         "Il est important de noter qu'aucune stratégie personnalisée ou ajustement spécifique "
                                         "n'a été pris en compte dans ce calcul. Une approche sur mesure, adaptée à votre profil "
                                         'individuel et réactive aux évolutions du marché, pourrait potentiellement générer des '
                                         'performances supérieures.')
                pdf.image(tmpfile.name, x=10, y=pdf.get_y()+10, w=190)
        except Exception as e:
            print(f"Error adding image to PDF: {e}")

    pdf.set_font_safe('Inter', 'B', 14)
    pdf.set_x(left_margin)
    pdf.cell(0, 10, 'Informations du client', 0, 1, 'L')
    pdf.ln(5)

    pdf.set_font_safe('Inter', '', 12)
    info_text = [
        f"Capital initial : {params['capital_initial']} €",
        f"Versement mensuel : {params['versement_mensuel']} €",
        f"Rendement annuel : {params['rendement_annuel']*100:.2f}%",
        f"Durée de simulation : {len(resultats_df)} ans"
    ]

    for line in info_text:
        pdf.set_x(left_margin)
        pdf.cell(0, 8, line, 0, 1, 'L')

    pdf.add_page()
    pdf.set_font_safe('Inter', 'B', 14)
    pdf.cell(0, 10, 'Résumé des résultats', 0, 1)
    pdf.set_font_safe('Inter', '', 12)
    
    derniere_annee = resultats_df.iloc[-1]
    capital_final = float(derniere_annee['Capital fin d\'année (NET)'].replace(' €', '').replace(',', '.'))
    epargne_investie = float(derniere_annee['Épargne investie'].replace(' €', '').replace(',', '.'))
    gains_totaux = capital_final - epargne_investie
    
    resume_text = "Capital final : {}\n".format(derniere_annee['Capital fin d\'année (NET)'])
    resume_text += "Total des versements : {}\n".format(derniere_annee['Épargne investie'])
    resume_text += "Gains totaux : {:.2f} €".format(gains_totaux)
    
    pdf.multi_cell(0, 10, resume_text)
    
    pdf.add_recap(params, objectives)
    
    create_detailed_table(pdf, resultats_df)

    pdf.set_xy(10, pdf.get_y() + 10)
    pdf.set_font_safe('Inter', 'I', 8)
    pdf.multi_cell(0, 4, "Note: Ce tableau présente une vue détaillée de l'évolution de votre investissement année par année, "
                         "incluant les versements, les rendements, les frais, les rachats et leur impact fiscal. "
                         "Les valeurs sont arrondies à deux décimales près.")

    pdf.add_page()
    pdf.set_fill_color(240, 240, 240)
    pdf.set_draw_color(200, 200, 200)
    pdf.set_font_safe('Inter', 'B', 12)
    pdf.cell(0, 10, 'AVERTISSEMENT LÉGAL', 1, 1, 'C', 1)
    pdf.set_font_safe('Inter', 'I', 10)
    pdf.set_text_color(80, 80, 80)
    disclaimer_text = (
        "Les performances passées ne préjugent pas des performances futures. "
        "Ce document est fourni à titre informatif uniquement et ne constitue pas un conseil en investissement. "
        "Les résultats présentés sont des estimations potentielles destinées à faciliter la compréhension "
        "du développement de votre patrimoine. Nous vous recommandons de consulter un professionnel "
        "qualifié avant de prendre toute décision d'investissement."
    )
    pdf.multi_cell(0, 5, disclaimer_text, 1, 'J', 1)

    pdf.add_last_page()

    try:
        pdf_output = pdf.output(dest='S').encode('latin-1', errors='ignore')
    except UnicodeEncodeError:
        print("Warning: Some characters could not be encoded. They will be replaced.")
        pdf_output = pdf.output(dest='S').encode('latin-1', errors='replace')

    return pdf_output


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
