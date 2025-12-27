from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import requests


@dataclass(frozen=True)
class OllamaConfig:
    base_url: str = "http://localhost:11434"
    model: str = "phi3:mini"
    timeout_seconds: int = 60


class OllamaClient:
    def __init__(self, config: OllamaConfig):
        self._config = config

    def generate(self, prompt: str) -> str:
        url = f"{self._config.base_url}/api/generate"
        payload = {
            "model": self._config.model,
            "prompt": prompt,
            "stream": False,
        }
        r = requests.post(url, json=payload, timeout=self._config.timeout_seconds)
        r.raise_for_status()
        data = r.json()
        return data.get("response", "").strip()
