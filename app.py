from pathlib import Path

import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
LOGO_PATH = BASE_DIR / "logo aplikasi.png"
BACKGROUND_PATH = BASE_DIR / "Background Aplikasi.jpg"

st.set_page_config(
    page_title="Claim Bensin & Parkir",
    page_icon=str(LOGO_PATH) if LOGO_PATH.exists() else "⛽",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "processed_claim_df" not in st.session_state:
    st.session_state.processed_claim_df = None
if "claim_missing_outlets" not in st.session_state:
    st.session_state.claim_missing_outlets = []
if "claim_incomplete_messages" not in st.session_state:
    st.session_state.claim_incomplete_messages = []


def inject_custom_css() -> None:
    background_css = ""
    if BACKGROUND_PATH.exists():
        background_css = f"""
        .stApp {{
            background: linear-gradient(rgba(255, 255, 255, 0.92), rgba(255, 255, 255, 0.92)),
                        url('file:///{BACKGROUND_PATH.as_posix()}');
            background-size: cover;
            background-attachment: fixed;
        }}
        """

    st.markdown(
        f"""
        <style>
        {background_css}
        .main-header {{
            padding: 1rem 0 0.5rem 0;
        }}
        .sidebar-logo {{
            text-align: center;
            margin-bottom: 1rem;
        }}
        div[data-testid="stSidebar"] {{
            background-color: rgba(248, 250, 252, 0.95);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


inject_custom_css()

with st.sidebar:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), use_container_width=True)
    st.title("Claim Bensin & Parkir")
    st.caption("Aplikasi perhitungan claim delivery team")
    st.divider()
    st.markdown(
        """
        **Menu Aplikasi**
        - Master Tarif
        - Proses Claim
        - Rekap Claim
        """
    )

st.markdown('<div class="main-header">', unsafe_allow_html=True)
st.title("Claim Bensin & Parkir Delivery")
st.markdown(
    """
    Selamat datang di aplikasi perhitungan claim bensin dan parkir tim delivery.

    Gunakan menu di sidebar kiri untuk:
    1. **Master Tarif** — kelola data outlet, shipper, dan tarif parkir
    2. **Proses Claim** — upload transaksi dan lengkapi shipper/tarif
    3. **Rekap Claim** — ringkasan claim per shipper dan export PDF
    """
)
st.markdown("</div>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.info("Master Tarif\n\nKelola outlet & tarif parkir")
with col2:
    st.info("Proses Claim\n\nUpload & proses transaksi")
with col3:
    st.info("Rekap Claim\n\nRingkasan & export PDF")
