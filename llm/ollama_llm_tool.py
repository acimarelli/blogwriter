import os
from langchain_ollama import ChatOllama
from langchain_community.llms import Ollama
from langchain_core.messages import HumanMessage
from crewai import LLM
from typing import List, Dict, Any

class OllamaLLMTool:
    def __init__(
        self,
        model: str,
        temperature: float = 0.5,
        top_p: float = 0.95,
        top_k: int = 40,
        repeat_penalty: float = 1.1,
        num_ctx: int = 4096,
        base_url: str = "http://localhost:11434",
    ):
        """Initialize an Ollama-backed LLM.

        Parameters
        ----------
        model : str
            Identifier of the model to use.
        temperature : float, optional
            Sampling temperature in the range ``0.0``‑``1.0``. Lower values make
            outputs more deterministic, while higher values increase creativity
            at the cost of potential incoherence. Defaults to ``0.5``.
        top_p : float, optional
            Nucleus sampling threshold between ``0.0`` and ``1.0``. The model
            considers only the most probable tokens with cumulative probability
            ``top_p``. Smaller values narrow the distribution; ``1.0`` disables
            the filter. Defaults to ``0.95``.
        top_k : int, optional
            Limits sampling to the ``top_k`` highest‑probability tokens. A value
            of ``0`` disables the restriction. Higher values can increase
            diversity but may introduce more randomness. Defaults to ``40``.
        repeat_penalty : float, optional
            Penalizes the model for repeating tokens. Values typically range
            from ``1.0`` (no penalty) upward; larger penalties reduce
            repetition but may also discard useful tokens. Defaults to ``1.1``.
        num_ctx : int, optional
            Maximum number of tokens the model may consider in its context
            window. Larger windows allow longer prompts but require more
            memory. Typical values range from a few thousand up to the model's
            limit. Defaults to ``4096``.
        base_url : str, optional
            URL of the Ollama server hosting the model. Change this if your
            server runs on a different host or port. Defaults to
            ``"http://localhost:11434"``.
        """

        self.model = model
        self.llm = LLM(
            model=self.model,
            base_url=base_url,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            repeat_penalty=repeat_penalty,
            num_ctx=num_ctx,
            stream=False,
        )

    def run(self, prompt: str) -> str:
        return self.llm.call(prompt)
