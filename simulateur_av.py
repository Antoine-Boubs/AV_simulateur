import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import math


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
    with open("/Users/boubs/Downloads/VS/style2.css") as f:  
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

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

# Titre de l'application
st.title("📊 Simulation de votre placement")

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

# Initialisation des variables de session
if "versements_libres" not in st.session_state:
    st.session_state.versements_libres = []
if "modifications_versements" not in st.session_state:
    st.session_state.modifications_versements = []
if "show_stopper_interface" not in st.session_state:
    st.session_state.show_stopper_interface = False
if "show_modifier_interface" not in st.session_state:
    st.session_state.show_modifier_interface = False

# Fonction pour ajouter un versement libre
def ajouter_versement_libre():
    st.session_state.versements_libres.append({
        "annee": 5,
        "montant": 1000.0
    })

# Fonction pour supprimer un versement libre
def supprimer_versement_libre(index):
    st.session_state.versements_libres.pop(index)

# Fonction pour ajouter une modification de versement
def ajouter_modification_versement(debut, fin, montant):
    st.session_state.modifications_versements.append({
        "debut": debut,
        "fin": fin,
        "montant": montant
    })

# Fonction pour supprimer une modification de versement
def supprimer_modification_versement(index):
    st.session_state.modifications_versements.pop(index)

# Fonction pour afficher l'interface de stop des versements
def toggle_stopper_interface():
    st.session_state.show_stopper_interface = not st.session_state.show_stopper_interface
    st.session_state.show_modifier_interface = False

# Fonction pour afficher l'interface de modification des versements
def toggle_modifier_interface():
    st.session_state.show_modifier_interface = not st.session_state.show_modifier_interface
    st.session_state.show_stopper_interface = False

# Boutons pour gérer les versements
col1, col2, col3 = st.columns(3)
with col1:
    st.button("➕ Ajouter un versement libre", on_click=ajouter_versement_libre)
with col2:
    st.button("🛑 Stopper les versements", on_click=toggle_stopper_interface)
with col3:
    st.button("📊 Modifier les versements", on_click=toggle_modifier_interface)

# Affichage de tous les versements libres avec option de suppression
for i, versement in enumerate(st.session_state.versements_libres):
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        versement["annee"] = st.slider(f"Année du versement libre {i+1}", min_value=1, max_value=60, value=versement["annee"])
    with col2:
        versement["montant"] = st.number_input(f"Montant du versement libre {i+1} (€)", min_value=0.0, value=versement["montant"])
    with col3:
        st.button("❌ Supprimer", key=f"supprimer_libre_{i}", on_click=supprimer_versement_libre, args=(i,))

# Interface pour stopper les versements
if st.session_state.show_stopper_interface:
    st.subheader("Stopper les versements")
    debut, fin = st.slider("Sélectionnez la période d'arrêt des versements", 1, 60, (1, 5))
    if st.button("Confirmer l'arrêt des versements"):
        ajouter_modification_versement(debut, fin, 0)
        st.session_state.show_stopper_interface = False

# Interface pour modifier les versements
if st.session_state.show_modifier_interface:
    st.subheader("Modifier les versements")
    debut, fin = st.slider("Sélectionnez la période de modification des versements", 1, 60, (1, 5))
    nouveau_montant = st.number_input("Nouveau montant des versements mensuels", min_value=0.0, value=400.0)
    if st.button("Confirmer la modification des versements"):
        ajouter_modification_versement(debut, fin, nouveau_montant)
        st.session_state.show_modifier_interface = False

# Affichage des modifications de versements
if st.session_state.modifications_versements:
    st.subheader("Modifications des versements")
    for i, modification in enumerate(st.session_state.modifications_versements):
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
        with col1:
            st.write(f"Années : {modification['debut']} - {modification['fin']}")
        with col2:
            st.write(f"Montant : {modification['montant']} €")
        with col3:
            if modification['montant'] == 0:
                st.write("Versements arrêtés")
            else:
                st.write("Versements modifiés")
        with col4:
            st.button("❌", key=f"supprimer_modif_{i}", on_click=supprimer_modification_versement, args=(i,))


st.header("🎯 Objectifs financiers")

# Ajouter des objectifs spécifiques
objectifs = []
nombre_objectifs = st.number_input("Combien d'objectifs souhaitez-vous définir ?", min_value=1, max_value=10, value=1)

for i in range(1, nombre_objectifs + 1):
    st.subheader(f"Objectif {i}")
    objectif_nom = st.text_input(f"Nom de l'objectif {i}", f"Objectif {i}")
    objectif_annee = st.slider(f"Année de réalisation de l'objectif {objectif_nom}", min_value=1, max_value=60, value=i * 10)
    montant_annuel_retrait = st.number_input(f"Montant annuel à retirer pour {objectif_nom} (€)", min_value=0, value=5000)
    duree_retrait = st.number_input(f"Durée de retrait pour {objectif_nom} (années)", min_value=1, value=4)
    

    objectifs.append({
        "nom": objectif_nom,
        "annee": objectif_annee,
        "montant_annuel": montant_annuel_retrait,
        "duree_retrait": duree_retrait,
    })

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
    for j in range(objectif["duree_retrait"] if not math.isinf(objectif["duree_retrait"]) else len(df_test) - annee):
        if annee + j < len(df_test):
            df_test.at[annee + j, "Rachat"] += montant_rachat_annuel




def calculer_duree_capi_max (objectifs):
    objectif_annee_max = max(obj["annee"] for obj in objectifs)
    return objectif_annee_max

def calcul_rendement_versements_mensuels(versement_mensuel_investi, rendement_annuel):
    rendement_versements = 0
    for mois in range(12):
        prorata = (12 - mois) / 12  # Le mois de janvier est investi 12 mois, février 11 mois, etc.
        rendement_versements += (versement_mensuel_investi * prorata) * rendement_annuel
    return rendement_versements

def calculer_duree_totale(objectifs):
    # Calculer la durée maximale en fonction des objectifs
    duree_totale = max(obj["annee"] + obj["duree_retrait"] for obj in objectifs)
    return duree_totale

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
        for modification in st.session_state.modifications_versements:
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
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df['Année'],
        y=df['Capital fin d\'année (NET)'].str.replace(' €', '').astype(float),
        mode='lines+markers',
        name='Capital fin d\'année',
        line=dict(color='#1f77b4')
    ))

    fig.add_trace(go.Scatter(
        x=df['Année'],
        y=df['Épargne investie'].str.replace(' €', '').astype(float),
        mode='lines+markers',
        name='Épargne investie',
        line=dict(color='#2ca02c')
    ))

    fig.add_trace(go.Bar(
        x=df['Année'],
        y=df['Rachat'].str.replace(' €', '').astype(float),
        name='Rachats',
        marker_color='#d62728'
    ))

    fig.update_layout(
        title='Évolution du placement financier',
        xaxis_title='Année',
        yaxis_title='Montant (€)',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        hovermode='x unified',
        updatemenus=[dict(
            type='buttons',
            direction='left',
            buttons=[
                dict(args=[{'visible': [True, True, True]}], label='Tout afficher', method='update'),
                dict(args=[{'visible': [True, False, False]}], label='Capital fin d\'année', method='update'),
                dict(args=[{'visible': [False, True, False]}], label='Épargne investie', method='update'),
                dict(args=[{'visible': [False, False, True]}], label='Rachats', method='update')
            ],
            pad={'r': 10, 't': 10},
            showactive=True,
            x=0.1,
            xanchor='left',
            y=1.1,
            yanchor='top'
        )]
    )

    return fig
st.plotly_chart(create_financial_chart(resultats_df), use_container_width=True)







def create_waterfall_chart(df: pd.DataFrame):
    # Utiliser une méthode différente pour traiter la colonne 'Capital fin d'année (NET)'
    capital_fin_annee = df['Capital fin d\'année (NET)'].str.replace(' €', '').str.replace(',', '.').astype(float)
    
    yearly_change = capital_fin_annee.diff()
    yearly_change = yearly_change.fillna(capital_fin_annee.iloc[0])

    final_capital = capital_fin_annee.iloc[-1]

    fig = go.Figure(go.Waterfall(
        name = "Evolution du capital",
        orientation = "v",
        measure = ["relative"] * len(df) + ["total"],
        x = df['Année'].tolist() + ["Total"],
        textposition = "outside",
        text = [f"{val:,.2f} €" for val in yearly_change] + [f"{final_capital:,.2f} €"],
        y = yearly_change.tolist() + [0],
        connector = {"line":{"color":"rgb(63, 63, 63)"}},
    ))

    fig.update_layout(
        title = "Evolution du capital année par année",
        showlegend = False,
        xaxis_title = "Année",
        yaxis_title = "Variation du capital (€)"
    )

    return fig

# Dans votre application Streamlit
st.plotly_chart(create_waterfall_chart(resultats_df), use_container_width=True)














def create_donut_chart(df: pd.DataFrame):
    last_year = df.iloc[-1]
    capital_initial = float(last_year['Capital initial (NET)'].replace(' €', ''))
    interets = float(last_year['Capital fin d\'année (NET)'].replace(' €', '')) - capital_initial

    fig = go.Figure(data=[go.Pie(
        labels=['Capital initial', 'Intérêts cumulés'],
        values=[capital_initial, interets],
        hole=.4,
        textinfo='label+percent',
        insidetextorientation='radial'
    )])

    fig.update_layout(
        title_text="Répartition du capital final",
        annotations=[dict(text='Capital<br>final', x=0.5, y=0.5, font_size=20, showarrow=False)]
    )

    return fig

# Dans votre application Streamlit
st.plotly_chart(create_donut_chart(resultats_df), use_container_width=True)













def create_bubble_chart(df: pd.DataFrame):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df['Année'],
        y=df['Capital fin d\'année (NET)'].str.replace(' €', '').astype(float),
        mode='lines+markers',
        name='Capital fin d\'année',
        line=dict(color='blue'),
        marker=dict(size=10)
    ))

    fig.add_trace(go.Scatter(
        x=df['Année'],
        y=df['Rachat'].str.replace(' €', '').astype(float),
        mode='markers',
        name='Rachats',
        marker=dict(
            size=df['Rachat'].str.replace(' €', '').astype(float) / 100,
            sizemode='area',
            sizeref=2.*max(df['Rachat'].str.replace(' €', '').astype(float))/(40.**2),
            sizemin=4,
            color='red'
        )
    ))

    fig.update_layout(
        title='Evolution du capital et des rachats',
        xaxis_title='Année',
        yaxis_title='Montant (€)',
        showlegend=True
    )

    return fig

# Dans votre application Streamlit
st.plotly_chart(create_bubble_chart(resultats_df), use_container_width=True)














def create_stacked_area_chart(df: pd.DataFrame):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df['Année'], 
        y=df['Capital initial (NET)'].str.replace(' €', '').astype(float),
        mode='lines',
        line=dict(width=0.5, color='rgb(131, 90, 241)'),
        stackgroup='one',
        name='Capital initial'
    ))

    fig.add_trace(go.Scatter(
        x=df['Année'],
        y=df['VP NET'].str.replace(' €', '').astype(float).cumsum(),
        mode='lines',
        line=dict(width=0.5, color='rgb(111, 231, 219)'),
        stackgroup='one',
        name='Versements programmés'
    ))

    fig.add_trace(go.Scatter(
        x=df['Année'],
        y=df['Rendement'].str.replace(' €', '').astype(float).cumsum(),
        mode='lines',
        line=dict(width=0.5, color='rgb(184, 247, 212)'),
        stackgroup='one',
        name='Rendements cumulés'
    ))

    fig.update_layout(
        title='Composition du capital au fil du temps',
        xaxis_title='Année',
        yaxis_title='Montant (€)',
        yaxis_type='linear',
        showlegend=True
    )

    return fig

# Dans votre application Streamlit
st.plotly_chart(create_stacked_area_chart(resultats_df), use_container_width=True)








if st.button("Lancer la simulation"):
    resultats_df = optimiser_objectifs(params, objectifs)
    
    chart_type = st.selectbox(
        "Choisissez le type de graphique",
        ["Ligne et barre", "Cascade", "Anneau", "Bulles", "Aires empilées"]
    )
    
    if chart_type == "Ligne et barre":
        st.plotly_chart(create_financial_chart(resultats_df), use_container_width=True, key="line_bar_chart")
    elif chart_type == "Cascade":
        st.plotly_chart(create_waterfall_chart(resultats_df), use_container_width=True, key="waterfall_chart")
    elif chart_type == "Anneau":
        st.plotly_chart(create_donut_chart(resultats_df), use_container_width=True, key="donut_chart")
    elif chart_type == "Bulles":
        st.plotly_chart(create_bubble_chart(resultats_df), use_container_width=True, key="bubble_chart")
    elif chart_type == "Aires empilées":
        st.plotly_chart(create_stacked_area_chart(resultats_df), use_container_width=True, key="stacked_area_chart")
    
    # Display the results table
    st.write("Résultats détaillés de la simulation :")
    st.dataframe(resultats_df)












import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
import base64
from io import BytesIO
import os

class PDF(FPDF):
    def __init__(self):
        super().__init__()
        # Ajuster le chemin pour correspondre à votre structure de dossier
        fonts_path = os.path.join(os.path.dirname(__file__), 'Inter Streamlit', 'static')
        
        # Ajouter les polices Inter
        self.add_font('Inter', '', os.path.join(fonts_path, 'Inter-Regular.ttf'), uni=True)
        self.add_font('Inter', 'B', os.path.join(fonts_path, 'Inter-Bold.ttf'), uni=True)
        self.add_font('Inter', 'I', os.path.join(fonts_path, 'Inter-Italic.ttf'), uni=True)

    def header(self):
        self.set_font('Inter', 'B', 12)
        self.cell(0, 10, 'Rapport de Simulation Financière', 0, 1, 'C')

    def footer(self):
        self.set_y(-15)
        self.set_font('Inter', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', 0, 0, 'C')

def create_pdf(data, figures):
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Ajout des données utilisateur
    pdf.set_font('Inter', 'B', 14)
    pdf.cell(0, 10, 'Paramètres de simulation', 0, 1)
    pdf.set_font('Inter', '', 12)
    for row in data:
        pdf.cell(90, 10, row[0], 1)
        pdf.cell(90, 10, row[1], 1)
        pdf.ln()

    # Ajout des graphiques
    for i, fig in enumerate(figures):
        img_buffer = BytesIO()
        fig.write_image(img_buffer, format="png")
        img_buffer.seek(0)
        pdf.add_page()
        pdf.set_font('Inter', 'B', 14)
        pdf.cell(0, 10, f'Graphique {i+1}', 0, 1)
        pdf.image(img_buffer, x=10, y=30, w=190)

    # Ajout de l'avertissement légal
    pdf.add_page()
    pdf.set_font('Inter', 'I', 10)
    pdf.set_text_color(128, 128, 128)  # Gris
    disclaimer_text = (
        "AVERTISSEMENT : Les performances passées ne préjugent pas des performances futures. "
        "Ce document est fourni à titre informatif uniquement et ne constitue pas un conseil en investissement. "
        "Les résultats présentés sont des estimations potentielles destinées à faciliter la compréhension "
        "du développement de votre patrimoine. Nous vous recommandons de consulter un professionnel "
        "qualifié avant de prendre toute décision d'investissement."
    )
    pdf.multi_cell(0, 5, disclaimer_text)

    return pdf.output()

def main():
    st.title("Simulation Financière")

    # Vos paramètres et calculs ici
    params = {
        "capital_initial": 10000,
        "versement_mensuel": 500,
        "rendement_annuel": 0.05,
        # Ajoutez d'autres paramètres selon vos besoins
    }

    # Votre logique de simulation ici
    # ...

    # Création des graphiques (exemple)
    def create_financial_chart(df):
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['Année'], y=df['Capital fin d\'année (NET)'], name='Capital'))
        return fig

    def create_waterfall_chart(df):
        fig = go.Figure(go.Waterfall(
            name = "Évolution du capital",
            orientation = "v",
            measure = ["relative"] * len(df),
            x = df['Année'],
            y = df['Capital fin d\'année (NET)'] - df['Capital initial (NET)'],
            connector = {"line":{"color":"rgb(63, 63, 63)"}},
        ))
        return fig

    # Supposons que vous ayez un DataFrame 'resultats_df' avec vos résultats
    resultats_df = pd.DataFrame({
        'Année': range(1, 11),
        'Capital initial (NET)': [10000] * 10,
        'Capital fin d\'année (NET)': [11000, 12100, 13310, 14641, 16105, 17716, 19487, 21436, 23579, 25937]
    })

    fig1 = create_financial_chart(resultats_df)
    fig2 = create_waterfall_chart(resultats_df)

    # Affichage des graphiques dans Streamlit
    st.plotly_chart(fig1)
    st.plotly_chart(fig2)

    if st.button("Générer le rapport PDF"):
        # Préparez les données pour le PDF
        data = [
            ["Paramètre", "Valeur"],
            ["Capital initial", f"{params['capital_initial']} €"],
            ["Versement mensuel", f"{params['versement_mensuel']} €"],
            ["Rendement annuel", f"{params['rendement_annuel']*100}%"],
            # Ajoutez d'autres paramètres ici
        ]

        # Générez le PDF
        pdf_bytes = create_pdf(data, [fig1, fig2])

        # Créez un lien de téléchargement pour le PDF
        b64 = base64.b64encode(pdf_bytes).decode()
        href = f'<a href="data:application/pdf;base64,{b64}" download="rapport_simulation.pdf">Télécharger le rapport PDF</a>'
        st.markdown(href, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
