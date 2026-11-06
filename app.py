import os
import hashlib
from pathlib import Path

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# -------------------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------------------
st.set_page_config(
    page_title="Renault Group | Performance industrielle",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

NAVY = "#172554"
BLUE = "#2563EB"
CYAN = "#06B6D4"
GREEN = "#16A34A"
ORANGE = "#F59E0B"
RED = "#DC2626"
BG = "#F4F7FB"

sns.set_theme(style="whitegrid", font="DejaVu Sans")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background: #F4F7FB; }
    [data-testid="stSidebar"] { background: #101D3A; }
    [data-testid="stSidebar"] * { color: #F8FAFC !important; }
    .hero {
        background: linear-gradient(115deg, #101D3A 0%, #1D4ED8 70%, #0891B2 100%);
        padding: 26px 30px; border-radius: 18px; color: white;
        margin-bottom: 20px; box-shadow: 0 8px 24px rgba(23,37,84,.14);
    }
    .hero h1 { color: white; font-size: 29px; margin: 0; font-weight: 800; }
    .hero p { color: #DBEAFE; margin: 7px 0 0 0; font-size: 14px; }
    .kpi {
        background: white; border: 1px solid #E5EAF2; border-radius: 14px;
        padding: 17px 18px; min-height: 112px;
        box-shadow: 0 3px 12px rgba(15,23,42,.04);
    }
    .kpi-label { color: #64748B; font-size: 12px; font-weight: 600; }
    .kpi-value { color: #172554; font-size: 27px; font-weight: 800; margin-top: 7px; }
    .kpi-sub { color: #94A3B8; font-size: 11px; margin-top: 3px; }
    .section-title { color: #172554; font-size: 18px; font-weight: 750; margin: 8px 0 12px; }
    .insight {
        background: white; border-left: 5px solid #2563EB; padding: 16px 18px;
        border-radius: 10px; color: #334155; margin: 8px 0;
    }
    div[data-testid="stMetric"] { background: white; padding: 13px; border-radius: 12px; border: 1px solid #E5EAF2; }
    .stButton>button { border-radius: 9px; font-weight: 600; }
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# -------------------------------------------------------------------
# AUTHENTICATION
# Demo credentials are defaults for local coursework use.
# In deployment, define APP_USERNAME and APP_PASSWORD as environment
# variables or use Streamlit secrets.
# -------------------------------------------------------------------
def get_credentials():
    try:
        username = st.secrets.get("APP_USERNAME", os.getenv("APP_USERNAME", "hajar"))
        password = st.secrets.get("APP_PASSWORD", os.getenv("APP_PASSWORD", "ha2707"))
    except Exception:
        username = os.getenv("APP_USERNAME", "hajar")
        password = os.getenv("APP_PASSWORD", "ha2707")
    return str(username), str(password)


def login():
    expected_user, expected_password = get_credentials()
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    st.markdown("""
    <div style="max-width:720px;margin:7vh auto 18px;text-align:center">
      <div style="font-size:44px">🏭</div>
      <div style="font-size:28px;font-weight:800;color:#172554">RENAULT GROUP</div>
      <div style="color:#64748B">Portail de pilotage industriel · Maroc</div>
    </div>
    """, unsafe_allow_html=True)
    left, center, right = st.columns([1, 1.1, 1])
    with center:
        with st.container(border=True):
            st.subheader("Connexion")
            st.caption("Veuillez vous identifier pour accéder au tableau de bord.")
            with st.form("login_form"):
                username = st.text_input("Identifiant", placeholder="Votre identifiant")
                password = st.text_input("Mot de passe", type="password", placeholder="Votre mot de passe")
                submitted = st.form_submit_button("Se connecter", use_container_width=True, type="primary")
            if submitted:
                if username == expected_user and password == expected_password:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Identifiant ou mot de passe incorrect.")
            st.caption("Accès de démonstration configuré pour le projet local.")
    st.stop()


if not st.session_state.get("authenticated", False):
    login()


# -------------------------------------------------------------------
# DATA LOADING AND CLEANING
# -------------------------------------------------------------------
REQUIRED = [
    "date_heure", "equipe", "machine_id", "poste", "produit",
    "temps_panne_min", "temps_reglage_min", "nb_micro_arrets",
    "temps_fonctionnement_min", "cadence_theorique_h",
    "pieces_produites", "pieces_bonnes", "pieces_rebutees",
]

NUMERIC_COLS = [
    "temps_ouverture_min", "arret_planifie_min", "temps_panne_min",
    "temps_reglage_min", "nb_micro_arrets", "duree_micro_arrets_min",
    "temps_fonctionnement_min", "cadence_theorique_h", "pieces_produites",
    "pieces_bonnes", "pieces_rebutees", "disponibilite_pct",
    "performance_pct", "qualite_pct", "TRS_pct",
    "temperature_machine_C", "vibration_mm_s", "energie_kwh",
]


@st.cache_data(show_spinner=False)
def load_csv(file):
    data = pd.read_csv(file)
    return data


def clean_data(raw):
    df = raw.copy()
    df.columns = [str(c).strip() for c in df.columns]

    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError("Colonnes obligatoires absentes : " + ", ".join(missing))

    df["date_heure"] = pd.to_datetime(df["date_heure"], errors="coerce")
    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["date_heure", "machine_id"])
    df = df.drop_duplicates()
    for col in ["equipe", "machine_id", "poste", "produit"]:
        df[col] = df[col].astype("string").fillna("Non renseigné").str.strip()

    # Missing numeric values are kept neutral for aggregation and flagged in data quality.
    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = df[col].fillna(0)

    # Calcul des indicateurs à partir des données disponibles.
    if "disponibilite_pct" not in df.columns:
        planned = (df.get("temps_ouverture_min", 0) - df.get("arret_planifie_min", 0)).clip(lower=0)
        loss = df["temps_panne_min"] + df["temps_reglage_min"] + df.get("duree_micro_arrets_min", 0)
        df["disponibilite_pct"] = np.where(planned > 0, (planned-loss).clip(lower=0) / planned * 100, 0)
    if "performance_pct" not in df.columns:
        theoretical = df["cadence_theorique_h"] * df["temps_fonctionnement_min"] / 60
        df["performance_pct"] = np.where(theoretical > 0, df["pieces_produites"] / theoretical * 100, 0)
    if "qualite_pct" not in df.columns:
        df["qualite_pct"] = np.where(df["pieces_produites"] > 0, df["pieces_bonnes"] / df["pieces_produites"] * 100, 0)

    df["TRS_calcule_pct"] = (
        df["disponibilite_pct"].clip(0, 100)
        * df["performance_pct"].clip(0, 150)
        * df["qualite_pct"].clip(0, 100) / 10000
    ).clip(0, 100)
    # Use source TRS where available, otherwise the calculated value.
    if "TRS_pct" not in df.columns:
        df["TRS_pct"] = df["TRS_calcule_pct"]
    else:
        df["TRS_pct"] = df["TRS_pct"].where(df["TRS_pct"].between(0, 100), df["TRS_calcule_pct"])

    df["jour_projet"] = (df["date_heure"].dt.normalize() - df["date_heure"].dt.normalize().min()).dt.days + 1
    df["periode_TPM"] = np.where(df["jour_projet"] >= 60, "Après TPM/SMED (jour 60+)", "Avant TPM/SMED")
    df["temps_arrets_total_min"] = (
        df["temps_panne_min"] + df["temps_reglage_min"] + df.get("duree_micro_arrets_min", 0)
    )
    df["taux_rebut_pct"] = np.where(
        df["pieces_produites"] > 0,
        df["pieces_rebutees"] / df["pieces_produites"] * 100,
        0,
    )
    return df


# -------------------------------------------------------------------
# DATA SOURCE
# -------------------------------------------------------------------
st.sidebar.markdown("## 🏭 Renault Group")
st.sidebar.caption("Pilotage des performances industrielles")
uploaded = st.sidebar.file_uploader("Importer le fichier CSV", type=["csv"])
default_path = Path("data/zahir_hajar.csv")

try:
    if uploaded is not None:
        raw_df = load_csv(uploaded)
        source_name = uploaded.name
    elif default_path.exists():
        raw_df = load_csv(str(default_path))
        source_name = str(default_path)
    else:
        st.markdown("<div class='hero'><h1>Tableau de bord industriel</h1><p>Analyse de la production, des arrêts, de la qualité et de l'énergie</p></div>", unsafe_allow_html=True)
        st.info("Importez votre fichier CSV depuis le panneau latéral pour afficher les analyses. Le CSV n'est pas inclus dans ce projet.")
        st.stop()
    df = clean_data(raw_df)
except Exception as exc:
    st.error(f"Impossible de charger les données : {exc}")
    st.stop()

if st.sidebar.button("Déconnexion", use_container_width=True):
    st.session_state.authenticated = False
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### Filtres")
min_date = df["date_heure"].min().date()
max_date = df["date_heure"].max().date()
date_range = st.sidebar.date_input("Période", value=(min_date, max_date), min_value=min_date, max_value=max_date)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

def options_for(col):
    return sorted(df[col].dropna().astype(str).unique().tolist()) if col in df.columns else []

teams = st.sidebar.multiselect("Équipe", options_for("equipe"), default=options_for("equipe"))
machines = st.sidebar.multiselect("Machine", options_for("machine_id"), default=options_for("machine_id"))
products = st.sidebar.multiselect("Produit", options_for("produit"), default=options_for("produit"))
posts = st.sidebar.multiselect("Poste", options_for("poste"), default=options_for("poste"))

filtered = df[
    df["date_heure"].dt.date.between(start_date, end_date)
    & df["equipe"].astype(str).isin(teams)
    & df["machine_id"].astype(str).isin(machines)
    & df["produit"].astype(str).isin(products)
    & df["poste"].astype(str).isin(posts)
].copy()

st.markdown("""
<div class="hero">
  <h1>Tableau de bord · Performance industrielle</h1>
  <p>Renault Group Maroc&nbsp;&nbsp;|&nbsp;&nbsp;Production · Fiabilité · Qualité · Énergie</p>
</div>
""", unsafe_allow_html=True)

if filtered.empty:
    st.warning("Aucune donnée ne correspond aux filtres sélectionnés.")
    st.stop()

# KPI calculations
total_prod = filtered["pieces_produites"].sum()
good_prod = filtered["pieces_bonnes"].sum()
scrap = filtered["pieces_rebutees"].sum()
trs = filtered["TRS_pct"].mean()
availability = filtered["disponibilite_pct"].mean()
performance = filtered["performance_pct"].mean()
quality = filtered["qualite_pct"].mean()
downtime = filtered["temps_arrets_total_min"].sum()
energy = filtered["energie_kwh"].sum() if "energie_kwh" in filtered else np.nan
scrap_rate = scrap / total_prod * 100 if total_prod else 0
bottleneck = filtered.groupby("machine_id")["TRS_pct"].mean().idxmin()

def kpi(label, value, sub=""):
    st.markdown(
        f"<div class='kpi'><div class='kpi-label'>{label}</div>"
        f"<div class='kpi-value'>{value}</div><div class='kpi-sub'>{sub}</div></div>",
        unsafe_allow_html=True,
    )

k1, k2, k3, k4, k5, k6 = st.columns(6)
with k1: kpi("TRS moyen", f"{trs:.1f} %", "Disponibilité × performance × qualité")
with k2: kpi("Pièces produites", f"{total_prod:,.0f}".replace(",", " "), "Volume total")
with k3: kpi("Pièces bonnes", f"{good_prod:,.0f}".replace(",", " "), "Production conforme")
with k4: kpi("Taux de rebut", f"{scrap_rate:.2f} %", f"{scrap:,.0f} pièces rebutées")
with k5: kpi("Temps d'arrêt", f"{downtime/60:,.1f} h".replace(",", " "), "Pannes + réglages + micro-arrêts")
with k6: kpi("Énergie", f"{energy:,.0f} kWh".replace(",", " ") if pd.notna(energy) else "N/D", "Consommation sur la période")

st.markdown("<div class='section-title'>Vue d'ensemble</div>", unsafe_allow_html=True)
c1, c2 = st.columns([1.6, 1])
with c1:
    daily = filtered.set_index("date_heure").resample("D").agg(
        TRS=("TRS_pct", "mean"), Production=("pieces_produites", "sum")
    ).reset_index()
    fig, ax = plt.subplots(figsize=(9, 3.4))
    sns.lineplot(data=daily, x="date_heure", y="TRS", ax=ax, color=BLUE, linewidth=2.4, label="TRS moyen")
    ax.set_ylabel("TRS (%)"); ax.set_xlabel(""); ax.set_ylim(bottom=0)
    ax.set_title("Évolution quotidienne du TRS", loc="left", fontweight="bold")
    ax.legend(frameon=False)
    fig.tight_layout(); st.pyplot(fig, use_container_width=True); plt.close(fig)
with c2:
    by_machine = filtered.groupby("machine_id", as_index=False)["TRS_pct"].mean().sort_values("TRS_pct")
    fig, ax = plt.subplots(figsize=(6, 3.4))
    sns.barplot(data=by_machine, x="TRS_pct", y="machine_id", ax=ax, color=CYAN)
    ax.set_xlabel("TRS moyen (%)"); ax.set_ylabel("Machine")
    ax.set_title("Performance par machine", loc="left", fontweight="bold")
    fig.tight_layout(); st.pyplot(fig, use_container_width=True); plt.close(fig)

st.markdown("<div class='section-title'>Analyse des pertes et des goulots</div>", unsafe_allow_html=True)
c3, c4 = st.columns(2)
with c3:
    loss_cols = {
        "Pannes": filtered["temps_panne_min"].sum(),
        "Réglages": filtered["temps_reglage_min"].sum(),
        "Micro-arrêts": filtered["duree_micro_arrets_min"].sum() if "duree_micro_arrets_min" in filtered else 0,
    }
    loss_df = pd.DataFrame({"Type d'arrêt": list(loss_cols.keys()), "Minutes": list(loss_cols.values())})
    loss_df = loss_df.sort_values("Minutes", ascending=False)
    fig, ax = plt.subplots(figsize=(7, 3.5))
    sns.barplot(data=loss_df, x="Minutes", y="Type d'arrêt", ax=ax, color=ORANGE)
    ax.set_title("Répartition des temps d'arrêt", loc="left", fontweight="bold")
    fig.tight_layout(); st.pyplot(fig, use_container_width=True); plt.close(fig)
with c4:
    machine_loss = filtered.groupby("machine_id")["temps_arrets_total_min"].sum().sort_values(ascending=False).reset_index()
    machine_loss["Cumul (%)"] = machine_loss["temps_arrets_total_min"].cumsum() / max(machine_loss["temps_arrets_total_min"].sum(), 1) * 100
    fig, ax = plt.subplots(figsize=(7, 3.5))
    sns.barplot(data=machine_loss, x="machine_id", y="temps_arrets_total_min", ax=ax, color=BLUE)
    ax2 = ax.twinx()
    ax2.plot(range(len(machine_loss)), machine_loss["Cumul (%)"], color=RED, marker="o", linewidth=2)
    ax2.set_ylim(0, 110); ax2.set_ylabel("Cumul (%)")
    ax.set_ylabel("Minutes d'arrêt"); ax.set_xlabel("Machine")
    ax.set_title("Pareto des arrêts par machine", loc="left", fontweight="bold")
    fig.tight_layout(); st.pyplot(fig, use_container_width=True); plt.close(fig)

st.markdown("<div class='section-title'>Qualité et consommation énergétique</div>", unsafe_allow_html=True)
c5, c6 = st.columns(2)
with c5:
    quality_machine = filtered.groupby("machine_id", as_index=False).agg(
        Produites=("pieces_produites", "sum"), Rebuts=("pieces_rebutees", "sum")
    )
    quality_machine["Taux rebut (%)"] = np.where(quality_machine["Produites"] > 0, quality_machine["Rebuts"] / quality_machine["Produites"] * 100, 0)
    fig, ax = plt.subplots(figsize=(7, 3.4))
    sns.barplot(data=quality_machine, x="machine_id", y="Taux rebut (%)", ax=ax, color=RED)
    ax.set_title("Taux de rebut par machine", loc="left", fontweight="bold")
    fig.tight_layout(); st.pyplot(fig, use_container_width=True); plt.close(fig)
with c6:
    if "energie_kwh" in filtered.columns:
        energy_machine = filtered.groupby("machine_id", as_index=False)["energie_kwh"].sum()
        fig, ax = plt.subplots(figsize=(7, 3.4))
        sns.barplot(data=energy_machine, x="machine_id", y="energie_kwh", ax=ax, color=GREEN)
        ax.set_title("Consommation énergétique par machine", loc="left", fontweight="bold")
        ax.set_ylabel("Énergie (kWh)")
        fig.tight_layout(); st.pyplot(fig, use_container_width=True); plt.close(fig)
    else:
        st.info("La colonne energie_kwh n'est pas présente dans le fichier.")

st.markdown("<div class='section-title'>Évaluation de l'action TPM / SMED</div>", unsafe_allow_html=True)
if df["jour_projet"].max() >= 60:
    period = filtered.groupby("periode_TPM", as_index=False).agg(
        TRS_moyen=("TRS_pct", "mean"),
        Pannes_min=("temps_panne_min", "mean"),
        Reglages_min=("temps_reglage_min", "mean"),
        Arrets_total_min=("temps_arrets_total_min", "mean"),
    )
    p1, p2, p3 = st.columns(3)
    for col, metric, label, unit in [
        (p1, "TRS_moyen", "TRS moyen", "%"),
        (p2, "Pannes_min", "Pannes moyennes / relevé", " min"),
        (p3, "Reglages_min", "Réglages moyens / relevé", " min"),
    ]:
        before = period.loc[period["periode_TPM"] == "Avant TPM/SMED", metric]
        after = period.loc[period["periode_TPM"] == "Après TPM/SMED (jour 60+)", metric]
        with col:
            if len(before) and len(after):
                delta = after.iloc[0] - before.iloc[0]
                st.metric(label, f"{after.iloc[0]:.2f}{unit}", f"{delta:+.2f}{unit} vs avant")
            else:
                st.metric(label, "Données insuffisantes")
    fig, ax = plt.subplots(figsize=(8, 3.2))
    melted = period.melt(id_vars="periode_TPM", value_vars=["Pannes_min", "Reglages_min"], var_name="Type", value_name="Minutes moyennes")
    sns.barplot(data=melted, x="Type", y="Minutes moyennes", hue="periode_TPM", ax=ax)
    ax.set_title("Comparaison avant / après TPM-SMED", loc="left", fontweight="bold")
    fig.tight_layout(); st.pyplot(fig, use_container_width=True); plt.close(fig)
    st.caption("La séparation avant/après est basée sur le 60e jour du jeu de données, conformément à la consigne du projet.")
else:
    st.info("Le jeu de données ne couvre pas 60 jours : la comparaison TPM/SMED n'est pas encore calculable.")

# Insight and recommendations
st.markdown("<div class='section-title'>Diagnostic et recommandations</div>", unsafe_allow_html=True)
bottleneck_row = filtered.groupby(["machine_id", "poste"], as_index=False).agg(
    trs=("TRS_pct", "mean"), stops=("temps_arrets_total_min", "sum")
).sort_values("trs").iloc[0]
st.markdown(
    f"<div class='insight'><b>Goulot observé :</b> {bottleneck_row['machine_id']} — "
    f"{bottleneck_row['poste']}, avec un TRS moyen de {bottleneck_row['trs']:.1f} %. "
    "Prioriser l'analyse de ses arrêts et de ses pertes de cadence.</div>",
    unsafe_allow_html=True,
)
st.markdown("""
- **Fiabilité :** analyser les causes récurrentes des pannes et mettre à jour le plan de maintenance préventive.
- **Réglages :** standardiser les changements de série et poursuivre les actions SMED.
- **Micro-arrêts :** enregistrer les causes et traiter les incidents répétitifs au poste.
- **Qualité :** examiner les références et opérations générant le plus de rebuts.
- **Énergie :** suivre les kWh par pièce produite pour comparer les machines à volume comparable.
""")
st.warning("Limite des données : le fichier fourni ne contient pas de ville, région, client, expédition ni date de livraison. La couverture des livraisons dans tout le Maroc ne peut donc pas être cartographiée ni évaluée avec ce CSV. Ajoutez ces champs dans une future version pour créer un volet logistique national.")

with st.expander("Consulter les données filtrées"):
    st.dataframe(filtered, use_container_width=True, hide_index=True)
    csv_bytes = filtered.to_csv(index=False).encode("utf-8-sig")
    st.download_button("Télécharger les données filtrées (CSV)", csv_bytes, "renault_donnees_filtrees.csv", "text/csv")

with st.expander("Qualité et structure des données"):
    quality_report = pd.DataFrame({
        "Indicateur": ["Lignes chargées", "Lignes après nettoyage", "Doublons supprimés", "Colonnes disponibles"],
        "Valeur": [len(raw_df), len(df), len(raw_df)-len(df), len(df.columns)]
    })
    st.dataframe(quality_report, hide_index=True, use_container_width=True)
    st.caption(f"Source chargée : {source_name}")

st.markdown("<hr><div style='text-align:center;color:#94A3B8;font-size:11px'>Renault Group · Dashboard de démonstration · Analyse industrielle</div>", unsafe_allow_html=True)
