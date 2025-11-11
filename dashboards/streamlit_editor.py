from __future__ import annotations

from pathlib import Path
from typing import List

import streamlit as st

# Directory containing the markdown files to edit.
MARKDOWN_DIR = Path("notebooks/outputs")
MARKDOWN_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(page_title="Markdown Editor", layout="wide")
st.title("📝 Markdown Editor")

st.sidebar.header("Impostazioni")
st.sidebar.write("I file markdown vengono letti e salvati nella cartella:")
st.sidebar.code(str(MARKDOWN_DIR.resolve()))


def get_markdown_files(directory: Path) -> List[str]:
    """Return the available markdown files sorted alphabetically."""
    return sorted(f.name for f in directory.glob("*.md"))


markdown_files = get_markdown_files(MARKDOWN_DIR)

if "current_file" not in st.session_state:
    st.session_state["current_file"] = None

if "editor_content" not in st.session_state:
    st.session_state["editor_content"] = ""


if not markdown_files:
    st.info(
        "Nessun file markdown trovato. Aggiungi file nella cartella specificata per iniziare."
    )
else:
    try:
        default_index = (
            markdown_files.index(st.session_state["current_file"])
            if st.session_state["current_file"] in markdown_files
            else 0
        )
    except ValueError:
        default_index = 0

    selected_file = st.selectbox(
        "Seleziona il file markdown da modificare",
        markdown_files,
        index=default_index,
    )

    if selected_file != st.session_state.get("current_file"):
        st.session_state["current_file"] = selected_file
        file_path = MARKDOWN_DIR / selected_file
        try:
            st.session_state["editor_content"] = file_path.read_text(encoding="utf-8")
        except OSError as exc:
            st.session_state["editor_content"] = ""
            st.error(f"Impossibile leggere il file '{file_path.name}': {exc}")


if st.session_state.get("current_file"):
    st.text_area(
        "Contenuto del file",
        height=600,
        key="editor_content",
    )

    file_path = MARKDOWN_DIR / st.session_state["current_file"]

    col_save, col_download = st.columns(2)

    with col_save:
        if st.button("💾 Salva", use_container_width=True):
            try:
                file_path.write_text(st.session_state["editor_content"], encoding="utf-8")
            except OSError as exc:
                st.error(f"Errore durante il salvataggio di '{file_path.name}': {exc}")
            else:
                st.success(f"File '{file_path.name}' salvato correttamente.")

    with col_download:
        st.download_button(
            label="⬇️ Download",
            data=st.session_state["editor_content"].encode("utf-8"),
            file_name=file_path.name,
            mime="text/markdown",
            use_container_width=True,
        )
else:
    st.warning("Seleziona un file markdown per iniziare a modificarlo.")
