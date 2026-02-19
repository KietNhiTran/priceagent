"""
Azure OpenAI + Semantic Kernel configuration.

Loads .env, validates Azure credentials, exposes a kernel factory.
Supports API key auth and DefaultAzureCredential (managed identity).
"""

from __future__ import annotations

import os
import logging
from pathlib import Path
from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field

# Load .env from backend/ directory
_env_path = Path(__file__).parent / ".env"
load_dotenv(_env_path, override=True)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Settings model
# ---------------------------------------------------------------------------
class Settings(BaseSettings):
    # Azure OpenAI
    azure_openai_endpoint: str = Field(default="", alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_api_key: str = Field(default="", alias="AZURE_OPENAI_API_KEY")
    azure_openai_chat_deployment: str = Field(default="gpt-4o", alias="AZURE_OPENAI_CHAT_DEPLOYMENT")
    azure_openai_vision_deployment: str = Field(default="gpt-4o", alias="AZURE_OPENAI_VISION_DEPLOYMENT")
    azure_openai_embedding_deployment: str = Field(default="text-embedding-3-large", alias="AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
    azure_openai_api_version: str = Field(default="2024-12-01-preview", alias="AZURE_OPENAI_API_VERSION")
    azure_openai_use_managed_identity: bool = Field(default=False, alias="AZURE_OPENAI_USE_MANAGED_IDENTITY")

    # App
    data_dir: str = Field(default="../data", alias="DATA_DIR")
    trace_db_path: str = Field(default="../data/traces.db", alias="TRACE_DB_PATH")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        populate_by_name = True

    @property
    def has_azure_credentials(self) -> bool:
        """Check if Azure OpenAI credentials are configured."""
        return bool(self.azure_openai_endpoint) and (
            bool(self.azure_openai_api_key) or self.azure_openai_use_managed_identity
        )

    @property
    def resolved_data_dir(self) -> Path:
        """Resolve data dir relative to backend/ directory."""
        p = Path(self.data_dir)
        if not p.is_absolute():
            p = Path(__file__).parent / p
        return p.resolve()

    @property
    def resolved_trace_db_path(self) -> Path:
        """Resolve trace DB path relative to backend/ directory."""
        p = Path(self.trace_db_path)
        if not p.is_absolute():
            p = Path(__file__).parent / p
        return p.resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings()


# ---------------------------------------------------------------------------
# Semantic Kernel factory
# ---------------------------------------------------------------------------
def get_kernel():
    """
    Create a Semantic Kernel instance with Azure OpenAI chat completion.
    Returns (kernel, has_real_ai) tuple.
    """
    from semantic_kernel import Kernel
    from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

    settings = get_settings()
    kernel = Kernel()
    has_real_ai = False

    if settings.has_azure_credentials:
        try:
            if settings.azure_openai_use_managed_identity:
                from azure.identity import DefaultAzureCredential
                credential = DefaultAzureCredential()
                chat_service = AzureChatCompletion(
                    deployment_name=settings.azure_openai_chat_deployment,
                    endpoint=settings.azure_openai_endpoint,
                    ad_token=credential,
                    api_version=settings.azure_openai_api_version,
                )
            else:
                chat_service = AzureChatCompletion(
                    deployment_name=settings.azure_openai_chat_deployment,
                    endpoint=settings.azure_openai_endpoint,
                    api_key=settings.azure_openai_api_key,
                    api_version=settings.azure_openai_api_version,
                )
            kernel.add_service(chat_service)
            has_real_ai = True
            logger.info("Semantic Kernel configured with Azure OpenAI (deployment=%s)", settings.azure_openai_chat_deployment)
        except Exception as e:
            logger.warning("Failed to configure Azure OpenAI: %s. Will use fallback.", e)
    else:
        logger.warning("Azure OpenAI credentials not found. All agents will use fallback responses.")

    return kernel, has_real_ai
