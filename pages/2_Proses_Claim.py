import streamlit as st

from utils.processing import parse_transaction_file, process_claim

st.title("Proses Claim")
st.caption("Upload file transaksi outlet dan lengkapi data Shipper serta Tarif.")

uploaded_file = st.file_uploader(
    "Upload File Transaksi Excel",
    type=["xlsx", "xls"],
    help="File harus memiliki kolom Tanggal, Nomor Transaksi, Nama Panggilan, Status Hari Ini, Total, dan Sisa Tagihan.",
)

if uploaded_file is not None:
    st.success(f"File terpilih: {uploaded_file.name}")

if st.button("Proses Claim", type="primary", disabled=uploaded_file is None):
    try:
        transactions_df = parse_transaction_file(uploaded_file)
        processed_df, missing_outlets, incomplete_messages = process_claim(transactions_df)

        st.session_state.processed_claim_df = processed_df
        st.session_state.claim_missing_outlets = missing_outlets
        st.session_state.claim_incomplete_messages = incomplete_messages

        if missing_outlets:
            for outlet in missing_outlets:
                st.error(
                    f"Outlet '{outlet}' tidak ditemukan di Master Tarif. "
                    "Silakan tambahkan outlet baru di Menu Master Tarif terlebih dahulu agar dapat diproses ulang."
                )

        for message in incomplete_messages:
            st.warning(message)

        if not missing_outlets and not incomplete_messages:
            st.success("Proses claim berhasil. Data siap digunakan di menu Rekap Claim.")

    except Exception as exc:
        st.error(f"Gagal memproses file: {exc}")

st.divider()

if st.session_state.get("processed_claim_df") is not None:
    processed_df = st.session_state.processed_claim_df
    st.subheader("Hasil Proses")
    st.caption(f"Total transaksi: {len(processed_df)}")

    display_df = processed_df.copy()
    display_df["Tanggal"] = display_df["Tanggal"].dt.strftime("%d/%m/%Y")
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    if st.session_state.get("claim_missing_outlets"):
        st.warning(
            "Masih terdapat outlet yang belum ada di Master Tarif. "
            "Lengkapi Master Tarif lalu proses ulang file transaksi."
        )
else:
    st.info("Belum ada data hasil proses. Upload file transaksi lalu klik Proses Claim.")
