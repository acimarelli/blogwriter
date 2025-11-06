from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

class ArticleState(BaseModel):
    # INPUT PRIMARI
    title: str = Field(default="", description="Titolo dell’articolo")

    # CONTENUTO GENERATO
    ## TESTO
    abstract: str = Field(default="", description="Abstract sintetico dell’articolo")
    structure: List[str] = Field(default_factory=list, description="Lista ordinata delle sezioni dell’articolo")
    
    current_section_index: int = Field(default=0, description="Indice paragrafo in scrittura")
    paragraphs: Dict[str, str] = Field(default_factory=dict, description="Mappatura sezione → paragrafo")
    section_summaries: Dict[str, str] = Field(default_factory=dict, description="Riassunti per ogni sezione")
    
    ## CODICE
    code_instructions: Dict[str, str] = Field(default_factory=dict, description="Istruzioni generate dal writer per generare codice")
    code_snippets: Dict[str, str] = Field(default_factory=dict, description="Codice prodotto per ciascuna sezione")
    
    ## OUTPUT EDITING
    original_article: str = Field(default="", description="Versione originale del documento markdown")
    edited_article: str = Field(default="", description="Versione finale del documento markdown editato")
    supervision_report: Dict[str, str] = Field(default_factory=dict, description="Osservazioni degli agenti supervisori sull’intero articolo")
    final_revision_report: dict = Field(default_factory=dict, description="Revisione definitiva ottenuta dall'analisi svolta dai diversi supervisori")

    # METADATA AGGIUNTIVI
    log_summary: Dict[str, Any] = Field(default_factory=dict, description="Metriche sintetiche dei log")
