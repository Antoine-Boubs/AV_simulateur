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


###
# Titre de l'application
st.title("📊 Simulation de votre placement")

# Section des paramètres d'entrée avec des sliders et des inputs
st.header("🔧 Paramètres de simulation")

col1, col2, col3 = st.columns(3)

with col1:
    capital_initial = st.number_input("💵 Capital initial (CI)", min_value=0.0, value=2000.0)
    frais_entree_ci = st.slider("💸 Frais d'entrée CI (%)", min_value=0.0, max_value=10.0, value=4.5) / 100

with col2:
    versement_mensuel = st.number_input("📅 Versement mensuel (VP)", min_value=0.0, value=400.0)
    frais_entree_vp = st.slider("💸 Frais d'entrée VP (%)", min_value=0.0, max_value=10.0, value=4.5) / 100

with col3:
    rendement_annuel = st.slider("📈 Rendement annuel (%)", min_value=0.0, max_value=20.0, value=5.0) / 100
    frais_gestion = st.slider("🛠️ Frais de gestion (%)", min_value=0.0, max_value=5.0, value=0.8) / 100

# Ajout d'un slider pour la durée de l'investissement
duree_investissement = st.slider("⏳ Durée de l'investissement (années)", min_value=1, max_value=100, value=20)

# Gestion de la liste des versements libres avec st.session_state
if "versements_libres" not in st.session_state:
    st.session_state.versements_libres = []  # Initialiser une liste vide

# Fonction pour ajouter un versement libre
def ajouter_versement_libre():
    st.session_state.versements_libres.append({
        "annee": 5,  # Valeur par défaut
        "montant": 1000.0  # Valeur par défaut
    })

# Fonction pour supprimer un versement libre
def supprimer_versement_libre(index):
    st.session_state.versements_libres.pop(index)

# Bouton pour ajouter un versement libre
st.button("➕ Ajouter un versement libre", on_click=ajouter_versement_libre)

# Affichage de tous les versements libres avec option de suppression
for i, versement in enumerate(st.session_state.versements_libres):
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        versement["annee"] = st.slider(f"Année du versement libre {i+1}", min_value=1, max_value=duree_investissement, value=versement["annee"])
    with col2:
        versement["montant"] = st.number_input(f"Montant du versement libre {i+1} (€)", min_value=0.0, value=versement["montant"])
    with col3:
        st.button("❌ Supprimer", key=f"supprimer_{i}", on_click=supprimer_versement_libre, args=(i,))

# Fonction pour calculer le rendement sur les versements mensuels avec prorata
def calcul_rendement_versements_mensuels(vp, rendement_annuel):
    rendement_versements = 0
    for mois in range(12):
        prorata = (12 - mois) / 12  # Le mois de janvier est investi 12 mois, février 11 mois, etc.
        rendement_versements += (vp * prorata) * rendement_annuel
    return rendement_versements

# Calcul des valeurs dynamiques pour le tableau
def calculer_epargne_annuelle(ci_net, ci_brut, vp_net, vp_brut, rendement, frais_gestion, duree, objectifs):
    data = []
    
    # Initialisation des variables
    capi_debut_annee = ci_net  # Capital de début d'année AVEC frais (net)
    epargne_investie = ci_brut + (vp_brut * 12)  # Épargne investie calculée sur capital initial brut et versements bruts

    # Création d'une colonne 'Rachat' initialement à 0 pour toutes les années
    rachats = [0.0] * duree
    for objectif in objectifs:
        annee_debut = objectif["annee"]
        duree_retrait = int(objectif["duree_retrait"])  # Conversion explicite en entier

        montant_annuel_retrait = objectif["montant_annuel"]
        
        # Appliquer les montants de rachat pour chaque année concernée
        for annee in range(annee_debut, annee_debut + duree_retrait):
            if annee <= duree:  # S'assurer de ne pas dépasser la durée totale
                rachats[annee - 1] += montant_annuel_retrait  # Année - 1 car index commence à 0

    for annee in range(1, duree+1):

        ### Étape 1 : Appliquer le rachat d'abord
        rachat_annee = rachats[annee - 1]  # Récupérer le rachat pour l'année en cours
        capi_debut_annee -= rachat_annee  # Soustraire le rachat du capital de début d'année

        ### Étape 2 : Calcul du capital fin d'année avec tous les frais (net)
        rendement_annuel_total = capi_debut_annee * rendement
        rendement_versements_net = calcul_rendement_versements_mensuels(vp_net, rendement)
        
        # Frais de gestion appliqués sur le capital net et les versements nets
        frais_gestion_total_avec_frais = (capi_debut_annee * frais_gestion)  # Frais de gestion sur le capital net
        frais_gestion_sur_versements_nets = 0
        
        for mois in range(12):
            prorata_mois = (12 - mois) / 12
            frais_gestion_sur_versements_nets += (vp_net * prorata_mois) * frais_gestion  # Frais de gestion sur les versements nets

        frais_gestion_total_avec_frais += frais_gestion_sur_versements_nets

        # Appliquer les versements libres dans l'année
        for versement in st.session_state.versements_libres:
            if versement["annee"] == annee:
                capi_debut_annee += versement["montant"]
                epargne_investie += versement["montant"]  # Ajouter le versement libre à l'épargne investie
        
        # Calcul du capital de fin d'année avec frais (frais d'entrée et gestion)
        capital_fin_annee = capi_debut_annee + (vp_net * 12) + rendement_annuel_total + rendement_versements_net - frais_gestion_total_avec_frais

        # Ajout des résultats dans la liste des données, avec la colonne 'Rachat' ajoutée
        data.append([
            annee, 
            f"{capi_debut_annee:.2f} €",  # Capital de début d'année AVEC frais (net)
            f"{vp_net * 12:.2f} €",  # Versement net annuel
            f"{rendement_annuel_total + rendement_versements_net:.2f} €",  # Rendement AVEC frais
            f"{frais_gestion_total_avec_frais:.2f} €",  # Frais de gestion totaux (version AVEC frais)
            f"{capital_fin_annee:.2f} €",  # Capital de fin d'année AVEC frais
            f"{rachat_annee:.2f} €",  # Montant de rachat pour l'année
            f"{epargne_investie:.2f} €",  # Épargne investie cumulée (brut)
        ])
        
        # Mise à jour des capitaux pour l'année suivante
        capi_debut_annee = capital_fin_annee  # Capital avec frais pour l'année suivante
        epargne_investie += vp_brut * 12  # Ajouter les versements bruts à l'épargne investie chaque année

    # Retour du DataFrame après la boucle, une fois qu'on a toutes les années
    return pd.DataFrame(data, columns=[
        "ANNÉE", "Capital initial (NET)", "VP NET", "RENDEMENT", "FRAIS DE GESTION", 
        "CAPI FIN D’ANNÉE (NET)", "RACHAT", "ÉPARGNE INVESTIE"
    ])

# Définition des objectifs financiers
st.header("🎯 Objectifs financiers")

# Ajouter des objectifs spécifiques
objectifs = []  # Initialisation de la liste des objectifs
nombre_objectifs = st.number_input("Combien d'objectifs souhaitez-vous définir ?", min_value=1, max_value=10, value=2)

for i in range(1, nombre_objectifs + 1):
    st.subheader(f"Objectif {i}")
    objectif_nom = st.text_input(f"Nom de l'objectif {i}", f"Objectif {i}")
    objectif_annee = st.slider(f"Année de réalisation de l'objectif {i}", min_value=1, max_value=duree_investissement, value=i * 5)
    montant_annuel_retrait = st.number_input(f"Montant annuel à retirer pour {objectif_nom} (€)", min_value=0, value=5000)
    retrait_indefini = st.checkbox(f"Retrait indéfini pour {objectif_nom} ?", key=f"indefini_{i}")
    
    if retrait_indefini:
        # Si la case retrait indéfini est cochée, demander une durée approximative
        st.info("Les mathématiques n'aiment pas l'incertitude, rentrez une durée approximative de votre rachat annuel.")
        duree_retrait = st.number_input(f"Durée approximative de retrait pour {objectif_nom} (années)", min_value=1, value=10, help = 'L\' espérance de vie est de 85 ans environ, faites vos jeux !')
    else:
        # Si la case n'est pas cochée, demander une durée normale de retrait
        duree_retrait = st.number_input(f"Durée de retrait pour {objectif_nom} (années)", min_value=1, max_value=duree_investissement, value=4)
    
    # Ajout des objectifs dans la liste
    objectifs.append({
        "nom": objectif_nom,
        "annee": objectif_annee,
        "montant_annuel": montant_annuel_retrait,
        "duree_retrait": duree_retrait,
    })

# Calcul des valeurs initiales
ci_net = capital_initial * (1 - frais_entree_ci)
ci_brut = capital_initial  # Capital brut avant frais d'entrée
vp_net = versement_mensuel * (1 - frais_entree_vp)
vp_brut = versement_mensuel  # Versements bruts avant frais

# Calcul du tableau avec les paramètres actuels et intégration des rachats
resultats_df = calculer_epargne_annuelle(ci_net, ci_brut, vp_net, vp_brut, rendement_annuel, frais_gestion, duree_investissement, objectifs)

# Affichage des résultats avec les rachats
st.header("📊 Résultats de la simulation avec rachats")
st.dataframe(resultats_df)


## Proposer une date d'arret de VP ? 



# Fonction pour calculer les résultats (ici vous remplissez avec vos calculs réels)
def calculer_epargne_annuelle(ci_net, ci_brut, vp_net, vp_brut, rendement, frais_gestion, duree, objectifs):
    # Cette fonction doit retourner votre DataFrame `resultats_df`
    # Exécution des calculs ici...
    # Voici un exemple simulé pour l'instant :
    years = list(range(1, duree + 1))
    valorisation = [ci_net * (1 + rendement)**year for year in years]
    epargne_investie = [vp_brut * 12 * year for year in years]
    return pd.DataFrame({
        "Année": years,
        "CAPI FIN D’ANNÉE (NET)": valorisation,
        "Épargne investie": epargne_investie
    })

# Calcul des valeurs initiales
ci_net = capital_initial * (1 - frais_entree_ci)
ci_brut = capital_initial  # Capital brut avant frais d'entrée
vp_net = versement_mensuel * (1 - frais_entree_vp)
vp_brut = versement_mensuel  # Versements bruts avant frais

# Exemple de DataFrame final après calcul
resultats_df = calculer_epargne_annuelle(ci_net, ci_brut, vp_net, vp_brut, rendement_annuel, frais_gestion, duree_investissement, [])

# Utilisation des données du DataFrame pour tracer le graphique
fig = go.Figure()

# Tracé de la valorisation du contrat
fig.add_trace(go.Scatter(x=resultats_df["Année"], y=resultats_df["CAPI FIN D’ANNÉE (NET)"],
                         mode='lines+markers', name='Valorisation du contrat', line=dict(color='#A52A2A')))

# Tracé de l'épargne investie
fig.add_trace(go.Scatter(x=resultats_df["Année"], y=resultats_df["Épargne investie"],
                         mode='lines+markers', name="Épargne investie", line=dict(color='#1E90FF')))

# Configuration du graphique
fig.update_layout(
    title="Patrimoine constitué",
    xaxis_title="Années",
    yaxis_title="Montant (€)",
    hovermode="x unified",
    legend_title="Légende",
    template="plotly_white"
)

# Affichage du graphique avec Streamlit
st.plotly_chart(fig)




import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Fonction pour calculer les résultats sur 100 ans
def calculer_epargne_annuelle(ci_net, ci_brut, vp_net, vp_brut, rendement, frais_gestion, duree):
    # Simuler les données pour 100 ans
    years = list(range(1, 101))
    valorisation = []
    effort_epargne = []
    
    capi = ci_net
    cumul_versements = 0
    
    for year in years:
        # Calcul du rendement annuel
        capi += capi * rendement
        cumul_versements += vp_brut * 12
        capi += vp_brut * 12  # Ajouter les versements chaque année
        
        valorisation.append(capi)
        effort_epargne.append(cumul_versements)
    
    return pd.DataFrame({
        "Année": years,
        "CAPI FIN D’ANNÉE (NET)": valorisation,
        "Effort d'épargne cumulé": effort_epargne
    })

# Configuration initiale
st.title("📊 Simulation de votre placement avec affichage dynamique")

# Variables de base (vous pouvez les fixer ou les récupérer via d'autres inputs)
capital_initial = 2000.0
versement_mensuel = 400.0
rendement_annuel = 5.0 / 100
frais_gestion = 0.8 / 100

# Calcul des valeurs initiales
ci_net = capital_initial
ci_brut = capital_initial
vp_net = versement_mensuel
vp_brut = versement_mensuel

# Calcul du DataFrame sur 100 ans
resultats_df = calculer_epargne_annuelle(ci_net, ci_brut, vp_net, vp_brut, rendement_annuel, frais_gestion, 100)

# Slider pour sélectionner la durée
duree_selectionnee = st.slider("Sélectionnez la durée (années)", min_value=1, max_value=100, value=20)

# Extraire les valeurs correspondantes à la durée sélectionnée
capital_acquis = resultats_df.loc[duree_selectionnee-1, "CAPI FIN D’ANNÉE (NET)"]
effort_epargne_cumule = resultats_df.loc[duree_selectionnee-1, "Effort d'épargne cumulé"]

# Calcul de la rentabilité
rentabilite = (capital_acquis - effort_epargne_cumule) / effort_epargne_cumule * 100 if effort_epargne_cumule != 0 else 0

# Affichage des informations sous forme de cartes
st.markdown("## En chiffres")

# Diviser l'écran en plusieurs colonnes pour afficher les cartes
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(label="Capital acquis", value=f"{capital_acquis:,.2f} €")

with col2:
    st.metric(label="Effort d'épargne cumulé", value=f"{effort_epargne_cumule:,.2f} €")

with col3:
    st.metric(label="Rentabilité", value=f"{rentabilite:.2f} %")

# Création du graphique interactif avec Plotly
fig = go.Figure()

# Tracé de la valorisation du contrat
fig.add_trace(go.Scatter(x=resultats_df["Année"], y=resultats_df["CAPI FIN D’ANNÉE (NET)"],
                         mode='lines+markers', name='Valorisation du contrat', line=dict(color='#A52A2A')))

# Tracé de l'épargne investie
fig.add_trace(go.Scatter(x=resultats_df["Année"], y=resultats_df["Effort d'épargne cumulé"],
                         mode='lines+markers', name="Effort d'épargne cumulé", line=dict(color='#1E90FF')))

# Configuration du graphique
fig.update_layout(
    title="Patrimoine constitué",
    xaxis_title="Années",
    yaxis_title="Montant (€)",
    hovermode="x unified",
    legend_title="Légende",
    template="plotly_white"
)

# Affichage du graphique avec Streamlit
st.plotly_chart(fig)
