# Renault Group — Dashboard de performance industrielle

Application Streamlit en français pour analyser les performances d'une chaîne de production industrielle.

## Contenu du projet

```text
renault_group_dashboard/
├── app.py
├── requirements.txt
├── README.md
└── data/
    └── (déposez ici votre fichier CSV — non inclus dans cette archive)
```

**Le fichier de données CSV n'est volontairement pas inclus** dans le ZIP. L'application permet de charger le CSV depuis la barre latérale ou de lire `data/zahir_hajar.csv` s'il est ajouté manuellement.

## Fonctionnalités

- Connexion avec identifiant et mot de passe.
- Import et nettoyage des données avec pandas.
- Filtres par période, équipe, machine, produit et poste.
- KPI : TRS, volume produit, pièces bonnes, taux de rebut, temps d'arrêt et énergie.
- Graphiques de tendance du TRS, comparaison des machines, répartition des arrêts, Pareto, qualité et énergie.
- Comparaison avant/après TPM-SMED à partir du 60e jour.
- Diagnostic du goulot d'étranglement et recommandations.
- Tableau des données filtrées et export CSV.

## Installation

Python 3.10 ou plus récent est recommandé.

### 1. Créer un environnement virtuel

Windows :

```bash
python -m venv .venv
.venv\Scripts\activate
```

macOS / Linux :

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 3. Ajouter les données

Deux possibilités :

- Lancer l'application et importer le fichier CSV depuis le panneau latéral.
- Ou placer le fichier sous `data/zahir_hajar.csv`.

Le CSV doit contenir au minimum les colonnes suivantes :

`date_heure, equipe, machine_id, poste, produit, temps_panne_min, temps_reglage_min, nb_micro_arrets, temps_fonctionnement_min, cadence_theorique_h, pieces_produites, pieces_bonnes, pieces_rebutees`

Les colonnes complémentaires comme `duree_micro_arrets_min`, `disponibilite_pct`, `performance_pct`, `qualite_pct`, `TRS_pct` et `energie_kwh` sont utilisées lorsqu'elles existent.

### 4. Démarrer

```bash
streamlit run app.py
```

L'application s'ouvre dans le navigateur, généralement à l'adresse `http://localhost:8501`.

## Connexion de démonstration

- Identifiant : `hajar`
- Mot de passe : `ha2707`

Pour un déploiement, ne conservez pas les identifiants de démonstration. Définissez plutôt les variables d'environnement `APP_USERNAME` et `APP_PASSWORD`, ou configurez les secrets Streamlit.

Exemple de fichier `.streamlit/secrets.toml` (ne pas publier ce fichier sur GitHub) :

```toml
APP_USERNAME = "votre_identifiant"
APP_PASSWORD = "un_mot_de_passe_long_et_unique"
```

## Méthode de calcul et limites

- Le TRS est affiché à partir de la colonne `TRS_pct` lorsqu'elle est valide. À défaut, il est recalculé à partir de disponibilité × performance × qualité.
- La disponibilité, la performance et la qualité sont moyennées sur les lignes filtrées.
- Les temps d'arrêt agrègent les pannes, les réglages et les durées de micro-arrêts lorsque cette dernière colonne est disponible.
- Le jour 60 est calculé à partir de la première date présente dans le fichier.
- Les valeurs calculées dépendent de la qualité et de la définition métier des colonnes sources.

**Limite logistique :** le CSV fourni décrit la production industrielle, mais ne contient pas les informations de livraison (région, ville, client, expédition, date de livraison). Le dashboard ne prétend donc pas analyser la distribution nationale au Maroc. Ces champs devront être ajoutés pour construire une carte et des KPI de livraison.

## Technologies

Python · Streamlit · pandas · NumPy · Matplotlib · Seaborn
