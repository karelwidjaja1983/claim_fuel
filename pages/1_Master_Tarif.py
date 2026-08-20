import pandas as pd
import streamlit as st

from utils.db_helper import SHIPPER_OPTIONS, import_master_from_excel, load_master_tarif, save_master_tarif

st.title("Master Tarif")
st.caption("Kelola data outlet, shipper, dan tarif parkir.")

if "master_tarif_editor" not in st.session_state:
    st.session_state.master_tarif_editor = load_master_tarif()

button_col1, button_col2, button_col3, button_col4 = st.columns([1, 1, 1, 2])

with button_col1:
    if st.button("Add New", use_container_width=True):
        new_row = pd.DataFrame(
            [
                {
                    "NO": len(st.session_state.master_tarif_editor) + 1,
                    "Nama Panggilan": "",
                    "Alamat Penagihan": "",
                    "Shipper": "Yasir",
                    "Tarif": 5000,
                }
            ]
        )
        st.session_state.master_tarif_editor = pd.concat(
            [st.session_state.master_tarif_editor, new_row],
            ignore_index=True,
        )
        st.rerun()

with button_col2:
    if st.button("Reload", use_container_width=True):
        st.session_state.master_tarif_editor = load_master_tarif()
        st.rerun()

with button_col3:
    if st.button("Save", type="primary", use_container_width=True):
        try:
            save_master_tarif(st.session_state.master_tarif_editor)
            st.session_state.master_tarif_editor = load_master_tarif()
            st.success("Data Master Tarif berhasil disimpan.")
        except Exception as exc:
            st.error(f"Gagal menyimpan data: {exc}")

with button_col4:
    uploaded_master = st.file_uploader(
        "Upload Master Excel",
        type=["xlsx", "xls"],
        label_visibility="collapsed",
    )

if uploaded_master is not None:
    replace_mode = st.radio(
        "Mode upload master",
        options=["Ganti semua data", "Gabungkan dengan data existing"],
        horizontal=True,
    )
    if st.button("Import Master Excel", use_container_width=True):
        try:
            imported_df = import_master_from_excel(
                uploaded_master,
                replace=replace_mode == "Ganti semua data",
            )
            st.session_state.master_tarif_editor = imported_df
            st.success("File Master Tarif berhasil diimport.")
            st.rerun()
        except Exception as exc:
            st.error(f"Gagal import file: {exc}")

st.divider()

edited_df = st.data_editor(
    st.session_state.master_tarif_editor,
    num_rows="dynamic",
    use_container_width=True,
    hide_index=True,
    column_config={
        "NO": st.column_config.NumberColumn("NO", disabled=True, width="small"),
        "Nama Panggilan": st.column_config.TextColumn("Nama Panggilan", required=True),
        "Alamat Penagihan": st.column_config.TextColumn("Alamat Penagihan", width="large"),
        "Shipper": st.column_config.SelectboxColumn("Shipper", options=SHIPPER_OPTIONS, required=True),
        "Tarif": st.column_config.NumberColumn("Tarif", min_value=0, step=1000, format="%d"),
    },
    key="master_tarif_table",
)

st.session_state.master_tarif_editor = edited_df

delete_col1, delete_col2 = st.columns([1, 4])
with delete_col1:
    if st.button("Delete Selected Rows", use_container_width=True):
        st.info("Hapus baris langsung di tabel dengan tombol minus pada baris, lalu klik Save.")

st.caption(f"Total outlet: {len(st.session_state.master_tarif_editor)}")
