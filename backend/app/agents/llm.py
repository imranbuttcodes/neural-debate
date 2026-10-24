"""LLM factory using Groq with LangChain."""

import logging
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from pydantic import SecretStr

logger = logging.getLogger(__name__)


def get_llm(model_name: str, streaming: bool = True):
    """Return a ChatGroq instance configured for the specified model."""
    load_dotenv(override=True)
    groq_api_key = os.getenv("GROQ_API_KEY", "").strip()

    if not groq_api_key or groq_api_key.startswith("gsk_xxxx"):
        raise ValueError(
            "GROQ_API_KEY is not set. Please set your valid Groq API key in .env"
        )

    groq_timeout = int(os.getenv("GROQ_TIMEOUT", "30"))

    logger.info("Initializing ChatGroq with model=%s", model_name)

    return ChatGroq(
        model=model_name,
        streaming=streaming,
        api_key=SecretStr(groq_api_key),
        temperature=0.7,
        max_tokens=400,
        timeout=float(groq_timeout),
    )

