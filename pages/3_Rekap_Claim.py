import streamlit as st

from utils.pdf_generator import generate_rekap_pdf
from utils.processing import (
    calculate_rekap,
    format_rekap_display,
    get_available_date_range,
)

st.title("Rekap Claim")
st.caption("Ringkasan claim bensin dan parkir per shipper.")

processed_df = st.session_state.get("processed_claim_df")

if processed_df is None or processed_df.empty:
    st.warning("Belum ada data hasil proses. Silakan proses claim terlebih dahulu di menu Proses Claim.")
    st.stop()

min_date, max_date = get_available_date_range(processed_df)
if min_date is None or max_date is None:
    st.error("Tidak ada tanggal valid pada data transaksi.")
    st.stop()

filter_col1, filter_col2 = st.columns(2)
with filter_col1:
    start_date = st.date_input(
        "Tanggal Awal",
        value=min_date,
        min_value=min_date,
        max_value=max_date,
    )
with filter_col2:
    end_date = st.date_input(
        "Tanggal Akhir",
        value=max_date,
        min_value=min_date,
        max_value=max_date,
    )

if start_date > end_date:
    st.error("Tanggal awal tidak boleh lebih besar dari tanggal akhir.")
    st.stop()

rekap_df = calculate_rekap(processed_df, start_date, end_date)

st.divider()
st.subheader("Tampilan Menu Rekap")
st.caption(f"Periode: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}")

if rekap_df.empty:
    st.info("Tidak ada data pada rentang tanggal yang dipilih.")
else:
    display_df = format_rekap_display(rekap_df)
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    pdf_bytes = generate_rekap_pdf(rekap_df, start_date, end_date)
    st.download_button(
        label="Export to PDF",
        data=pdf_bytes,
        file_name=f"Rekap_Claim_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.pdf",
        mime="application/pdf",
        type="primary",
        use_container_width=False,
    )

    st.caption("Claim Bensin dihitung Rp 30.000 per hari unik per shipper. Claim Parkir dihitung dari total tarif transaksi.")
