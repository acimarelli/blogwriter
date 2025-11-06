import re
import os


class MarkdownUtils:
    @staticmethod
    def inject_code(paragraph: str, section: str, code_snippets: dict) -> str:
        """
        Sostituisce i blocchi [CODICE_RICHIESTO][START] ... [END]
        con il codice corrispondente alla sezione, wrappato in Markdown.

        Args:
            paragraph (str): testo del paragrafo che può contenere placeholder.
            section (str): nome della sezione (chiave in code_snippets).
            code_snippets (dict): dizionario {section_name: code_string}.

        Returns:
            str: paragrafo aggiornato con codice iniettato.
        """
        code_to_insert = code_snippets.get(section, "").strip()
        if not code_to_insert:
            # Se non c’è codice per la sezione, rimuovo i placeholder
            return re.sub(r"\[CODICE_RICHIESTO\]\[START\].*?\[END\]", "", paragraph, flags=re.DOTALL).strip()

        def _replace_block(_):
            return f"\n{code_to_insert}\n"

        updated_paragraph = re.sub(
            r"\[CODICE_RICHIESTO\]\[START\].*?\[END\]",
            _replace_block,
            paragraph,
            flags=re.DOTALL
        )
        return updated_paragraph.strip()

    @staticmethod
    def generate_markdown(
        title: str,
        abstract: str,
        structure: list,
        paragraphs: dict,
        code_snippets: dict,
        write_output: bool = False,
        output_path: str | None = None
    ) -> str:
        """
        Genera un file markdown ben formattato con eventuali snippet di codice iniettati.

        Args:
            title (str): Titolo dell'articolo.
            abstract (str): Abstract del contenuto.
            structure (list): Lista ordinata delle sezioni.
            paragraphs (dict): Dizionario {section: testo}.
            code_snippets (dict): Dizionario {section: codice}.
            output_path (str, opzionale): percorso di output per il file .md (default: <title>.md).

        Returns:
            str: Contenuto Markdown completo.
        """
        md_lines = []

        # Titolo principale
        md_lines.append(f"# {title}\n")

        # Abstract
        md_lines.append("## Abstract\n")
        md_lines.append(abstract.strip() + "\n")

        # Corpo dell’articolo
        for section in structure:
            md_lines.append(f"## {section}\n")

            paragraph_text = paragraphs.get(section, "").strip()
            processed_text = MarkdownUtils.inject_code(paragraph_text, section, code_snippets)

            md_lines.append(processed_text + "\n")

        # Concatenazione
        md_text = "\n".join(md_lines)

        if write_output:   
            # Gestione nome file
            filename = os.path.join(output_path, f"{title.lower().replace(' ', '_').replace('/', '-')}.md") if output_path is not None else f"{title.lower().replace(' ', '_').replace('/', '-')}.md"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(md_text)

        return md_text