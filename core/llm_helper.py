"""
core/llm_helpers_min.py

Ultra‑simple helpers for ONE‑SHOT prompts.
- ask_ollama(prompt, model?)  -> str   # uses `ollama run <model>` CLI
- ask_openai(prompt, api_key?, model?) -> str   # hits OpenAI Chat Completions

No histories, no streaming, minimal error strings you can show in UI.

Quick setup
-----------
1) (optional) `uv pip install python-dotenv` and create a `.env` with:
   OLLAMA_MODEL=mistral:latest
   OPENAI_API_KEY=sk-...
   OPENAI_MODEL=gpt-4o-mini
   OPENAI_BASE_URL=https://api.openai.com/v1
   OPENAI_TEMPERATURE=0.2
   OPENAI_MAX_TOKENS=512
   LLM_TIMEOUT_SEC=60
2) Make sure `ollama` is installed if you use the local path:
   ollama serve
   ollama pull mistral:latest
"""
from __future__ import annotations

import os
import json
import subprocess
import shutil
import urllib.request
import urllib.error
from typing import Optional

# load .env if python-dotenv is present (safe if not installed)
try:  # pragma: no cover
    from dotenv import load_dotenv
    load_dotenv()  # loads .env in working dir if present
except Exception:
    pass

__all__ = ["ask_ollama", "ask_openai", "ask_llm"]


def ask_ollama(prompt: str, model: Optional[str] = None) -> str:
    """Send `prompt` to local Ollama via CLI and return the output text.

    Example:
        ask_ollama("Say hi in one short sentence.")
    """
    if not isinstance(prompt, str) or not prompt.strip():
        return "[ollama] empty prompt"

    model = model or os.getenv("OLLAMA_MODEL", "mistral:latest")
    ollama_bin = shutil.which("ollama") or "ollama"

    try:
        proc = subprocess.run(
            [ollama_bin, "run", model],
            input=prompt,
            text=True,
            encoding="utf-8", 
            errors="replace",      
            capture_output=True,
            check=False,
            timeout=float(os.getenv("LLM_TIMEOUT_SEC", "1200")),
        )

        if proc.returncode != 0:
            err = proc.stderr.strip() or "unknown error"
            return f"[ollama] {proc.returncode} {err}"
        return proc.stdout.strip()
    except FileNotFoundError:
        return "[ollama] binary not found (install Ollama and ensure it's in PATH)"
    except subprocess.TimeoutExpired:
        return "[ollama] timeout"
    except Exception as e:  # keep it blunt/simple
        return f"[ollama] error: {e}"


def ask_openai(prompt: str, api_key: Optional[str] = None, model: Optional[str] = None) -> str:
    import os, json, socket, urllib.parse, urllib.request, urllib.error

    if not isinstance(prompt, str) or not prompt.strip():
        return "[openai] empty prompt"

    api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "[openai] missing OPENAI_API_KEY"

    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.2"))
    max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "512"))
    timeout = float(os.getenv("LLM_TIMEOUT_SEC", "60"))

    # DNS sanity check
    host = urllib.parse.urlparse(base_url).hostname or "api.openai.com"
    try:
        socket.getaddrinfo(host, 443)
    except OSError as se:
        return f"[openai] DNS cannot resolve {host}: {se}"

    # Optionally bypass proxies if env says so (set OPENAI_BYPASS_PROXY=1)
    if os.getenv("OPENAI_BYPASS_PROXY", "0") == "1":
        urllib.request.install_opener(urllib.request.build_opener(
            urllib.request.ProxyHandler({})
        ))

    url = f"{base_url}/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            obj = json.loads(body)
            return obj.get("choices", [{}])[0].get("message", {}).get("content", "")
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode("utf-8")
        except Exception:
            detail = ""
        return f"[openai] {e.code} {detail[:200]}"
    except urllib.error.URLError as e:
        return f"[openai] connection error to {host}: {getattr(e, 'reason', e)}"
    except Exception as e:
        return f"[openai] error: {e}"


# Convenience dispatcher
# Decide which engine to use.
# Prefer the explicit `method` argument; otherwise read LLM_METHOD/LLM_PROVIDER from the environment.

def ask_llm(
    prompt: str,
    method: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> str:
    """Dispatch to Ollama or OpenAI.

    method: 'ollama' or 'openai'. If None, uses LLM_METHOD or LLM_PROVIDER env (default 'ollama').
    """
    m = (method or os.getenv("LLM_METHOD") or os.getenv("LLM_PROVIDER") or "ollama").lower()
    if m == "openai":
        return ask_openai(prompt, api_key=api_key, model=model)
    # default to ollama
    return ask_ollama(prompt, model=model)
