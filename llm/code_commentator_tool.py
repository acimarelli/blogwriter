import os
from langchain_ollama import ChatOllama
from crewai import LLM


class CodeCommentatorTool:
    """Tool per aggiungere commenti e docstring a uno snippet Python via LLM."""

    def __init__(self, model:str = "ollama/deepseek-coder:33b"):
        # Imposta il modello di default
        self.model = model

        # Inizializza l'LLM
        self.llm = LLM(
            model=self.model,
            base_url="http://localhost:11434",
            temperature=0.2,         # deterministico
            top_p=0.9,
            top_k=20,
            repeat_penalty=1.15,
            num_ctx=8192
        )

    def run(self, prompt: str) -> str:
        return self.llm.call(prompt)