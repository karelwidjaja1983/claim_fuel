import pandas as pd
import streamlit as st

from utils.db_helper import SHIPPER_OPTIONS
from utils.processing import parse_transaction_file, process_claim


def _reset_replacement_choice() -> None:
    st.session_state.claim_shipper_replacement_choice = None
    st.session_state.claim_process_run_id = st.session_state.get("claim_process_run_id", 0) + 1


def _format_display_df(processed_df: pd.DataFrame) -> pd.DataFrame:
    display_df = processed_df.copy()
    display_df["Tanggal"] = pd.to_datetime(display_df["Tanggal"], errors="coerce").dt.strftime("%d/%m/%Y")
    return display_df


def _prepare_edited_claim_df(edited_df: pd.DataFrame) -> pd.DataFrame:
    prepared_df = edited_df.copy()
    prepared_df["Tanggal"] = pd.to_datetime(prepared_df["Tanggal"], errors="coerce", dayfirst=True)

    for column in ["Total", "Sisa Tagihan", "Tarif"]:
        prepared_df[column] = pd.to_numeric(prepared_df[column], errors="coerce")

    prepared_df["SHIPPER"] = prepared_df["SHIPPER"].replace("", pd.NA)
    return prepared_df

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
        _reset_replacement_choice()

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

    replacement_choice = st.session_state.get("claim_shipper_replacement_choice")

    if replacement_choice is None:
        st.info("Apakah ada penggantian shipper?")
        choice_col1, choice_col2, _ = st.columns([1, 1, 4])
        with choice_col1:
            if st.button("Ada", type="primary", use_container_width=True):
                st.session_state.claim_shipper_replacement_choice = "Ada"
                st.rerun()
        with choice_col2:
            if st.button("Tidak", use_container_width=True):
                st.session_state.claim_shipper_replacement_choice = "Tidak"
                st.rerun()

    if replacement_choice == "Ada":
        st.info("Silakan ubah kolom SHIPPER untuk outlet yang digantikan sementara.")
        disabled_columns = [column for column in processed_df.columns if column != "SHIPPER"]
        editor_key = f"processed_claim_editor_{st.session_state.get('claim_process_run_id', 0)}"
        edited_df = st.data_editor(
            processed_df,
            num_rows="fixed",
            use_container_width=True,
            hide_index=True,
            disabled=disabled_columns,
            column_config={
                "Tanggal": st.column_config.DateColumn("Tanggal", format="DD/MM/YYYY"),
                "SHIPPER": st.column_config.SelectboxColumn("SHIPPER", options=SHIPPER_OPTIONS, required=True),
                "Tarif": st.column_config.NumberColumn("Tarif", min_value=0, step=1000, format="%d"),
            },
            key=editor_key,
        )
        st.session_state.processed_claim_df = _prepare_edited_claim_df(edited_df)
        st.success("Perubahan SHIPPER tersimpan dan akan dipakai di menu Rekap Claim.")
    else:
        if replacement_choice == "Tidak":
            st.success("Proses claim selesai tanpa penggantian shipper.")
        st.dataframe(_format_display_df(processed_df), use_container_width=True, hide_index=True)

    if st.session_state.get("claim_missing_outlets"):
        st.warning(
            "Masih terdapat outlet yang belum ada di Master Tarif. "
            "Lengkapi Master Tarif lalu proses ulang file transaksi."
        )
else:
    st.info("Belum ada data hasil proses. Upload file transaksi lalu klik Proses Claim.")
