"""
Fortrinnsrett-app – arbeidsmiljøloven § 14-2 (3)

To visninger, valgt via query-parameter:
  ?side=kandidat  →  Kandidatvisning (åpen for alle)
  (default)       →  HR-portal (passordbeskyttet)
"""

import streamlit as st
from datetime import date, datetime

import database

# ── Sidekonfigurasjon ──────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Konsern – Ledige stillinger",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Konstanter ─────────────────────────────────────────────────────────────────

SELSKAPER = [
    "Brim Explorer AS",
    "Brav AS",
    "Elopak ASA",
    "Ferd Eiendom AS",
    "Interwell AS",
    "Mestergruppen AS",
    "Mintra Holding AS",
    "Norkart AS",
    "Servi Group AS",
    "Simployer Group AS",
    "TRY AS",
]

# ── Initialiser database ───────────────────────────────────────────────────────

database.init_db()

# ── Hjelpefunksjoner ───────────────────────────────────────────────────────────


def get_passwords() -> dict[str, str]:
    """Hent passord fra Streamlit secrets. Fallback til 'test123' lokalt."""
    try:
        return dict(st.secrets["passwords"])
    except Exception:
        return {s: "test123" for s in SELSKAPER}


def verify_password(selskap: str, passord: str) -> bool:
    return get_passwords().get(selskap) == passord


def format_date(date_str: str | None) -> str:
    if not date_str:
        return "Ikke oppgitt"
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%d.%m.%Y")
    except ValueError:
        return date_str


# ── DEL 2: KANDIDATVISNING ─────────────────────────────────────────────────────


def vis_kandidatside():
    st.title("Ledige stillinger i konsernet")

    st.info(
        "Du har fortrinnsrett til ledige stillinger i konsernet i henhold til "
        "**arbeidsmiljøloven § 14-2 (3)**. Ta kontakt med kontaktpersonen for "
        "stillingen du er interessert i."
    )

    stillinger = database.hent_aktive_stillinger()

    # ── Filterpanel ────────────────────────────────────────────────────────────
    col_tittel, col_filter = st.columns([3, 1])
    with col_tittel:
        st.subheader(f"{len(stillinger)} ledig(e) stilling(er) i konsernet")
    with col_filter:
        valgt_selskap = st.selectbox(
            "Filtrer på selskap",
            ["Alle selskaper"] + SELSKAPER,
            label_visibility="collapsed",
        )

    if valgt_selskap != "Alle selskaper":
        stillinger = [s for s in stillinger if s["selskap"] == valgt_selskap]

    if not stillinger:
        st.warning("Ingen ledige stillinger funnet for valgt selskap.")
        return

    # ── Stillingskort ──────────────────────────────────────────────────────────
    for s in stillinger:
        with st.container(border=True):
            col_info, col_meta = st.columns([3, 1])

            with col_info:
                st.markdown(f"### {s['tittel']}")
                st.caption(f"**{s['selskap']}**  ·  {s['arbeidssted'] or 'Ikke oppgitt'}")

            with col_meta:
                brøk = s.get("stillingsbrøk")
                frist = s.get("søknadsfrist")
                st.markdown(
                    f"**Stillingsbrøk:** {int(brøk)} %" if brøk else "**Stillingsbrøk:** –"
                )
                st.markdown(f"**Søknadsfrist:** {format_date(frist)}")

            if s.get("beskrivelse"):
                st.markdown(s["beskrivelse"])

            kontakt_navn = s.get("kontaktperson_navn") or "–"
            kontakt_epost = s.get("kontaktperson_epost") or ""
            if kontakt_epost:
                st.markdown(
                    f"**Kontaktperson:** {kontakt_navn} "
                    f"([{kontakt_epost}](mailto:{kontakt_epost}))"
                )
            else:
                st.markdown(f"**Kontaktperson:** {kontakt_navn}")

    # ── Bunntekst ──────────────────────────────────────────────────────────────
    st.divider()
    st.caption(
        "Er du HR-ansvarlig? Logg inn i [HR-portalen](?side=hr) for å administrere stillinger."
    )


# ── DEL 1: HR-PORTAL ──────────────────────────────────────────────────────────


def vis_innlogging():
    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        st.title("HR-portal")
        st.markdown("Logg inn med ditt selskaps passord for å administrere stillinger.")
        st.divider()

        with st.form("login_form"):
            selskap = st.selectbox("Velg selskap", SELSKAPER)
            passord = st.text_input("Passord", type="password")
            innlogg = st.form_submit_button("Logg inn", use_container_width=True, type="primary")

        if innlogg:
            if verify_password(selskap, passord):
                st.session_state["innlogget"] = True
                st.session_state["selskap"] = selskap
                st.rerun()
            else:
                st.error("Feil passord. Prøv igjen.")

        st.divider()
        st.caption(
            "Vil du se ledige stillinger som kandidat? Gå til "
            "[kandidatvisningen](?side=kandidat)."
        )


def vis_hr_portal():
    selskap = st.session_state["selskap"]

    # ── Topplinje ──────────────────────────────────────────────────────────────
    col_tittel, col_logout = st.columns([5, 1])
    with col_tittel:
        st.title(f"HR-portal – {selskap}")
    with col_logout:
        st.markdown("")  # Litt luft over knappen
        if st.button("Logg ut", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    tab_liste, tab_ny = st.tabs(["Mine stillinger", "Legg ut ny stilling"])

    with tab_liste:
        vis_mine_stillinger(selskap)

    with tab_ny:
        vis_ny_stilling_form(selskap)


def vis_mine_stillinger(selskap: str):
    stillinger = database.hent_stillinger_for_selskap(selskap)
    aktive = [s for s in stillinger if s["status"] == "aktiv"]
    lukkede = [s for s in stillinger if s["status"] != "aktiv"]

    # ── Aktive stillinger ──────────────────────────────────────────────────────
    st.subheader(f"Aktive stillinger ({len(aktive)})")

    if not aktive:
        st.info("Ingen aktive stillinger. Bruk fanen «Legg ut ny stilling» for å publisere.")
    else:
        for s in aktive:
            etikett = (
                f"{s['tittel']} – {s['arbeidssted'] or '–'} "
                f"({int(s['stillingsbrøk'] or 0)} %)"
            )
            with st.expander(etikett):
                vis_stilling_editor(s)

    # ── Lukkede stillinger ─────────────────────────────────────────────────────
    if lukkede:
        st.divider()
        with st.expander(f"Lukkede / fylte stillinger ({len(lukkede)})", expanded=False):
            for s in lukkede:
                st.markdown(f"- ~~{s['tittel']}~~ *(lukket {s.get('opprettet_dato', '')[:10]})*")


def vis_stilling_editor(s: dict):
    """Redigeringsskjema for en eksisterende stilling."""
    with st.form(f"edit_{s['id']}"):
        tittel = st.text_input("Stillingstittel", value=s["tittel"])
        beskrivelse = st.text_area("Beskrivelse", value=s.get("beskrivelse") or "", height=180)

        col1, col2 = st.columns(2)
        with col1:
            arbeidssted = st.text_input("Arbeidssted", value=s.get("arbeidssted") or "")
            brøk = st.number_input(
                "Stillingsbrøk (%)",
                min_value=0,
                max_value=100,
                value=int(s.get("stillingsbrøk") or 100),
            )
        with col2:
            frist_str = s.get("søknadsfrist")
            try:
                frist_default = datetime.strptime(frist_str, "%Y-%m-%d").date() if frist_str else date.today()
            except (ValueError, TypeError):
                frist_default = date.today()
            søknadsfrist = st.date_input("Søknadsfrist", value=frist_default)
            kontakt_navn = st.text_input("Kontaktperson navn", value=s.get("kontaktperson_navn") or "")

        kontakt_epost = st.text_input("Kontaktperson e-post", value=s.get("kontaktperson_epost") or "")

        col_lagre, col_lukk = st.columns(2)
        with col_lagre:
            lagre = st.form_submit_button("Lagre endringer", use_container_width=True, type="primary")
        with col_lukk:
            lukk = st.form_submit_button(
                "Merk som lukket / fylt",
                use_container_width=True,
                type="secondary",
            )

    if lagre:
        database.oppdater_stilling(
            stilling_id=s["id"],
            tittel=tittel,
            beskrivelse=beskrivelse,
            arbeidssted=arbeidssted,
            stillingsbrøk=float(brøk),
            søknadsfrist=str(søknadsfrist),
            kontaktperson_navn=kontakt_navn,
            kontaktperson_epost=kontakt_epost,
        )
        st.success("Endringer lagret!")
        st.rerun()

    if lukk:
        database.lukk_stilling(s["id"])
        st.success("Stilling markert som lukket.")
        st.rerun()


def vis_ny_stilling_form(selskap: str):
    st.subheader("Legg ut ny stilling")

    with st.form("ny_stilling", clear_on_submit=True):
        tittel = st.text_input("Stillingstittel *")
        beskrivelse = st.text_area("Beskrivelse", height=200)

        col1, col2 = st.columns(2)
        with col1:
            arbeidssted = st.text_input("Arbeidssted *")
            brøk = st.number_input(
                "Stillingsbrøk (%)", min_value=0, max_value=100, value=100
            )
        with col2:
            søknadsfrist = st.date_input("Søknadsfrist *", value=date.today())
            kontakt_navn = st.text_input("Kontaktperson navn *")

        kontakt_epost = st.text_input("Kontaktperson e-post *")

        publiser = st.form_submit_button(
            "Publiser stilling", use_container_width=True, type="primary"
        )

    if publiser:
        mangler = []
        if not tittel:
            mangler.append("Stillingstittel")
        if not arbeidssted:
            mangler.append("Arbeidssted")
        if not kontakt_navn:
            mangler.append("Kontaktperson navn")
        if not kontakt_epost:
            mangler.append("Kontaktperson e-post")

        if mangler:
            st.error(f"Fyll ut påkrevde felt: {', '.join(mangler)}")
        else:
            database.legg_til_stilling(
                selskap=selskap,
                tittel=tittel,
                beskrivelse=beskrivelse,
                arbeidssted=arbeidssted,
                stillingsbrøk=float(brøk),
                søknadsfrist=str(søknadsfrist),
                kontaktperson_navn=kontakt_navn,
                kontaktperson_epost=kontakt_epost,
            )
            st.success(f"Stillingen «{tittel}» er publisert!")


# ── ROUTING og MAIN ────────────────────────────────────────────────────────────


def main():
    side = st.query_params.get("side", "hr")

    if side == "kandidat":
        vis_kandidatside()
    else:
        if not st.session_state.get("innlogget"):
            vis_innlogging()
        else:
            vis_hr_portal()


if __name__ == "__main__":
    main()
