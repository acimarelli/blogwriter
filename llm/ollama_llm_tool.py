import os
from langchain_ollama import ChatOllama
from langchain_community.llms import Ollama
from langchain_core.messages import HumanMessage
from crewai import LLM
from typing import List, Dict, Any

class OllamaLLMTool:
    def __init__(self, model: str):
        self.model = model
        self.llm = LLM(
            model=self.model,
            base_url="http://localhost:11434",
            # custom_llm_provider="ollama",
            temperature=0.5,
            top_p=0.95,
            top_k=40,
            repeat_penalty=1.1, 
            stream=False)

    def run(self, prompt: str) -> str:
        return self.llm.call(prompt)
    
