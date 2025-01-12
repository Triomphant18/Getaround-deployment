import mlflow
import uvicorn
import json
import pandas as pd
from pydantic import BaseModel
from typing import Literal, List, Union
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse, RedirectResponse


description = """

Cette API permet d'explorer et de prédire les prix de location de véhicules en fonction de plusieurs attributs de voiture. Elle offre des points de terminaison (endpoints) pour prévisualiser les données, récupérer les valeurs uniques d'une colonne, et réaliser des prédictions de prix basées sur des caractéristiques spécifiques d'une voiture.

## Dataset Feature Descriptions

- **model_key**: Marque ou modèle de la voiture (ex : "Toyota", "Ford").
- **mileage**: Nombre de kilomètres parcourus par la voiture, ce qui peut influencer l'usure et l'entretien.
- **engine_power**: Puissance du moteur, en chevaux, reflétant les performances du véhicule.
- **fuel**: Type de carburant utilisé (ex : "diesel", "essence").
- **paint_color**: Couleur de la voiture, potentiellement influente sur le prix selon la demande.
- **car_type**: Type de voiture, tel que "sedan" ou "SUV".
- **private_parking_available**: Booléen indiquant si le stationnement privé est inclus.
- **has_gps**: Booléen indiquant si la voiture est équipée d'un GPS.
- **has_air_conditioning**: Booléen indiquant si la voiture dispose de la climatisation.
- **automatic_car**: Booléen indiquant si la voiture possède une transmission automatique.
- **has_getaround_connect**: Booléen indiquant si la voiture est équipée du système GetAround Connect.
- **has_speed_regulator**: Booléen indiquant si la voiture est équipée d'un régulateur de vitesse.
- **winter_tires**: Booléen indiquant si la voiture possède des pneus d'hiver.

---

## Endpoints

1. **`/preview`**
   - Retourne les premières lignes du dataset pour une vue d'ensemble rapide de la structure et du contenu des données.
   
2. **`/unique-values`**
   - Accepte le nom d'une colonne comme paramètre et retourne les valeurs uniques de cette colonne, permettant aux utilisateurs d'explorer les valeurs distinctes des variables catégorielles.

3. **`/predict`**
   - Accepte en entrée les caractéristiques d'une voiture et retourne un prix de location prédit basé sur le modèle d'apprentissage supervisé, permettant un tarif dynamique selon les spécifications fournies.
   
4. **`/batch-predict`**
   - Fonctionne exactement comme le predict mais prend en entrée un fichier csv

"""

tags_metadata = [{"name": "Visualisation"}, {"name": "Machine-Learning"}]

app = FastAPI(
    title="Pricing Prediction API",
    description=description,
    openapi_tags=tags_metadata,
    version="0.1",
)


class PredictionSample(BaseModel):
    model_key: str
    mileage: Union[int, float]
    engine_power: Union[int, float]
    fuel: str
    paint_color: str
    car_type: str
    private_parking_available: bool
    has_gps: bool
    has_air_conditioning: bool
    automatic_car: bool
    has_getaround_connect: bool
    has_speed_regulator: bool
    winter_tires: bool


class PredictionInput(BaseModel):
    input: List[PredictionSample]


@app.get("/", include_in_schema=False)
async def root():
    "Redirect to the documentation"
    return RedirectResponse(url="/docs")


@app.get("/preview", tags=["Visualisation"])
async def dataset_preview(rows: int = 15):
    """
    Get a preview of the dataset

    Parameters:
    rows (int): The number of rows to select. Default is 15.

    Returns:
    JSON: JSON representation of the top rows from the dataset.
    """
    df = pd.read_csv(
        "https://full-stack-assets.s3.eu-west-3.amazonaws.com/Deployment/get_around_pricing_project.csv",
        index_col=[0],
    )
    sample = df.head(rows)
    json_data = sample.to_dict(orient="records")
    return JSONResponse(content={"data": json_data, "row_count": rows})


@app.post("/unique-values", tags=["Visualisation"])
async def unique_values(col_name: str):
    """
    Returns the unique values of a given column name
    """
    df = pd.read_csv(
        "https://full-stack-assets.s3.eu-west-3.amazonaws.com/Deployment/get_around_pricing_project.csv",
        index_col=[0],
    )
    if col_name in df.columns:
        unique_columns = df[col_name].unique().tolist()
        json_data = {"unique_columns": unique_columns}
        return JSONResponse(json_data)
    else:
        return {"error": f"Column '{col_name}' not found in the dataset."}


@app.post("/predict", tags=["Machine-Learning"])
async def prediction(data: PredictionInput):
    """
    Make prediction
    """
    df = pd.DataFrame(data.input[0])
    df.set_index(0, inplace=True)
    df = df.T

    # Preprocessing
    preprocessor = "runs:/a73622d206e34c43be7660794faebaf3/preprocessor"

    # Load model
    preprocess = mlflow.sklearn.load_model(preprocessor)

    # Load model
    logged_model = "runs:/cbbd70fa6f724502a277d301659450fc/XGBoost_model"

    # Load model as a PyFuncModel.
    loaded_model = mlflow.pyfunc.load_model(logged_model)

    # Predict on a Pandas DataFrame.
    prediction = loaded_model.predict(pd.DataFrame(preprocess.transform(df)))

    return JSONResponse({"predictions": prediction.tolist()})


@app.post("/batch-predict", tags=["Machine-Learning"])
async def batch_predict(file: UploadFile = File(...)):
    """
    Make Batch predictions
    """
    data = pd.read_csv(file.file)

    # Preprocessing
    preprocessor = "runs:/a73622d206e34c43be7660794faebaf3/preprocessor"

    # Load model
    preprocess = mlflow.sklearn.load_model(preprocessor)

    # Load model
    logged_model = "runs:/cbbd70fa6f724502a277d301659450fc/XGBoost_model"

    # Load model as a PyFuncModel.
    loaded_model = mlflow.pyfunc.load_model(logged_model)

    # Predict on a Pandas DataFrame.
    predictions = loaded_model.predict(pd.DataFrame(preprocess.transform(data)))

    return JSONResponse({"predictions": predictions.tolist()})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=4000, debug=True, reload=True)
