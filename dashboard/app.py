import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import requests
import json


# Charger le dataset avec mise en cache
@st.cache_data
def load_data():
    dataset_url = "https://full-stack-assets.s3.eu-west-3.amazonaws.com/Deployment/get_around_delay_analysis.xlsx"
    return pd.read_excel(dataset_url)


# Charger le deuxième dataset pour l'optimisation des prix
@st.cache_data
def load_pricing_data():
    pricing_url = "https://full-stack-assets.s3.eu-west-3.amazonaws.com/Deployment/get_around_pricing_project.csv"
    return pd.read_csv(pricing_url, index_col=[0])


# Charger les données
dataset = load_data()
dataset2 = load_pricing_data()

# Nettoyage des données
dataset_clean = dataset[
    (dataset["state"] == "canceled")
    & (dataset["delay_at_checkout_in_minutes"].isnull())
    | (
        (dataset["state"] == "ended")
        & (dataset["delay_at_checkout_in_minutes"].notnull())
    )
].reset_index(drop=True)

# Traiter les données
dataset_clean_canceled = dataset_clean[dataset_clean["state"] == "canceled"]
dataset_clean = dataset_clean[
    (dataset_clean["delay_at_checkout_in_minutes"] <= 60 * 24 * 3)
    & (dataset_clean["delay_at_checkout_in_minutes"] >= -60 * 24 * 3)
]
dataset_clean = pd.concat([dataset_clean, dataset_clean_canceled])

### Partie II
st.write("## Partie I: Data Analysis")

# Afficher les premières lignes du dataset
st.write("### Aperçu du dataset nettoyé")
st.dataframe(dataset_clean.head())

# Taux d'annulation
st.write("### Taux d'annulation des locations")

# Calculer la répartition des états
state_counts = dataset_clean["state"].value_counts(normalize=True).reset_index()
state_counts.columns = ["State", "Proportion"]

# Graphique en secteur (pie chart) avec Plotly
fig = px.pie(
    state_counts,
    values="Proportion",
    names="State",
    title="Répartition des locations par état",
    color="State",
    hole=0.3,
)
st.plotly_chart(fig)

# Calculer le taux d'annulation
cancelation_rate = state_counts["Proportion"].iloc[1] * 100
st.write(f"On peut voir qu'il y a environ {cancelation_rate.round(2)}% d'annulations.")

# Vérification de la proportion d'annulations dues à des retards de la location précédente
st.write("### Proportion d'annulations dues à un retard de la location précédente")

cancel_previous = dataset_clean[
    (dataset_clean["state"] == "canceled")
    & (dataset_clean["time_delta_with_previous_rental_in_minutes"].notna())
]

long_late = len(cancel_previous["previous_ended_rental_id"]) - len(
    cancel_previous["previous_ended_rental_id"].unique()
)

canceled_previous_dt = dataset_clean[
    (
        dataset_clean["rental_id"].isin(
            cancel_previous["previous_ended_rental_id"].unique()
        )
    )
    & (dataset_clean["delay_at_checkout_in_minutes"].notna())
][["checkin_type", "delay_at_checkout_in_minutes"]]

cancelation_late = (
    (
        len(
            canceled_previous_dt[
                canceled_previous_dt["delay_at_checkout_in_minutes"] > 0
            ]
        )
        + long_late
    )
    * 100
    // len(canceled_previous_dt)
)

st.write(
    f"On peut voir que *{cancelation_late}% des annulations sont dues à des retards* de la location précédente."
)


# Calcul de l'impact des seuils sur les retards
def calculate_impact_cases(df, thresholds=range(10, 240, 20)):
    mobile_cases, connect_cases = [], []
    delay_df = df[df["delay_at_checkout_in_minutes"] > 0]
    for i in thresholds:
        counts = (
            delay_df[delay_df["delay_at_checkout_in_minutes"] <= i]["checkin_type"]
            .value_counts()
            .reindex(["mobile", "connect"], fill_value=0)
        )
        mobile_cases.append(counts.get("mobile", 0))
        connect_cases.append(counts.get("connect", 0))
    impact_df = pd.DataFrame(
        {
            "threshold": thresholds,
            "mobile_case": mobile_cases,
            "connect_case": connect_cases,
        }
    )
    return impact_df


# Afficher les courbes de seuil d'impact
impact_df = calculate_impact_cases(dataset_clean)
st.write("### Impact des seuils de retard sur les cas de retards")
st.line_chart(impact_df.set_index("threshold")[["mobile_case", "connect_case"]])

# Vérification de la fréquence des retards des conducteurs pour le prochain enregistrement
st.write("### Fréquence des retards des conducteurs pour le prochain enregistrement")

nextcheckin_late_df = dataset_clean[dataset_clean["state"] == "ended"][
    ["delay_at_checkout_in_minutes"]
]
nextcheckin_late_pro = (
    ((nextcheckin_late_df > 0).sum()).iloc[0] * 100 // len(nextcheckin_late_df)
)
nextcheckin_late_avg = (
    nextcheckin_late_df[nextcheckin_late_df["delay_at_checkout_in_minutes"] > 0]
    .mean()
    .values[0]
    .round(2)
)

st.write(
    f"Les conducteurs sont en retard *{nextcheckin_late_pro}% du temps*. Cela peut entraîner un *temps d'attente moyen de {nextcheckin_late_avg} minutes pour le prochain conducteur*."
)


# Calcule l'impact pour les cas résolus
def calculate_resolved_cases(df):
    resolve_df = df[df["delay_at_checkout_in_minutes"] > 0]
    resolve_cases_mobile, resolve_cases_connect = [], []
    for threshold in range(10, 240, 20):
        counts = (
            resolve_df[resolve_df["delay_at_checkout_in_minutes"] <= threshold][
                "checkin_type"
            ]
            .value_counts()
            .reindex(["mobile", "connect"], fill_value=0)
        )
        resolve_cases_mobile.append(counts.get("mobile", 0))
        resolve_cases_connect.append(counts.get("connect", 0))
    return pd.DataFrame(
        {
            "threshold": range(10, 240, 20),
            "resolve_mobile": resolve_cases_mobile,
            "resolve_connect": resolve_cases_connect,
        }
    )


resolve_df = calculate_resolved_cases(canceled_previous_dt)
st.write("## Cas résolus en fonction du seuil de retard")
st.line_chart(resolve_df.set_index("threshold")[["resolve_mobile", "resolve_connect"]])

distinct_car = len(dataset_clean["car_id"].unique())
st.write(f"Nous avons *{distinct_car} distincts voitures* dans notre jeu de données")

# Ajouter un contrôle pour le nombre de voitures à afficher
top_n = st.slider(
    "Nombre de voitures les plus impactées par les retards",
    min_value=15,
    max_value=50,
    step=5,
)


# Fonction pour obtenir les voitures les plus impactées par les retards
def get_top_cars_with_late_checkouts(df, top_n=30):
    car_usage_count = df["car_id"].value_counts()
    frequently_used_cars = car_usage_count[car_usage_count > 1]
    top_used_cars_df = df[df["car_id"].isin(frequently_used_cars.index[:top_n])][
        ["car_id", "checkin_type", "delay_at_checkout_in_minutes"]
    ]
    top_used_cars_df["is_late"] = top_used_cars_df[
        "delay_at_checkout_in_minutes"
    ].apply(lambda x: 1 if x > 0 else 0)
    top_used_cars_df["count"] = 1
    late_mean_per_car = (
        top_used_cars_df[top_used_cars_df["is_late"] == 1]
        .groupby("car_id")["delay_at_checkout_in_minutes"]
        .mean()
        .rename("mean_delay")
    )
    late_rate_per_car = top_used_cars_df.groupby("car_id")[["is_late", "count"]].sum()
    late_rate_per_car["late_rate"] = (
        late_rate_per_car["is_late"] * 100 / late_rate_per_car["count"]
    )
    result = pd.concat([late_mean_per_car, late_rate_per_car], axis=1)
    return result.sort_values(by="late_rate", ascending=False)


# Obtenir les voitures les plus impactées
top_cars_df = get_top_cars_with_late_checkouts(dataset_clean, top_n)

# Afficher les résultats sous forme de tableau
st.write(f"### Top {top_n} voitures les plus impactées par les retards")
st.dataframe(top_cars_df)


st.write(f"### Taux de retard par les {top_n} véhicules les plus utilisés")

# Graphique des voitures les plus impactées
st.bar_chart(top_cars_df["late_rate"], use_container_width=True)

# Calculer le prix moyen de location
average_rental_price = dataset2["rental_price_per_day"].mean()
st.write(f"Le prix moyen de location est de **{average_rental_price:.2f}**.")


# Calculer le nombre d'annulations
cancel_len = len(dataset_clean[dataset_clean["state"] == "canceled"])

# Estimer l'impact financier des annulations dues aux retards
estimated_revenue_loss = (cancelation_late / 100) * cancel_len * average_rental_price
st.write(
    f"D'après l'analyse précédente, nous savons que 60 % des annulations sont dues à des retards. En résolvant le problème des retards, nous pourrions augmenter les bénéfices de plus de {estimated_revenue_loss.round(2)} et améliorer la fiabilité."
)
### Partie II
st.write("## Partie II: Try the API")
# En-tête de l'application

st.write("#### Sélectionnez les valeurs pour chaque attribut de la voiture :")

# Créer le formulaire pour saisir les données de chaque colonne
with st.form(key="formulaire_données"):

    # Variables catégorielles avec sélection des valeurs uniques
    model_key = st.selectbox(
        "Modèle de voiture (model_key)", dataset2["model_key"].unique()
    )
    fuel = st.selectbox("Type de carburant (fuel)", dataset2["fuel"].unique())
    paint_color = st.selectbox(
        "Couleur de peinture (paint_color)", dataset2["paint_color"].unique()
    )
    car_type = st.selectbox("Type de voiture (car_type)", dataset2["car_type"].unique())

    # Variables booléennes avec checkbox pour True/False
    private_parking_available = st.checkbox("Parking privé disponible", value=False)
    has_gps = st.checkbox("Équipé d'un GPS", value=False)
    has_air_conditioning = st.checkbox("Climatisation disponible", value=False)
    automatic_car = st.checkbox("Transmission automatique", value=False)
    has_getaround_connect = st.checkbox("Équipé de Getaround Connect", value=False)
    has_speed_regulator = st.checkbox("Équipé d'un régulateur de vitesse", value=False)
    winter_tires = st.checkbox("Pneus d'hiver disponibles", value=False)

    # Variables numériques (input de type nombre)
    mileage = st.number_input(
        "Kilométrage (mileage)", min_value=0, max_value=300000, value=30000, step=500
    )
    engine_power = st.number_input(
        "Puissance du moteur (engine_power)",
        min_value=50,
        max_value=500,
        value=140,
        step=10,
    )

    # Bouton pour soumettre le formulaire
    submit_button = st.form_submit_button(label="Générer les données")

# Afficher le DataFrame avec les données sélectionnées après soumission
if submit_button:
    # Formater les données selon l'entrée du l'API
    user_data = [
        {
            "model_key": model_key,
            "mileage": mileage,
            "engine_power": engine_power,
            "fuel": fuel,
            "paint_color": paint_color,
            "car_type": car_type,
            "private_parking_available": private_parking_available,
            "has_gps": has_gps,
            "has_air_conditioning": has_air_conditioning,
            "automatic_car": automatic_car,
            "has_getaround_connect": has_getaround_connect,
            "has_speed_regulator": has_speed_regulator,
            "winter_tires": winter_tires,
        }
    ]
    user_data = {"input": user_data}

    st.write("#### Prédiction")
    r = requests.post(
        "https://apigetaround-62925c81cfd8.herokuapp.com/predict",
        data=json.dumps(user_data),
    )
    if r.status_code == 200:
        r = r.json()
        st.write(f"The predicted rental price is:  **{round(r['predictions'][0], 2)}**")