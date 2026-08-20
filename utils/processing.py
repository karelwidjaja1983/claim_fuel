from __future__ import annotations

from datetime import date, datetime

import pandas as pd

from utils.db_helper import load_master_tarif

BENSIN_PER_DAY = 30_000
RESULT_COLUMNS = [
    "Tanggal",
    "Nomor Transaksi",
    "Nama Panggilan",
    "Status Hari Ini",
    "Total",
    "Sisa Tagihan",
    "SHIPPER",
    "Tarif",
]
REKAP_COLUMNS = ["Shipper", "Bensin", "Parkir", "Total", "Jumlah Outlet"]


def _find_header_row(raw_df: pd.DataFrame) -> int | None:
    for idx, row in raw_df.iterrows():
        values = [str(v).strip().lower() for v in row.tolist() if pd.notna(v)]
        if "tanggal" in values and "nama panggilan" in values:
            return idx
    return None


def parse_transaction_file(source) -> pd.DataFrame:
    raw_df = pd.read_excel(source, sheet_name=0, header=None)
    header_row = _find_header_row(raw_df)
    if header_row is None:
        raise ValueError("Format file tidak valid. Kolom Tanggal dan Nama Panggilan tidak ditemukan.")

    df = pd.read_excel(source, sheet_name=0, header=header_row)
    df.columns = [str(col).strip() for col in df.columns]
    df = df.dropna(how="all")

    required_columns = [
        "Tanggal",
        "Nomor Transaksi",
        "Nama Panggilan",
        "Status Hari Ini",
        "Total",
        "Sisa Tagihan",
    ]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Kolom wajib tidak ditemukan: {', '.join(missing_columns)}")

    df["Nama Panggilan"] = df["Nama Panggilan"].astype(str).str.strip()
    df = df[df["Nama Panggilan"].ne("") & df["Nama Panggilan"].ne("nan")]
    df["Tanggal"] = pd.to_datetime(df["Tanggal"], errors="coerce", dayfirst=True)
    return df.reset_index(drop=True)


def _normalize_shipper(value) -> str | None:
    if pd.isna(value) or str(value).strip() == "":
        return None
    mapping = {
        "yasir": "Yasir",
        "ical": "Ical",
        "saddam": "Saddam",
    }
    return mapping.get(str(value).strip().lower())


def process_claim(transactions_df: pd.DataFrame, master_df: pd.DataFrame | None = None) -> tuple[pd.DataFrame, list[str], list[str]]:
    master = master_df if master_df is not None else load_master_tarif()
    lookup = master[["Nama Panggilan", "Shipper", "Tarif"]].copy()
    lookup["Nama Panggilan"] = lookup["Nama Panggilan"].astype(str).str.strip()

    merged = transactions_df.merge(lookup, on="Nama Panggilan", how="left")
    merged["SHIPPER"] = merged["Shipper"].apply(_normalize_shipper)
    merged["Tarif"] = pd.to_numeric(merged["Tarif"], errors="coerce")

    missing_outlets = sorted(
        merged.loc[merged["SHIPPER"].isna(), "Nama Panggilan"].dropna().unique().tolist()
    )

    incomplete_rows = merged[
        merged["SHIPPER"].isna() | merged["Tarif"].isna() | (merged["Tarif"] <= 0)
    ]
    incomplete_messages: list[str] = []
    if not incomplete_rows.empty:
        incomplete_messages.append(
            "Data tidak lengkap. Terdapat data Shipper atau Tarif yang kosong pada hasil proses. "
            "Silakan lengkapi data terlebih dahulu."
        )

    result = merged[
        [
            "Tanggal",
            "Nomor Transaksi",
            "Nama Panggilan",
            "Status Hari Ini",
            "Total",
            "Sisa Tagihan",
            "SHIPPER",
            "Tarif",
        ]
    ].copy()

    return result, missing_outlets, incomplete_messages


def get_available_date_range(processed_df: pd.DataFrame) -> tuple[date | None, date | None]:
    valid_dates = processed_df["Tanggal"].dropna()
    if valid_dates.empty:
        return None, None
    return valid_dates.min().date(), valid_dates.max().date()


def calculate_rekap(
    processed_df: pd.DataFrame,
    start_date: date,
    end_date: date,
) -> pd.DataFrame:
    if processed_df.empty:
        return pd.DataFrame(columns=REKAP_COLUMNS)

    filtered = processed_df.copy()
    filtered = filtered[filtered["Tanggal"].notna()]
    filtered = filtered[
        (filtered["Tanggal"].dt.date >= start_date) & (filtered["Tanggal"].dt.date <= end_date)
    ]
    filtered = filtered[filtered["SHIPPER"].notna()]
    filtered = filtered[filtered["Tarif"].notna()]

    if filtered.empty:
        return pd.DataFrame(columns=REKAP_COLUMNS)

    summaries = []
    for shipper, group in filtered.groupby("SHIPPER"):
        distinct_days = group["Tanggal"].dt.date.nunique()
        bensin = distinct_days * BENSIN_PER_DAY
        parkir = group["Tarif"].sum()
        summaries.append(
            {
                "Shipper": shipper,
                "Bensin": int(bensin),
                "Parkir": int(parkir),
                "Total": int(bensin + parkir),
                "Jumlah Outlet": int(len(group)),
            }
        )

    rekap_df = pd.DataFrame(summaries, columns=REKAP_COLUMNS).sort_values("Shipper").reset_index(drop=True)

    total_row = {
        "Shipper": "TOTAL",
        "Bensin": int(rekap_df["Bensin"].sum()),
        "Parkir": int(rekap_df["Parkir"].sum()),
        "Total": int(rekap_df["Total"].sum()),
        "Jumlah Outlet": int(rekap_df["Jumlah Outlet"].sum()),
    }
    return pd.concat([rekap_df, pd.DataFrame([total_row])], ignore_index=True)


def format_currency(value) -> str:
    if pd.isna(value):
        return "-"
    return f"Rp {int(value):,}".replace(",", ".")


def format_rekap_display(rekap_df: pd.DataFrame) -> pd.DataFrame:
    display_df = rekap_df.copy()
    for column in ["Bensin", "Parkir", "Total"]:
        display_df[column] = display_df[column].apply(format_currency)
    return display_df
