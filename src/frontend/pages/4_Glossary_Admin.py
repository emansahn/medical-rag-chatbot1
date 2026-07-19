"""Authenticated administration interface for the controlled Darija glossary."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import streamlit as st

from src.frontend.components.icons import icon
from src.frontend.components.theme import apply_theme
from src.frontend.components.top_nav import render_top_nav
from src.frontend.services.api_client import ApiError, get_backend_client


STATUSES = {
    "draft": "Brouillon",
    "linguistic_review": "Révision linguistique",
    "medical_review": "Révision médicale",
    "approved": "Approuvé",
    "rejected": "Rejeté",
}
STATUS_BADGE_CLASS = {
    "draft": "neutral",
    "linguistic_review": "info",
    "medical_review": "warn",
    "approved": "ok",
    "rejected": "error",
}


def _login(client) -> None:
    st.markdown(
        f'<h3 style="display:flex;align-items:center;gap:8px;">{icon("lock", 18)}Connexion administrateur</h3>',
        unsafe_allow_html=True,
    )
    st.info(
        "Le premier compte est créé au démarrage du backend avec "
        "`ADMIN_BOOTSTRAP_USERNAME` et `ADMIN_BOOTSTRAP_PASSWORD`."
    )
    with st.form("admin-login"):
        username = st.text_input("Nom d’utilisateur")
        password = st.text_input("Mot de passe", type="password")
        submitted = st.form_submit_button("Se connecter", type="primary")
    if submitted:
        try:
            session = client.admin_login(username, password)
            st.session_state.admin_token = session["access_token"]
            st.session_state.admin_username = session["username"]
            st.rerun()
        except ApiError as exc:
            st.error(exc.message)


def _term_payload(prefix: str, term: dict | None = None) -> dict:
    term = term or {}
    french = st.text_input("Terme français", value=term.get("french", ""), key=f"{prefix}-fr")
    arabic = st.text_input("Darija — arabe", value=term.get("arabic", ""), key=f"{prefix}-ar")
    latin = st.text_input("Darija — latin", value=term.get("latin", ""), key=f"{prefix}-latn")
    aliases = st.text_area(
        "Alias (un par ligne)",
        value="\n".join(term.get("aliases", [])),
        key=f"{prefix}-aliases",
    )
    status = st.selectbox(
        "Statut",
        options=list(STATUSES),
        format_func=lambda value: STATUSES[value],
        index=list(STATUSES).index(term.get("status", "draft")),
        key=f"{prefix}-status",
    )
    notes = st.text_area("Notes de validation", value=term.get("notes", ""), key=f"{prefix}-notes")
    return {
        "french": french.strip(),
        "arabic": arabic.strip(),
        "latin": latin.strip(),
        "aliases": [line.strip() for line in aliases.splitlines() if line.strip()],
        "status": status,
        "notes": notes.strip(),
    }


def _render_management(client, token: str) -> None:
    c1, c2 = st.columns([4, 1])
    c1.success(f"Connecté : {st.session_state.get('admin_username', 'administrateur')}")
    if c2.button("Déconnexion", use_container_width=True):
        try:
            client.admin_logout(token)
        finally:
            st.session_state.pop("admin_token", None)
            st.session_state.pop("admin_username", None)
            st.rerun()

    tab_list, tab_add, tab_audit = st.tabs(["Termes", "Ajouter", "Journal d’audit"])
    with tab_list:
        filter_col, search_col = st.columns(2)
        selected_status = filter_col.selectbox(
            "Filtrer par statut", ["", *STATUSES],
            format_func=lambda value: "Tous" if not value else STATUSES[value],
        )
        search = search_col.text_input("Rechercher")
        terms = client.glossary_terms(token, selected_status, search)
        st.caption(f"{len(terms)} terme(s)")
        if terms:
            st.dataframe(
                [
                    {
                        "ID": term["id"], "Français": term["french"],
                        "Arabe": term["arabic"], "Latin": term["latin"],
                        "Statut": STATUSES[term["status"]],
                    }
                    for term in terms
                ],
                use_container_width=True,
                hide_index=True,
            )
            selected_id = st.selectbox(
                "Modifier un terme",
                [term["id"] for term in terms],
                format_func=lambda term_id: next(
                    term["french"] for term in terms if term["id"] == term_id
                ),
            )
            selected = next(term for term in terms if term["id"] == selected_id)
            badge_class = STATUS_BADGE_CLASS.get(selected["status"], "neutral")
            st.markdown(
                f'<span class="mc-badge {badge_class}">{STATUSES[selected["status"]]}</span>',
                unsafe_allow_html=True,
            )
            with st.form(f"edit-{selected_id}"):
                payload = _term_payload(f"edit-{selected_id}", selected)
                save = st.form_submit_button("Enregistrer les modifications", type="primary")
            if save:
                try:
                    client.update_glossary_term(token, selected_id, payload)
                    st.success("Terme mis à jour.")
                    st.rerun()
                except ApiError as exc:
                    st.error(exc.message)
            with st.expander("Zone dangereuse"):
                if st.button("Supprimer définitivement", key=f"delete-{selected_id}"):
                    client.delete_glossary_term(token, selected_id)
                    st.rerun()

    with tab_add:
        with st.form("create-term"):
            payload = _term_payload("create")
            create = st.form_submit_button("Créer le terme", type="primary")
        if create:
            try:
                client.create_glossary_term(token, payload)
                st.success("Terme créé.")
                st.rerun()
            except ApiError as exc:
                st.error(exc.message)

    with tab_audit:
        logs = client.admin_audit_log(token)
        st.dataframe(
            [
                {
                    "Date": row["created_at"], "Administrateur": row.get("username"),
                    "Action": row["action"], "Entité": row["entity_type"],
                    "ID": row.get("entity_id"),
                }
                for row in logs
            ],
            use_container_width=True,
            hide_index=True,
        )


def main() -> None:
    apply_theme("Administration du glossaire", "🔐")
    render_top_nav("glossaire")
    st.markdown(
        f'<div class="mc-page-header"><div class="mc-eyebrow">{icon("shield", 14)}Administration sécurisée</div>'
        '<h1 class="mc-page-title">Glossaire médical Darija</h1>'
        '<div class="mc-page-lead">Proposez, révisez et approuvez la terminologie utilisée par le RAG.</div></div>',
        unsafe_allow_html=True,
    )
    client = get_backend_client()
    token = st.session_state.get("admin_token")
    if not token:
        _login(client)
        return
    try:
        client.admin_me(token)
        _render_management(client, token)
    except ApiError as exc:
        if exc.status_code == 401:
            st.session_state.pop("admin_token", None)
            st.warning("Session expirée. Reconnectez-vous.")
            _login(client)
        else:
            st.error(exc.message)


if __name__ == "__main__":
    main()
