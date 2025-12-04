from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import Any, Iterable, List, Mapping, MutableMapping, Sequence
from crewai import LLM

logger = logging.getLogger(__name__)

# from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
# from transformers import logging as hf_logging
from crewai.llms.base_llm import BaseLLM

# hf_logging.set_verbosity_error()


@dataclass
class Output:
    """Wrapper minimale compatibile con CrewAI."""
    raw: str

    def __repr__(self) -> str:  # pragma: no cover - metodo di debug
        return f"Output(raw={self.raw!r})"


def _normalize_content(content: Any) -> str:
    """Converte diversi tipi di contenuto in una stringa."""

    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, (list, tuple)):
        return " ".join(_normalize_content(item) for item in content)
    if isinstance(content, Mapping):
        # Alcune librerie (es. LangChain) utilizzano chiavi ``text`` oppure ``content``
        for key in ("text", "content", "value"):
            if key in content:
                return _normalize_content(content[key])
    return str(content)


# class _HuggingFaceLLMAdapter(BaseLLM):
#     """Adattatore ``BaseLLM`` che incapsula una pipeline ``transformers``."""

#     def __init__(
#         self,
#         model_name: str,
#         text_generation_pipeline,
#         # max_new_tokens: int,
#         temperature: float | None = None,
#     ) -> None:
#         super().__init__(model=model_name, temperature=temperature)
#         self._pipeline = text_generation_pipeline

#     def _messages_to_prompt(self, messages: Sequence[Any]) -> str:
#         prompt_lines: List[str] = []
#         for message in messages:
#             role = "user"
#             content = ""
#             if isinstance(message, Mapping):
#                 role = str(message.get("role", role))
#                 content = _normalize_content(message.get("content"))
#             else:
#                 role = str(getattr(message, "role", getattr(message, "type", role)))
#                 content = _normalize_content(getattr(message, "content", message))

#             role = role.upper() if role else "USER"
#             prompt_lines.append(f"{role}: {content}")

#         if prompt_lines and not prompt_lines[-1].startswith("ASSISTANT:"):
#             prompt_lines.append("ASSISTANT:")
        
#         return "\n".join(prompt_lines)

#     def _coerce_prompt(self, messages: Any) -> str:
#         if isinstance(messages, str):
#             return messages
#         if isinstance(messages, Iterable):
#             return self._messages_to_prompt(list(messages))
#         return str(messages)
    
#     def call(
#         self,
#         messages: Any,
#         tools: list[dict[str, Any]] | None = None,
#         callbacks: list[Any] | None = None,
#         available_functions: Mapping[str, Any] | None = None,
#     ) -> str:
#         prompt = self._coerce_prompt(messages)
#         if not prompt:
#             raise ValueError("Prompt vuoto passato al modello Hugging Face.")

#         generations = self._pipeline(
#             prompt,
#             # max_new_tokens=self._max_new_tokens,
#             pad_token_id=self._pipeline.tokenizer.eos_token_id,
#             return_full_text=False,
#         )
#         if not generations:
#             raise RuntimeError("La pipeline Hugging Face non ha prodotto output.")
#         candidate = generations[0]
#         if isinstance(candidate, MutableMapping):
#             text = candidate.get("generated_text") or candidate.get("summary_text")
#             if text is not None:
#                 return text.strip()
#         return _normalize_content(candidate).strip()


class LocalLLMTool:
    """Adapter generico per usare Ollama o Hugging Face con CrewAI."""

    SUPPORTED_BACKENDS = {"ollama", "huggingface"}

    def __init__(
        self,
        model: str,
        backend: str = "ollama",  # "ollama" | "huggingface"
        temperature: float = 0.5,
        top_p: float = 0.95,
        top_k: int = 40,
        repeat_penalty: float = 1.1,
        num_ctx: int = 4096,
        base_url: str = "http://localhost:11434",
        hf_device: int | str | None = None,
        trust_remote_code: bool = False,
    ) -> None:
        self.model = model
        self.backend = backend.lower()
        if self.backend not in self.SUPPORTED_BACKENDS:
            raise ValueError(
                f"Backend non supportato: {backend}. Opzioni valide: {self.SUPPORTED_BACKENDS}."
            )

        if self.backend == "ollama":
            # --- Ollama backend ---
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
        else:
            # # --- Hugging Face backend ---
            # logger.info("Caricamento del modello Hugging Face '%s'...", self.model)

            # tokenizer = AutoTokenizer.from_pretrained(
            #     self.model,
            #     padding_side="left",
            #     trust_remote_code=trust_remote_code,
            # )
            # if tokenizer.pad_token_id is None and tokenizer.eos_token_id is not None:
            #     tokenizer.pad_token = tokenizer.eos_token
            # model_hf = AutoModelForCausalLM.from_pretrained(self.model)

            # model_hf = AutoModelForCausalLM.from_pretrained(
            #     self.model,
            #     trust_remote_code=trust_remote_code,
            # )

            # pipeline_kwargs: dict[str, Any] = {
            #     "temperature": temperature,
            #     "top_p": top_p,
            #     "top_k": top_k,
            #     "repetition_penalty": repeat_penalty,
            #     "return_full_text": False,
            # }
            # if hf_device is not None:
            #     pipeline_kwargs["device"] = hf_device

            # generation_pipeline = pipeline(
            #     "text-generation",
            #     model=model_hf,
            #     tokenizer=tokenizer,
            #     **pipeline_kwargs,
            # )

            # self.llm = _HuggingFaceLLMAdapter(
            #     model_name=self.model,
            #     text_generation_pipeline=generation_pipeline,
            #     temperature=temperature,
            # )
            raise ValueError("SORRY: HF NEED TO BE FIXED!!!")
        
    def run(self, prompt: Any) -> Output:
        """Esegue il modello e restituisce sempre un :class:`Output`."""

        raw_result = self.llm.call(prompt)

        if isinstance(raw_result, Output):
            return raw_result
        if isinstance(raw_result, MutableMapping):
            text = _normalize_content(raw_result.get("output"))
        else:
            text = _normalize_content(raw_result)

        return Output(raw=text)
    
    def __call__(self, prompt: Any) -> Output:
        return self.run(prompt)