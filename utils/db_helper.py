from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "master_tarif.db"
DEFAULT_MASTER_PATH = BASE_DIR / "Master_Tarif.xlsx"

MASTER_COLUMNS = ["NO", "Nama Panggilan", "Alamat Penagihan", "Shipper", "Tarif"]
SHIPPER_OPTIONS = ["Yasir", "Ical", "Saddam"]


def _normalize_shipper(value) -> str | None:
    if pd.isna(value) or str(value).strip() == "":
        return None
    mapping = {
        "yasir": "Yasir",
        "ical": "Ical",
        "saddam": "Saddam",
    }
    return mapping.get(str(value).strip().lower(), str(value).strip())


def _prepare_master_df(df: pd.DataFrame) -> pd.DataFrame:
    prepared = df.copy()
    for column in MASTER_COLUMNS:
        if column not in prepared.columns:
            prepared[column] = None

    prepared = prepared[MASTER_COLUMNS].copy()
    prepared["Nama Panggilan"] = prepared["Nama Panggilan"].astype(str).str.strip()
    prepared["Alamat Penagihan"] = prepared["Alamat Penagihan"].fillna("").astype(str).str.strip()
    prepared["Shipper"] = prepared["Shipper"].apply(_normalize_shipper)
    prepared["Tarif"] = pd.to_numeric(prepared["Tarif"], errors="coerce")
    prepared = prepared[prepared["Nama Panggilan"].ne("") & prepared["Nama Panggilan"].ne("nan")]
    prepared = prepared.drop_duplicates(subset=["Nama Panggilan"], keep="last")
    prepared = prepared.reset_index(drop=True)
    prepared["NO"] = range(1, len(prepared) + 1)
    return prepared


def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _create_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS master_tarif (
            no INTEGER PRIMARY KEY,
            nama_panggilan TEXT NOT NULL UNIQUE,
            alamat_penagihan TEXT,
            shipper TEXT,
            tarif REAL
        )
        """
    )


def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        _create_schema(conn)
        row_count = conn.execute("SELECT COUNT(*) FROM master_tarif").fetchone()[0]
        conn.commit()

    if row_count == 0 and DEFAULT_MASTER_PATH.exists():
        seed_df = pd.read_excel(DEFAULT_MASTER_PATH)
        save_master_tarif(seed_df, skip_init=True)


def load_master_tarif() -> pd.DataFrame:
    init_db()
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT no AS "NO",
                   nama_panggilan AS "Nama Panggilan",
                   alamat_penagihan AS "Alamat Penagihan",
                   shipper AS "Shipper",
                   tarif AS "Tarif"
            FROM master_tarif
            ORDER BY no
            """
        ).fetchall()

    if not rows:
        return pd.DataFrame(columns=MASTER_COLUMNS)

    df = pd.DataFrame([dict(row) for row in rows], columns=MASTER_COLUMNS)
    df["Tarif"] = pd.to_numeric(df["Tarif"], errors="coerce")
    return df


def save_master_tarif(df: pd.DataFrame, skip_init: bool = False) -> None:
    prepared = _prepare_master_df(df)
    if not skip_init:
        init_db()

    with get_connection() as conn:
        _create_schema(conn)
        conn.execute("DELETE FROM master_tarif")
        conn.executemany(
            """
            INSERT INTO master_tarif (no, nama_panggilan, alamat_penagihan, shipper, tarif)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (
                    int(row["NO"]),
                    row["Nama Panggilan"],
                    row["Alamat Penagihan"],
                    row["Shipper"],
                    None if pd.isna(row["Tarif"]) else float(row["Tarif"]),
                )
                for _, row in prepared.iterrows()
            ],
        )
        conn.commit()


def import_master_from_excel(source, replace: bool = True) -> pd.DataFrame:
    if isinstance(source, (str, Path)):
        uploaded_df = pd.read_excel(source)
    else:
        uploaded_df = pd.read_excel(source)

    prepared = _prepare_master_df(uploaded_df)

    if replace:
        save_master_tarif(prepared)
        return load_master_tarif()

    existing = load_master_tarif()
    combined = pd.concat([existing, prepared], ignore_index=True)
    save_master_tarif(combined)
    return load_master_tarif()
