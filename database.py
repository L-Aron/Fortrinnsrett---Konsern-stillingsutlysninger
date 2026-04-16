import sqlite3
from datetime import datetime

DB_PATH = "stillinger.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Opprett databasetabell hvis den ikke finnes."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS stillinger (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                selskap             TEXT    NOT NULL,
                tittel              TEXT    NOT NULL,
                beskrivelse         TEXT,
                arbeidssted         TEXT,
                stillingsbrøk       REAL,
                søknadsfrist        TEXT,
                kontaktperson_navn  TEXT,
                kontaktperson_epost TEXT,
                status              TEXT    NOT NULL DEFAULT 'aktiv',
                opprettet_dato      TEXT    NOT NULL
            )
        """)
        conn.commit()


def hent_aktive_stillinger() -> list[dict]:
    """Hent alle aktive stillinger på tvers av selskaper."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM stillinger WHERE status = 'aktiv' ORDER BY opprettet_dato DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def hent_stillinger_for_selskap(selskap: str) -> list[dict]:
    """Hent alle stillinger (aktive og lukkede) for ett selskap."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM stillinger WHERE selskap = ? ORDER BY opprettet_dato DESC",
            (selskap,),
        ).fetchall()
    return [dict(r) for r in rows]


def legg_til_stilling(
    selskap: str,
    tittel: str,
    beskrivelse: str,
    arbeidssted: str,
    stillingsbrøk: float,
    søknadsfrist: str,
    kontaktperson_navn: str,
    kontaktperson_epost: str,
) -> int:
    """Legg til en ny stilling og returner ID."""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO stillinger
                (selskap, tittel, beskrivelse, arbeidssted, stillingsbrøk,
                 søknadsfrist, kontaktperson_navn, kontaktperson_epost,
                 status, opprettet_dato)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'aktiv', ?)
            """,
            (
                selskap,
                tittel,
                beskrivelse,
                arbeidssted,
                stillingsbrøk,
                søknadsfrist,
                kontaktperson_navn,
                kontaktperson_epost,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
        conn.commit()
        return cursor.lastrowid


def oppdater_stilling(
    stilling_id: int,
    tittel: str,
    beskrivelse: str,
    arbeidssted: str,
    stillingsbrøk: float,
    søknadsfrist: str,
    kontaktperson_navn: str,
    kontaktperson_epost: str,
):
    """Oppdater feltene på en eksisterende stilling."""
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE stillinger
            SET tittel              = ?,
                beskrivelse         = ?,
                arbeidssted         = ?,
                stillingsbrøk       = ?,
                søknadsfrist        = ?,
                kontaktperson_navn  = ?,
                kontaktperson_epost = ?
            WHERE id = ?
            """,
            (
                tittel,
                beskrivelse,
                arbeidssted,
                stillingsbrøk,
                søknadsfrist,
                kontaktperson_navn,
                kontaktperson_epost,
                stilling_id,
            ),
        )
        conn.commit()


def lukk_stilling(stilling_id: int):
    """Marker en stilling som lukket/fylt."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE stillinger SET status = 'lukket' WHERE id = ?",
            (stilling_id,),
        )
        conn.commit()
