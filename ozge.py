# =============================================================================
# ELEKTRİKLİ ARACA GEÇİŞ SÜRECİ İÇİN KARAR DESTEK SİSTEMİ
# IPCC Tier 2 Metodolojisi & XGBoost Destekli Senaryo Analizi
# Karabük Üniversitesi – Endüstri Mühendisliği Lisans Bitirme Tezi
# Özge ÖZBAY & Sümeyye TEKİN
# =============================================================================
# Çalıştırmak için:
#   pip install streamlit pandas matplotlib numpy
#   streamlit run app.py
# =============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
from matplotlib.gridspec import GridSpec
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="EV Geçiş Karar Destek Sistemi",
    page_icon="⚡",
    layout="wide",
)

# ─────────────────────────────────────────────────────────────────────────────
# BÖLÜM 1 – SABİT DEĞERLER
# ─────────────────────────────────────────────────────────────────────────────

EF_CO2_DIZEL  = 2.690
EF_CO2_BENZIN = 2.350

EF_CH4_OTOBÜS_DIZEL    = 3.9
EF_N2O_OTOBÜS_DIZEL    = 3.9
EF_CH4_MINİBÜS_DIZEL   = 3.9
EF_N2O_MINİBÜS_DIZEL   = 3.9

EF_GRID     = 0.43
ETA_SARJ    = 0.90
E_OTOBÜS_EV = 0.18
E_MINİBÜS_EV= 0.12

TUK_OTOBÜS_DIZEL  = 0.33
TUK_MINİBÜS_DIZEL = 0.12

GWP_CH4 = 28
GWP_N2O = 265

ANALIZ_YILI = 15
AYLAR       = ANALIZ_YILI * 12

RENK = {
    "MD": "#555555",
    "S1": "#2166AC",
    "S2": "#F4A100",
    "S3": "#1B7837",
}
ETIKET = {
    "MD": "Mevcut Durum (Tam Dizel)",
    "S1": "Senaryo 1 – 1/3 EV Geçişi",
    "S2": "Senaryo 2 – 2/3 EV Geçişi",
    "S3": "Senaryo 3 – Tam EV Geçişi",
}

plt.rcParams.update({
    "font.family"      : "DejaVu Sans",
    "axes.titlesize"   : 13,
    "axes.labelsize"   : 11,
    "xtick.labelsize"  : 9,
    "ytick.labelsize"  : 9,
    "legend.fontsize"  : 9,
    "figure.dpi"       : 110,
    "axes.grid"        : True,
    "grid.alpha"       : 0.35,
    "axes.spines.top"  : False,
    "axes.spines.right": False,
})

# ─────────────────────────────────────────────────────────────────────────────
# BAŞLIK
# ─────────────────────────────────────────────────────────────────────────────

st.title("⚡ Elektrikli Araca Geçiş – Karar Destek Sistemi")
st.markdown(
    "**IPCC Tier 2 Metodolojisi | Karabük UlaşımAŞ Filo Analizi**  \n"
    "Karabük Üniversitesi – Endüstri Mühendisliği Lisans Bitirme Tezi  \n"
    "*Özge ÖZBAY & Sümeyye TEKİN*"
)
st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# BÖLÜM 3 – KULLANICI GİRİŞLERİ (SIDEBAR)
# ─────────────────────────────────────────────────────────────────────────────

st.sidebar.header("📋 Filo Bilgisi Girişi")

st.sidebar.subheader("Mevcut Filo")
n_otobüs_mevcut  = st.sidebar.number_input("Mevcut DİZEL OTOBÜS sayısı (adet)", min_value=1, value=10, step=1)
n_minibüs_mevcut = st.sidebar.number_input("Mevcut DİZEL MİNİBÜS sayısı (adet)", min_value=0, value=5, step=1)

st.sidebar.subheader("Araç Birim Fiyatları (TL)")
fiyat_otobüs_ev  = st.sidebar.number_input("Elektrikli OTOBÜS birim fiyatı (TL)", min_value=1.0, value=5_000_000.0, step=100_000.0, format="%.0f")
fiyat_minibüs_ev = st.sidebar.number_input("Elektrikli MİNİBÜS birim fiyatı (TL)", min_value=0.0, value=2_000_000.0, step=100_000.0, format="%.0f")

st.sidebar.subheader("Yıllık Bakım Maliyetleri (TL/araç/yıl)")
bakim_otobüs_dizel  = st.sidebar.number_input("Dizel OTOBÜS bakım (TL/araç)",      min_value=0.0, value=80_000.0, step=1_000.0, format="%.0f")
bakim_minibüs_dizel = st.sidebar.number_input("Dizel MİNİBÜS bakım (TL/araç)",     min_value=0.0, value=50_000.0, step=1_000.0, format="%.0f")
bakim_otobüs_ev     = st.sidebar.number_input("Elektrikli OTOBÜS bakım (TL/araç)", min_value=0.0, value=40_000.0, step=1_000.0, format="%.0f")
bakim_minibüs_ev    = st.sidebar.number_input("Elektrikli MİNİBÜS bakım (TL/araç)",min_value=0.0, value=25_000.0, step=1_000.0, format="%.0f")

st.sidebar.subheader("Yakıt ve Enerji Fiyatları")
dizel_fiyat    = st.sidebar.number_input("Dizel fiyatı (TL/L)",           min_value=0.01, value=45.50, step=0.50, format="%.2f")
elektrik_fiyat = st.sidebar.number_input("Elektrik / şarj ücreti (TL/kWh)", min_value=0.01, value=4.50, step=0.10, format="%.2f")

st.sidebar.subheader("Yıllık Kilometre (Filo Geneli)")
km_otobüs_yillik  = st.sidebar.number_input("OTOBÜS filosu toplam yıllık km",  min_value=1.0, value=1_000_000.0, step=10_000.0, format="%.0f")
km_minibüs_yillik = st.sidebar.number_input("MİNİBÜS filosu toplam yıllık km", min_value=0.0, value=300_000.0,   step=10_000.0, format="%.0f")

st.sidebar.subheader("Enflasyon")
tufe_yuzde = st.sidebar.number_input("Yıllık TÜFE oranı (%)", min_value=0.0, value=40.0, step=1.0, format="%.1f")
tufe_orani = tufe_yuzde / 100

hesapla = st.sidebar.button("🚀 Analizi Çalıştır", use_container_width=True, type="primary")

if not hesapla:
    st.info("👈 Sol panelden filo bilgilerini girin ve **Analizi Çalıştır** butonuna tıklayın.")
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# BÖLÜM 4 – SENARYO TANIMLARI
# ─────────────────────────────────────────────────────────────────────────────

n_otobüs_s1 = max(1, round(n_otobüs_mevcut / 3))
n_otobüs_s2 = max(1, round(2 * n_otobüs_mevcut / 3))
n_otobüs_s3 = n_otobüs_mevcut

n_minibüs_s1 = round(n_minibüs_mevcut / 3)
n_minibüs_s2 = round(2 * n_minibüs_mevcut / 3)
n_minibüs_s3 = n_minibüs_mevcut

md = dict(otobüs_dizel=n_otobüs_mevcut, otobüs_ev=0,
          minibüs_dizel=n_minibüs_mevcut, minibüs_ev=0)

s1 = dict(otobüs_dizel=n_otobüs_mevcut - n_otobüs_s1, otobüs_ev=n_otobüs_s1,
          minibüs_dizel=n_minibüs_mevcut - n_minibüs_s1, minibüs_ev=n_minibüs_s1)

s2 = dict(otobüs_dizel=n_otobüs_mevcut - n_otobüs_s2, otobüs_ev=n_otobüs_s2,
          minibüs_dizel=n_minibüs_mevcut - n_minibüs_s2, minibüs_ev=n_minibüs_s2)

s3 = dict(otobüs_dizel=0, otobüs_ev=n_otobüs_mevcut,
          minibüs_dizel=0, minibüs_ev=n_minibüs_mevcut)

st.subheader("📊 Senaryo Tanımları")
senaryo_df = pd.DataFrame([
    {"Senaryo": ETIKET["MD"], "Dizel Otobüs": md["otobüs_dizel"], "EV Otobüs": md["otobüs_ev"],
     "Dizel Minibüs": md["minibüs_dizel"], "EV Minibüs": md["minibüs_ev"]},
    {"Senaryo": ETIKET["S1"], "Dizel Otobüs": s1["otobüs_dizel"], "EV Otobüs": s1["otobüs_ev"],
     "Dizel Minibüs": s1["minibüs_dizel"], "EV Minibüs": s1["minibüs_ev"]},
    {"Senaryo": ETIKET["S2"], "Dizel Otobüs": s2["otobüs_dizel"], "EV Otobüs": s2["otobüs_ev"],
     "Dizel Minibüs": s2["minibüs_dizel"], "EV Minibüs": s2["minibüs_ev"]},
    {"Senaryo": ETIKET["S3"], "Dizel Otobüs": s3["otobüs_dizel"], "EV Otobüs": s3["otobüs_ev"],
     "Dizel Minibüs": s3["minibüs_dizel"], "EV Minibüs": s3["minibüs_ev"]},
])
st.dataframe(senaryo_df, use_container_width=True, hide_index=True)

# ─────────────────────────────────────────────────────────────────────────────
# BÖLÜM 5 – EMİSYON HESAPLARI (IPCC Tier 2)
# ─────────────────────────────────────────────────────────────────────────────

def emisyon_hesapla(senaryo, km_oto, km_mini):
    sonuc = {}
    oto_km_dizel = (senaryo["otobüs_dizel"] / max(n_otobüs_mevcut, 1)) * km_oto
    co2_oto_d  = oto_km_dizel * TUK_OTOBÜS_DIZEL * EF_CO2_DIZEL
    ch4_oto_d  = oto_km_dizel * EF_CH4_OTOBÜS_DIZEL / 1e6
    n2o_oto_d  = oto_km_dizel * EF_N2O_OTOBÜS_DIZEL / 1e6

    oto_km_ev  = (senaryo["otobüs_ev"] / max(n_otobüs_mevcut, 1)) * km_oto
    co2_oto_ev = oto_km_ev * (E_OTOBÜS_EV / ETA_SARJ) * EF_GRID

    mini_km_dizel = (senaryo["minibüs_dizel"] / max(n_minibüs_mevcut, 1)) * km_mini if n_minibüs_mevcut > 0 else 0
    co2_mini_d  = mini_km_dizel * TUK_MINİBÜS_DIZEL * EF_CO2_DIZEL
    ch4_mini_d  = mini_km_dizel * EF_CH4_MINİBÜS_DIZEL / 1e6
    n2o_mini_d  = mini_km_dizel * EF_N2O_MINİBÜS_DIZEL / 1e6

    mini_km_ev  = (senaryo["minibüs_ev"] / max(n_minibüs_mevcut, 1)) * km_mini if n_minibüs_mevcut > 0 else 0
    co2_mini_ev = mini_km_ev * (E_MINİBÜS_EV / ETA_SARJ) * EF_GRID

    sonuc["CO2_kg"]  = co2_oto_d + co2_oto_ev + co2_mini_d + co2_mini_ev
    sonuc["CH4_kg"]  = ch4_oto_d + ch4_mini_d
    sonuc["N2O_kg"]  = n2o_oto_d + n2o_mini_d
    sonuc["CO2e_ton"] = (
        sonuc["CO2_kg"] + sonuc["CH4_kg"] * GWP_CH4 + sonuc["N2O_kg"] * GWP_N2O
    ) / 1000
    sonuc["CO2_oto_dizel_kg"]  = co2_oto_d
    sonuc["CO2_oto_ev_kg"]     = co2_oto_ev
    sonuc["CO2_mini_dizel_kg"] = co2_mini_d
    sonuc["CO2_mini_ev_kg"]    = co2_mini_ev
    return sonuc

em_md = emisyon_hesapla(md, km_otobüs_yillik, km_minibüs_yillik)
em_s1 = emisyon_hesapla(s1, km_otobüs_yillik, km_minibüs_yillik)
em_s2 = emisyon_hesapla(s2, km_otobüs_yillik, km_minibüs_yillik)
em_s3 = emisyon_hesapla(s3, km_otobüs_yillik, km_minibüs_yillik)

# ─────────────────────────────────────────────────────────────────────────────
# BÖLÜM 6 – EMİSYON GRAFİKLERİ
# ─────────────────────────────────────────────────────────────────────────────

st.divider()
st.subheader("🌿 IPCC Tier 2 – Senaryo Bazlı Yıllık Emisyon Karşılaştırması")

tum_kodlar     = ["MD", "S1", "S2", "S3"]
tum_etiketler  = [ETIKET[k] for k in tum_kodlar]
tum_renkler    = [RENK[k]   for k in tum_kodlar]
tum_emisyonlar = [em_md, em_s1, em_s2, em_s3]

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle(
    "IPCC Tier 2 Metodolojisi – Senaryo Bazlı Yıllık Emisyon Karşılaştırması\n"
    "Karabük UlaşımAŞ Toplu Taşıma Filosu",
    fontsize=13, fontweight="bold", y=1.01
)

ax = axes[0, 0]
vals = [e["CO2_kg"] / 1000 for e in tum_emisyonlar]
bars = ax.bar(tum_etiketler, vals, color=tum_renkler, width=0.5, edgecolor="white", linewidth=1.2)
ax.set_title("CO₂ Emisyonu", fontweight="bold")
ax.set_ylabel("CO₂ (ton/yıl)")
ax.set_xticklabels(tum_etiketler, rotation=12, ha="right")
for bar, v in zip(bars, vals):
    ax.text(bar.get_x() + bar.get_width() / 2, v + max(vals) * 0.01,
            f"{v:,.0f}", ha="center", va="bottom", fontsize=9, fontweight="bold")
ax.set_ylim(0, max(vals) * 1.18)

ax = axes[0, 1]
vals = [e["CH4_kg"] for e in tum_emisyonlar]
bars = ax.bar(tum_etiketler, vals, color=tum_renkler, width=0.5, edgecolor="white", linewidth=1.2)
ax.set_title("CH₄ Emisyonu", fontweight="bold")
ax.set_ylabel("CH₄ (kg/yıl)")
ax.set_xticklabels(tum_etiketler, rotation=12, ha="right")
for bar, v in zip(bars, vals):
    ax.text(bar.get_x() + bar.get_width() / 2, v + max(vals) * 0.01,
            f"{v:,.3f}", ha="center", va="bottom", fontsize=9, fontweight="bold")
ax.set_ylim(0, max(vals) * 1.18 if max(vals) > 0 else 1)

ax = axes[1, 0]
vals = [e["N2O_kg"] for e in tum_emisyonlar]
bars = ax.bar(tum_etiketler, vals, color=tum_renkler, width=0.5, edgecolor="white", linewidth=1.2)
ax.set_title("N₂O Emisyonu", fontweight="bold")
ax.set_ylabel("N₂O (kg/yıl)")
ax.set_xticklabels(tum_etiketler, rotation=12, ha="right")
for bar, v in zip(bars, vals):
    ax.text(bar.get_x() + bar.get_width() / 2, v + max(vals) * 0.01,
            f"{v:,.3f}", ha="center", va="bottom", fontsize=9, fontweight="bold")
ax.set_ylim(0, max(vals) * 1.18 if max(vals) > 0 else 1)

ax = axes[1, 1]
vals = [e["CO2e_ton"] for e in tum_emisyonlar]
bars = ax.bar(tum_etiketler, vals, color=tum_renkler, width=0.5, edgecolor="white", linewidth=1.2)
ax.set_title("Toplam CO₂e Emisyonu (GWP₁₀₀, AR5)", fontweight="bold")
ax.set_ylabel("CO₂e (ton/yıl)")
ax.set_xticklabels(tum_etiketler, rotation=12, ha="right")
for bar, v in zip(bars, vals):
    ax.text(bar.get_x() + bar.get_width() / 2, v + max(vals) * 0.01,
            f"{v:,.1f}", ha="center", va="bottom", fontsize=9, fontweight="bold")
ax.set_ylim(0, max(vals) * 1.18)

plt.tight_layout()
st.pyplot(fig)
plt.close(fig)

# 6.5 – Emisyon azalma yüzdeleri
fig, ax = plt.subplots(figsize=(9, 4))
gaz_adlari = ["CO₂ (ton/yıl)", "CH₄ (kg/yıl)", "N₂O (kg/yıl)", "CO₂e (ton/yıl)"]
md_vals = [em_md["CO2_kg"]/1000, em_md["CH4_kg"], em_md["N2O_kg"], em_md["CO2e_ton"]]
s1_vals = [em_s1["CO2_kg"]/1000, em_s1["CH4_kg"], em_s1["N2O_kg"], em_s1["CO2e_ton"]]
s2_vals = [em_s2["CO2_kg"]/1000, em_s2["CH4_kg"], em_s2["N2O_kg"], em_s2["CO2e_ton"]]
s3_vals = [em_s3["CO2_kg"]/1000, em_s3["CH4_kg"], em_s3["N2O_kg"], em_s3["CO2e_ton"]]

pct_s1 = [(1 - s1_vals[i]/md_vals[i])*100 if md_vals[i]>0 else 0 for i in range(4)]
pct_s2 = [(1 - s2_vals[i]/md_vals[i])*100 if md_vals[i]>0 else 0 for i in range(4)]
pct_s3 = [(1 - s3_vals[i]/md_vals[i])*100 if md_vals[i]>0 else 0 for i in range(4)]

y     = np.arange(len(gaz_adlari))
width = 0.25
ax.barh(y - width, pct_s1, width, color=RENK["S1"], label=ETIKET["S1"])
ax.barh(y,         pct_s2, width, color=RENK["S2"], label=ETIKET["S2"])
ax.barh(y + width, pct_s3, width, color=RENK["S3"], label=ETIKET["S3"])
ax.set_yticks(y)
ax.set_yticklabels(gaz_adlari)
ax.set_xlabel("Mevcut Duruma Göre Emisyon Azalma Oranı (%)")
ax.set_title("Emisyon Azalma Oranları – Mevcut Duruma Kıyasla", fontweight="bold")
ax.legend(loc="lower right")
for i, (p1, p2, p3) in enumerate(zip(pct_s1, pct_s2, pct_s3)):
    ax.text(p1 + 0.5, i - width,   f"%{p1:.1f}", va="center", fontsize=8)
    ax.text(p2 + 0.5, i,           f"%{p2:.1f}", va="center", fontsize=8)
    ax.text(p3 + 0.5, i + width,   f"%{p3:.1f}", va="center", fontsize=8)
ax.set_xlim(0, 115)
plt.tight_layout()
st.pyplot(fig)
plt.close(fig)

# ─────────────────────────────────────────────────────────────────────────────
# BÖLÜM 7 – MALİYET HESAPLARI
# ─────────────────────────────────────────────────────────────────────────────

def maliyet_serileri(senaryo, n_arac_ev_oto, n_arac_ev_mini,
                     fiyat_oto_ev, fiyat_mini_ev, tufe, yil=15):
    aylık_yakıt_dizel_0  = (
        senaryo["otobüs_dizel"]  * (km_otobüs_yillik  / n_otobüs_mevcut  if n_otobüs_mevcut  else 0) * TUK_OTOBÜS_DIZEL  * dizel_fiyat +
        senaryo["minibüs_dizel"] * (km_minibüs_yillik / n_minibüs_mevcut if n_minibüs_mevcut else 0) * TUK_MINİBÜS_DIZEL * dizel_fiyat
    ) / 12

    aylık_yakıt_ev_0 = (
        senaryo["otobüs_ev"]  * (km_otobüs_yillik  / n_otobüs_mevcut  if n_otobüs_mevcut  else 0) * (E_OTOBÜS_EV  / ETA_SARJ) * elektrik_fiyat +
        senaryo["minibüs_ev"] * (km_minibüs_yillik / n_minibüs_mevcut if n_minibüs_mevcut else 0) * (E_MINİBÜS_EV / ETA_SARJ) * elektrik_fiyat
    ) / 12

    aylık_bakım_0 = (
        senaryo["otobüs_dizel"]  * bakim_otobüs_dizel  +
        senaryo["minibüs_dizel"] * bakim_minibüs_dizel +
        senaryo["otobüs_ev"]     * bakim_otobüs_ev     +
        senaryo["minibüs_ev"]    * bakim_minibüs_ev
    ) / 12

    yatirim_toplam = n_arac_ev_oto * fiyat_oto_ev + n_arac_ev_mini * fiyat_mini_ev
    if tufe > 0:
        carpan_toplami = sum((1 + tufe) ** t for t in range(yil))
        taksit_yil1_yillik = yatirim_toplam / carpan_toplami
    else:
        taksit_yil1_yillik = yatirim_toplam / yil if yil > 0 else 0

    kayitlar = []
    for ay in range(1, yil * 12 + 1):
        yil_no = (ay - 1) // 12
        yil_carpani = (1 + tufe) ** yil_no
        yakıt  = (aylık_yakıt_dizel_0 + aylık_yakıt_ev_0) * yil_carpani
        bakım  = aylık_bakım_0 * yil_carpani
        taksit = (taksit_yil1_yillik / 12) * yil_carpani if yatirim_toplam > 0 else 0
        toplam = yakıt + bakım + taksit
        kayitlar.append({
            "ay"    : ay,
            "yil"   : yil_no + 1,
            "yakıt" : yakıt,
            "bakım" : bakım,
            "taksit": taksit,
            "toplam": toplam,
        })
    return pd.DataFrame(kayitlar)

df_md = maliyet_serileri(md, 0, 0, 0, 0, tufe_orani)
df_s1 = maliyet_serileri(s1, n_otobüs_s1, n_minibüs_s1, fiyat_otobüs_ev, fiyat_minibüs_ev, tufe_orani)
df_s2 = maliyet_serileri(s2, n_otobüs_s2, n_minibüs_s2, fiyat_otobüs_ev, fiyat_minibüs_ev, tufe_orani)
df_s3 = maliyet_serileri(s3, n_otobüs_mevcut, n_minibüs_mevcut, fiyat_otobüs_ev, fiyat_minibüs_ev, tufe_orani)

# ─────────────────────────────────────────────────────────────────────────────
# BÖLÜM 8 – MEVCUT DURUM AYLIK MALİYET
# ─────────────────────────────────────────────────────────────────────────────

st.divider()
st.subheader("💰 15 Yıllık Maliyet Analizi")

st.markdown("**Mevcut Durum (Tam Dizel): Aylık Maliyet**")
fig, ax = plt.subplots(figsize=(14, 5))
ax.set_title(
    f"Mevcut Durum (Tam Dizel): Aylık Yakıt + Bakım Maliyeti\n"
    f"(15 Yıl | TÜFE: %{tufe_orani*100:.1f} | Tek yıllar → mavi, çift yıllar → yeşil)",
    fontweight="bold"
)
for _, grp in df_md.groupby("yil"):
    yil_no = int(grp["yil"].iloc[0])
    renk   = "#2166AC" if yil_no % 2 == 1 else "#4DAC26"
    ax.plot(grp["ay"], grp["toplam"] / 1e6, color=renk, linewidth=1.8)

mavi_p  = mpatches.Patch(color="#2166AC", label="Tek yıllar (1,3,5…13)")
yesil_p = mpatches.Patch(color="#4DAC26", label="Çift yıllar (2,4,6…14)")
ax.legend(handles=[mavi_p, yesil_p], loc="upper left")
ax.set_xlabel("Ay")
ax.set_ylabel("Aylık Maliyet (Milyon TL)")
ax.xaxis.set_major_locator(mticker.MultipleLocator(12))
ax.xaxis.set_minor_locator(mticker.MultipleLocator(6))
for y in range(1, ANALIZ_YILI + 1):
    ax.axvline(y * 12, color="gray", lw=0.5, alpha=0.4, linestyle="--")
plt.tight_layout()
st.pyplot(fig)
plt.close(fig)

# ─────────────────────────────────────────────────────────────────────────────
# BÖLÜM 9 – SENARYO GRAFİKLERİ + ÖDEME PLANLARI
# ─────────────────────────────────────────────────────────────────────────────

def ciz_senaryo_maliyet(df, kod):
    renk = RENK[kod]
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.set_title(
        f"{ETIKET[kod]}: Aylık Toplam Maliyet (Yakıt + Bakım + Araç Taksiti)\n"
        f"(15 Yıl | TÜFE: %{tufe_orani*100:.1f})",
        fontweight="bold"
    )
    ax.fill_between(df["ay"], df["yakıt"] / 1e6, alpha=0.4, color=renk, label="Yakıt")
    ax.fill_between(df["ay"], (df["yakıt"] + df["bakım"]) / 1e6, df["yakıt"] / 1e6,
                    alpha=0.4, color="gray", label="Bakım")
    ax.fill_between(df["ay"], df["toplam"] / 1e6, (df["yakıt"] + df["bakım"]) / 1e6,
                    alpha=0.4, color="orange", label="Araç Taksiti")
    ax.plot(df["ay"], df["toplam"] / 1e6, color=renk, linewidth=2, label="Toplam")
    ax.set_xlabel("Ay")
    ax.set_ylabel("Aylık Maliyet (Milyon TL)")
    ax.legend(loc="upper left")
    ax.xaxis.set_major_locator(mticker.MultipleLocator(12))
    for y in range(1, ANALIZ_YILI + 1):
        ax.axvline(y * 12, color="gray", lw=0.5, alpha=0.4, linestyle="--")
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

def odeme_plani_tablosu(df, kod):
    st.markdown(f"**15 Yıllık Ödeme Planı – {ETIKET[kod]}**")
    yillik_df = df.groupby("yil").mean(numeric_only=True).reset_index()
    yillik_df.columns = ["Yıl", "Ay (ort.)", "Aylık Yakıt (TL)", "Aylık Bakım (TL)", "Aylık Taksit (TL)", "Aylık Toplam (TL)"]
    yillik_df = yillik_df[["Yıl", "Aylık Yakıt (TL)", "Aylık Bakım (TL)", "Aylık Taksit (TL)", "Aylık Toplam (TL)"]]
    for col in ["Aylık Yakıt (TL)", "Aylık Bakım (TL)", "Aylık Taksit (TL)", "Aylık Toplam (TL)"]:
        yillik_df[col] = yillik_df[col].map(lambda x: f"{x:,.0f}")
    st.dataframe(yillik_df, use_container_width=True, hide_index=True)

def ciz_yillik_toplam(df, kod):
    yillik = df.groupby("yil")["toplam"].sum().reset_index()
    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(yillik["yil"], yillik["toplam"] / 1e6,
                  color=RENK[kod], edgecolor="white", linewidth=1.2)
    ax.set_title(f"{ETIKET[kod]}: Yıllık Toplam Maliyet (15 Yıl)", fontweight="bold")
    ax.set_xlabel("Yıl")
    ax.set_ylabel("Yıllık Toplam Maliyet (Milyon TL)")
    ax.set_xticks(yillik["yil"])
    for bar, v in zip(bars, yillik["toplam"] / 1e6):
        ax.text(bar.get_x() + bar.get_width() / 2, v + yillik["toplam"].max() / 1e6 * 0.01,
                f"{v:.1f}M", ha="center", va="bottom", fontsize=8)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

for kod, df_ in [("S1", df_s1), ("S2", df_s2), ("S3", df_s3)]:
    st.markdown(f"---\n### {ETIKET[kod]}")
    ciz_senaryo_maliyet(df_, kod)
    odeme_plani_tablosu(df_, kod)
    ciz_yillik_toplam(df_, kod)

# ─────────────────────────────────────────────────────────────────────────────
# BÖLÜM 9B – BAŞA BAŞ NOKTASI (AMORTİSMAN)
# ─────────────────────────────────────────────────────────────────────────────

st.divider()
st.subheader("📉 Başa Baş Noktası (Amorti) Analizi")

st.markdown(
    "**Yöntem:** Her senaryo için başlangıç yatırım maliyeti (−) ile "
    "ilerleyen aylarda mevcut duruma göre elde edilen tasarruflar (+) "
    "kümülatif olarak toplanır. Grafik sıfırı kestiğinde yatırım "
    "kendini amorti etmiş demektir (başa baş noktası = amorti yılı)."
)

def basbas_serileri(df_sen, df_md_ref, yatirim_toplam):
    tasarruf_aylik = (df_md_ref["yakıt"] + df_md_ref["bakım"]).values - \
                     (df_sen["yakıt"]   + df_sen["bakım"]).values
    kumul = np.cumsum(tasarruf_aylik) - yatirim_toplam
    return kumul

def yatirim_hesapla(n_oto_ev, n_mini_ev):
    return n_oto_ev * fiyat_otobüs_ev + n_mini_ev * fiyat_minibüs_ev

yatirim_s1 = yatirim_hesapla(n_otobüs_s1, n_minibüs_s1)
yatirim_s2 = yatirim_hesapla(n_otobüs_s2, n_minibüs_s2)
yatirim_s3 = yatirim_hesapla(n_otobüs_mevcut, n_minibüs_mevcut)

kumul_s1 = basbas_serileri(df_s1, df_md, yatirim_s1)
kumul_s2 = basbas_serileri(df_s2, df_md, yatirim_s2)
kumul_s3 = basbas_serileri(df_s3, df_md, yatirim_s3)

aylar_x = np.arange(1, ANALIZ_YILI * 12 + 1)

def bul_basbas_ay(kumul_dizi):
    for i, v in enumerate(kumul_dizi):
        if v >= 0:
            return i + 1
    return None

def ay_yil_str(ay):
    if ay is None:
        return "15 yıl içinde amorti edilemiyor"
    yil = (ay - 1) // 12 + 1
    kalan_ay = (ay - 1) % 12
    return f"Yıl {yil}, Ay {kalan_ay + 1} (≈ {ay/12:.1f}. yıl)"

bb_s1 = bul_basbas_ay(kumul_s1)
bb_s2 = bul_basbas_ay(kumul_s2)
bb_s3 = bul_basbas_ay(kumul_s3)

col1, col2, col3 = st.columns(3)
col1.metric("Senaryo 1 – Amorti", ay_yil_str(bb_s1))
col2.metric("Senaryo 2 – Amorti", ay_yil_str(bb_s2))
col3.metric("Senaryo 3 – Amorti", ay_yil_str(bb_s3))

fig, ax = plt.subplots(figsize=(13, 6))
ax.plot(aylar_x, kumul_s1 / 1e6, color=RENK["S1"], linewidth=2.2, label=ETIKET["S1"])
ax.plot(aylar_x, kumul_s2 / 1e6, color=RENK["S2"], linewidth=2.2, label=ETIKET["S2"])
ax.plot(aylar_x, kumul_s3 / 1e6, color=RENK["S3"], linewidth=2.2, label=ETIKET["S3"])
ax.axhline(0, color="black", linewidth=1.4, linestyle="--", label="Başa Baş Seviyesi (Amorti)")

for bb_ay, kod in [(bb_s1, "S1"), (bb_s2, "S2"), (bb_s3, "S3")]:
    if bb_ay is not None:
        bb_yil = bb_ay / 12
        ax.axvline(bb_ay, color=RENK[kod], linewidth=1.2, linestyle=":", alpha=0.7)
        ax.scatter([bb_ay], [0], color=RENK[kod], zorder=5, s=90, edgecolors="white", linewidth=1.5)
        ylim = ax.get_ylim()
        yt = ylim[1] * 0.05 if ylim[1] != 0 else 5
        ax.annotate(
            f"Amorti\n{bb_yil:.1f}. yıl",
            xy=(bb_ay, 0),
            xytext=(bb_ay + 2, yt),
            fontsize=8, color=RENK[kod], fontweight="bold",
            arrowprops=dict(arrowstyle="->", color=RENK[kod], lw=1.2),
        )

for y in range(1, ANALIZ_YILI + 1):
    ax.axvline(y * 12, color="gray", lw=0.4, alpha=0.3, linestyle="--")

ax.set_xlabel("Ay")
ax.set_ylabel("Kümülatif Net Tasarruf (Milyon TL)\n← Zarar | Kar →")
ax.set_title(
    "Başa Baş Noktası (Amorti) Analizi – Mevcut Duruma Göre Kümülatif Tasarruf\n"
    "Grafik sıfırı kestiğinde yatırım kendini amorti etmiş olur (= Amorti Yılı)",
    fontweight="bold"
)
ax.legend(loc="lower right")
ax.xaxis.set_major_locator(mticker.MultipleLocator(12))
plt.tight_layout()
st.pyplot(fig)
plt.close(fig)

# ─────────────────────────────────────────────────────────────────────────────
# BÖLÜM 10 – KÜMÜLATİF MALİYET KARŞILAŞTIRMA
# ─────────────────────────────────────────────────────────────────────────────

st.divider()
st.subheader("📈 Senaryo Bazlı Kümülatif Maliyet Karşılaştırması – 15 Yıl")

fig, ax = plt.subplots(figsize=(12, 6))
for df_, kod in [(df_md, "MD"), (df_s1, "S1"), (df_s2, "S2"), (df_s3, "S3")]:
    cumul = df_["toplam"].cumsum() / 1e9
    ax.plot(df_["ay"], cumul, color=RENK[kod], linewidth=2.5, label=ETIKET[kod])

ax.set_title("Senaryo Bazlı Kümülatif Maliyet Karşılaştırması – 15 Yıl", fontweight="bold")
ax.set_xlabel("Ay")
ax.set_ylabel("Kümülatif Toplam Maliyet (Milyar TL)")
ax.legend(loc="upper left")
ax.xaxis.set_major_locator(mticker.MultipleLocator(12))
for y in range(1, ANALIZ_YILI + 1):
    ax.axvline(y * 12, color="gray", lw=0.4, alpha=0.3, linestyle="--")
plt.tight_layout()
st.pyplot(fig)
plt.close(fig)

# ─────────────────────────────────────────────────────────────────────────────
# BÖLÜM 12 – ÖZET RAPOR
# ─────────────────────────────────────────────────────────────────────────────

st.divider()
st.subheader("📋 Özet Rapor")

ozet_data = []
for kod, em, df_ in [
    ("MD", em_md, df_md),
    ("S1", em_s1, df_s1),
    ("S2", em_s2, df_s2),
    ("S3", em_s3, df_s3),
]:
    satir = {
        "Senaryo"        : ETIKET[kod],
        "CO₂e/yıl (ton)" : f"{em['CO2e_ton']:,.1f}",
        "15Y Toplam (MilyarTL)": f"{df_['toplam'].sum()/1e9:,.2f}",
    }
    if kod != "MD":
        bb_ay = {"S1": bb_s1, "S2": bb_s2, "S3": bb_s3}[kod]
        satir["Amorti"] = ay_yil_str(bb_ay)
    else:
        satir["Amorti"] = "—"
    ozet_data.append(satir)

st.dataframe(pd.DataFrame(ozet_data), use_container_width=True, hide_index=True)

st.info(
    f"**Sistem Parametreleri:** Analiz Süresi: {ANALIZ_YILI} yıl | "
    f"TÜFE: %{tufe_orani*100:.1f} | Dizel: {dizel_fiyat:.2f} TL/L | "
    f"Elektrik: {elektrik_fiyat:.2f} TL/kWh | Şarj Verimi: %{ETA_SARJ*100:.0f} | "
    f"Şebeke EF (Türkiye): {EF_GRID} kg CO₂/kWh [IEA 2023]"
)
