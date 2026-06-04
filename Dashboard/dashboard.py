import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import os

sns.set_theme(style="whitegrid")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ---------- helper ----------
def render(fig):
    """Tampilkan figure lalu tutup agar tidak menumpuk di memori."""
    st.pyplot(fig)
    plt.close(fig)


def tentukan_musim(b):
    if b in [12, 1, 2]:
        return "Dingin"
    elif b in [3, 4, 5]:
        return "Semi"
    elif b in [6, 7, 8]:
        return "Panas"
    else:
        return "Gugur"


# ---------- LOAD DATA ----------
@st.cache_data
def load_data():
    df = pd.concat(
        [pd.read_csv(os.path.join(BASE_DIR, f"air_quality_part{i}.csv")) for i in (1, 2, 3)],
        ignore_index=True,
    )

    if "datetime" in df.columns:
        df["datetime"] = pd.to_datetime(df["datetime"])
    else:
        df["datetime"] = pd.to_datetime(df[["year", "month", "day", "hour"]])

    # Pakai kolom yang sudah ada di CSV; hitung hanya jika belum ada.
    if "musim" not in df.columns:
        df["musim"] = df["month"].apply(tentukan_musim)
    if "melebihi_ambang" not in df.columns:
        df["melebihi_ambang"] = df["PM2.5"] > 75

    return df.sort_values("datetime")


all_df = load_data()

# ---------- SIDEBAR / FILTER ----------
min_date = all_df["datetime"].min().date()
max_date = all_df["datetime"].max().date()
daftar_stasiun = sorted(all_df["station"].unique())

with st.sidebar:
    st.title("Filter Data")
    st.markdown("Dashboard Kualitas Udara Beijing")

    rentang = st.date_input(
        label="Rentang Waktu",
        min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date],
    )

    stasiun_pilihan = st.multiselect(
        label="Pilih Stasiun",
        options=daftar_stasiun,
        default=daftar_stasiun,
    )

# Guard: saat user baru memilih satu tanggal, date_input mengembalikan 1 elemen.
if not isinstance(rentang, (list, tuple)) or len(rentang) != 2:
    st.info("Pilih tanggal awal dan akhir untuk menampilkan data.")
    st.stop()
start_date, end_date = rentang

# Terapkan filter
main_df = all_df[
    (all_df["datetime"].dt.date >= start_date)
    & (all_df["datetime"].dt.date <= end_date)
    & (all_df["station"].isin(stasiun_pilihan))
]

# Guard filter kosong
if main_df.empty:
    st.warning("Tidak ada data untuk filter ini. Pilih minimal satu stasiun dan rentang tanggal yang valid.")
    st.stop()

# ---------- HEADER & METRIC ----------
st.header("Dashboard Kualitas Udara Beijing :cloud:")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Rata-rata PM2.5", f"{main_df['PM2.5'].mean():.1f} µg/m³")
with col2:
    st.metric("Median PM2.5", f"{main_df['PM2.5'].median():.1f} µg/m³")
with col3:
    st.metric("% Jam > 75 µg/m³", f"{main_df['melebihi_ambang'].mean()*100:.1f}%")

# ================= P1 — TREN =================
st.subheader("P1 · Tren PM2.5 dari Waktu ke Waktu")
ts = main_df.set_index("datetime")["PM2.5"].resample("ME").mean().dropna()
fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(ts.index, ts.values, color="#C44E52", label="Rata-rata bulanan")
if len(ts) >= 2:
    t = np.arange(len(ts))
    slope, intercept = np.polyfit(t, ts.values, 1)
    yhat = slope * t + intercept
    r2 = 1 - ((ts.values - yhat) ** 2).sum() / ((ts.values - ts.values.mean()) ** 2).sum()
    ax.plot(ts.index, yhat, color="black", ls="--", lw=2, label="Garis tren")
    st.caption(f"Laju perubahan kurang lebih {slope*12:+.2f} µg/m³ per tahun · R² = {r2:.3f}")
ax.set_ylabel("PM2.5 (µg/m³)")
ax.set_xlabel("")
ax.legend()
render(fig)

# ================= P2 — MUSIM & JAM =================
st.subheader("P2 · Pola Musiman & Harian")
col1, col2 = st.columns(2)
with col1:
    urut = ["Dingin", "Gugur", "Semi", "Panas"]
    musim_avg = main_df.groupby("musim")["PM2.5"].mean().reindex(urut).dropna()
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.barplot(x=musim_avg.index, y=musim_avg.values, palette="coolwarm", ax=ax,
                hue=musim_avg.index, legend=False)
    ax.set_title("Rata-rata PM2.5 per Musim")
    ax.set_ylabel("PM2.5 (µg/m³)")
    ax.set_xlabel("")
    render(fig)
with col2:
    diurnal = main_df.groupby("hour")["PM2.5"].mean()
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(diurnal.index, diurnal.values, marker="o", color="#8172B3")
    ax.set_title("Pola Harian PM2.5")
    ax.set_xlabel("Jam")
    ax.set_ylabel("PM2.5 (µg/m³)")
    render(fig)
if not musim_avg.empty:
    st.caption(
        f"Amplitudo musim kurang lebih {musim_avg.max()-musim_avg.min():.1f} µg/m³ · "
        f"amplitudo harian kurang lebih {diurnal.max()-diurnal.min():.1f} µg/m³"
    )

# ================= P3 — RATA-RATA PER STASIUN =================
st.subheader("P3 · Rata-rata PM2.5 per Stasiun")
mean_st = main_df.groupby("station")["PM2.5"].mean().sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(12, 5))
sns.barplot(x=mean_st.index, y=mean_st.values, palette="flare", ax=ax,
            hue=mean_st.index, legend=False)
ax.axhline(mean_st.mean(), color="blue", ls="--", label=f"Rata-rata {mean_st.mean():.1f}")
ax.set_title("Rata-rata PM2.5 per Stasiun (makin tinggi = makin berpolusi)")
ax.set_ylabel("PM2.5 (µg/m³)")
ax.set_xlabel("")
ax.legend()
plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
render(fig)

# ================= P4 — % MELEBIHI AMBANG =================
st.subheader("P4 · Proporsi Jam Melebihi Ambang (PM2.5 > 75 µg/m³)")
prop = (main_df.groupby("station")["melebihi_ambang"].mean() * 100).sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(12, 5))
sns.barplot(x=prop.index, y=prop.values, palette="rocket_r", ax=ax,
            hue=prop.index, legend=False)
ax.axhline(prop.mean(), color="blue", ls="--", label=f"Rata-rata {prop.mean():.0f}%")
ax.set_ylabel("Persentase (%)")
ax.set_xlabel("")
ax.legend()
plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
render(fig)
st.caption("Catatan: 75 µg/m³ adalah standar rata-rata 24 jam (China CAAQS); di sini dibaca sebagai persentase jam di atas 75, bukan pelanggaran standar resmi.")

# ================= P5 — KORELASI =================
st.subheader("P5 · Korelasi Antar Variabel")
kolom = ["PM2.5", "PM10", "SO2", "NO2", "CO", "O3", "TEMP", "PRES", "DEWP", "RAIN", "WSPM"]
fig, ax = plt.subplots(figsize=(10, 8))
sns.heatmap(main_df[kolom].corr(), annot=True, fmt=".2f", cmap="RdBu_r", center=0, ax=ax)
render(fig)

# ================= ANALISIS LANJUTAN — CV =================
with st.expander("Analisis Lanjutan · Variabilitas PM2.5 per Stasiun (Koefisien Variasi)"):
    cv = main_df.groupby("station")["PM2.5"].agg(
        lambda s: s.std() / s.mean()
    ).sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(12, 5))
    sns.barplot(x=cv.index, y=cv.values, palette="magma", ax=ax, hue=cv.index, legend=False)
    ax.axhline(cv.mean(), color="blue", ls="--", label=f"Rata-rata CV = {cv.mean():.2f}")
    ax.set_title("Koefisien Variasi per Stasiun (makin tinggi = makin fluktuatif)")
    ax.set_ylabel("Koefisien Variasi")
    ax.set_xlabel("")
    ax.legend()
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    render(fig)

st.caption("Proyek Analisis Data — Kualitas Udara Beijing (Mar 2013 – Feb 2017)")
