
# GetAround API Project 🚗

## Description

Ce projet propose une solution complète pour analyser et optimiser les opérations de GetAround. Il comprend trois composants principaux :  
1. **API** : Fournit un endpoint `/predict` et `/batch-predict` pour les prédictions.  
2. **Tableau de bord interactif** : Visualisation des données avec Streamlit.  
3. **Serveur MLflow** : Suivi des expérimentations de Machine Learning.

---

## Structure du projet

### 1. **API (FastAPI)**
- Fournit un endpoint pour les prédictions via `/predict`.
- **Commande Docker pour lancer l'API** :  
  ```bash
  docker run -it    
  -p 4000:4000    
  -v "$(pwd):/home/app"    
  -e PORT=4000    
  -e MLFLOW_TRACKING_URI=$APP_URI    
  -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID    
  -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY    
  -e BACKEND_STORE_URI=$BACKEND_STORE_URI    
  -e ARTIFACT_ROOT=$ARTIFACT_ROOT    
  getaroundapi
  ```

### 2. **Tableau de bord (Streamlit)**
- Visualisation des analyses des retards et des impacts des seuils sur les revenus.
- **Commande Docker pour lancer Streamlit** :  
  ```bash
  docker run -it    
  -p 8501:8501    
  -v "$(pwd):/home/app"    
  -e PORT=8501    
  getaround-streamlit
  ```

### 3. **Serveur MLflow**
- Gère le suivi des modèles et des artefacts.
- **Commande Docker pour lancer MLflow** :  
  ```bash
  docker run -it    
  -p 8000:8000    
  -v "$(pwd):/home/app"    
  -e PORT=8000    
  -e APP_URI=$APP_URI    
  -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID    
  -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY    -e BACKEND_STORE_URI=$BACKEND_STORE_URI    -e ARTIFACT_ROOT=$ARTIFACT_ROOT    mlflow-get-around
  ```

---

## Fichiers importants

- **Dockerfile API** : Configuration pour lancer l'API.
- **Dockerfile Streamlit** : Configuration pour le tableau de bord interactif.
- **Dockerfile MLflow** : Configuration pour le serveur MLflow.
- **requirements.txt** : Contient les dépendances nécessaires pour tous les composants.

---

## Technologies utilisées

- **Python** : Pandas, Scikit-learn, XGBoost
- **FastAPI** : Pour l'API
- **Streamlit** : Pour la visualisation des données
- **MLflow** : Pour le suivi des expérimentations
- **Docker** : Pour la conteneurisation

---

## Auteur

Projet développé dans le cadre d’une étude de cas GetAround.