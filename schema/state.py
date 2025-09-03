from pydantic import BaseModel, Field
from typing import Dict, List, Optional

class ArticleState(BaseModel):
    # INPUT PRIMARI
    title: str = Field(default="", description="Titolo dell’articolo")
    abstract: str = Field(default="", description="Abstract sintetico dell’articolo")
    structure: List[str] = Field(default_factory=list, description="Lista ordinata delle sezioni dell’articolo")

    # CONTENUTO GENERATO
    ## TESTO
    current_section_index: int = Field(default=0, description="Indice paragrafo in scrittura")
    paragraphs: Dict[str, str] = Field(default_factory=dict, description="Mappatura sezione → paragrafo")
    section_summaries: Dict[str, str] = Field(default_factory=dict, description="Riassunti per ogni sezione")
    
    ## CODICE
    code_instructions: Dict[str, str] = Field(default_factory=dict, description="Istruzioni generate dal writer per generare codice")
    code_snippets: Dict[str, str] = Field(default_factory=dict, description="Codice prodotto per ciascuna sezione")
    
    ## OUTPUT EDITING
    edited_article: str = Field(default="", description="Versione finale del documento markdown editato")
    supervision_report: str = Field(default="", description="Osservazioni degli agenti supervisori sull’intero articolo")
    
    # METADATA AGGIUNTIVI
    sources: List[str] = Field(default_factory=list, description="Link e riferimenti utilizzati nella ricerca")
    logs: List[str] = Field(default_factory=list, description="Log di sistema/testo grezzo intermedio")
