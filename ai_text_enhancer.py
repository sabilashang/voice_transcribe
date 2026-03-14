"""
AI Text Enhancer for Voice Transcription
=========================================
Transforms raw, fragmented, and incomprehensible voice-to-text output
into clean, contextually coherent, and well-structured text using AI
language models.

Supported AI Providers:
  - Moonshot     (Kimi K2.5, Kimi K2-Thinking, moonshot-v1-auto, etc.)  ← DEFAULT
  - OpenAI       (GPT-4o, GPT-4, GPT-3.5-turbo)
  - Anthropic    (Claude 3.5 Sonnet, Claude 3 Opus/Haiku)
  - Google       (Gemini 1.5 Pro/Flash)
  - Ollama       (local — Llama 3, Mistral, Phi-3, etc.)

Moonshot / Kimi Models (api.moonshot.ai):
  - kimi-k2.5                  ← recommended, best quality
  - kimi-k2-thinking-turbo     ← fast reasoning
  - kimi-k2-thinking           ← deep reasoning
  - moonshot-v1-auto           ← auto-selects best tier
  - moonshot-v1-128k           ← longest context (128 k tokens)
  - moonshot-v1-32k
  - moonshot-v1-8k             ← fastest / cheapest

Enhancement Modes:
  - clean        → Remove filler words & fix grammar (minimal changes)
  - enhance      → Full improvement: structure, punctuation, coherence
  - formal       → Rewrite in professional/formal tone
  - casual       → Rewrite in friendly, casual tone
  - summarize    → Condense to key points only
  - bullets      → Convert to structured bullet points
  - meeting_notes→ Format as meeting notes with action items
  - technical    → Clean technical documentation style

Usage (Moonshot/Kimi — default):
  enhancer = AITextEnhancer()                        # uses MOONSHOT_API_KEY env var
  result   = enhancer.enhance(raw_text, mode="enhance")
  print(result.enhanced_text)

Usage (explicit):
  enhancer = AITextEnhancer(EnhancerConfig(
      provider="moonshot", model="kimi-k2.5"
  ))
"""

from __future__ import annotations

import os
import json
import time
import logging
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Callable, Generator

# Load .env automatically if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
#  Pre-configured API Keys
#  Priority: environment variable > constant below
# ─────────────────────────────────────────────────────────────────────────────

# Moonshot / Kimi — set here so the module works without a .env file.
# Override at any time by setting the MOONSHOT_API_KEY environment variable.
_MOONSHOT_API_KEY_DEFAULT = "sk-JFagqIalz8zEug95Q0moiAWuOZQjwkgL4Wb7JuleYmznwo7Y"


# ─────────────────────────────────────────────────────────────────────────────
#  Data Classes
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class EnhancementResult:
    """Holds the result of a single AI enhancement call."""
    original_text:  str
    enhanced_text:  str
    mode:           str
    provider:       str
    model:          str
    timestamp:      str = field(default_factory=lambda: datetime.now().isoformat())
    processing_time: float = 0.0
    tokens_used:    int = 0
    word_count_before: int = 0
    word_count_after:  int = 0
    changes_detected:  bool = False
    error:          Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    def summary(self) -> str:
        """Return a one-line human-readable summary of the enhancement."""
        if self.error:
            return f"[ERROR] {self.error}"
        delta = self.word_count_after - self.word_count_before
        sign  = "+" if delta >= 0 else ""
        return (
            f"Mode={self.mode} | Provider={self.provider}/{self.model} | "
            f"Words: {self.word_count_before} → {self.word_count_after} ({sign}{delta}) | "
            f"Time: {self.processing_time:.2f}s"
        )


@dataclass
class EnhancerConfig:
    """Configuration for the AI Text Enhancer."""
    # Provider: "moonshot" | "openai" | "anthropic" | "google" | "ollama"
    provider:    str  = "moonshot"

    # Model names per provider (defaults to Moonshot Kimi K2.5)
    model:       str  = "kimi-k2.5"

    # API keys — read from environment by default
    moonshot_api_key:  Optional[str] = None   # env: MOONSHOT_API_KEY
    openai_api_key:    Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key:    Optional[str] = None

    # Ollama settings
    ollama_host: str  = "http://localhost:11434"
    ollama_model:str  = "llama3"

    # Behaviour
    temperature:     float = 0.3     # Lower = more conservative/faithful
    max_tokens:      int   = 4096    # Max output tokens
    timeout:         int   = 60      # Request timeout in seconds
    retry_attempts:  int   = 3       # Retries on transient errors
    retry_delay:     float = 1.5     # Seconds between retries

    # Context hints passed to the system prompt
    domain_hint:     Optional[str] = None   # e.g. "medical", "legal", "tech"
    speaker_count:   int           = 1      # Number of distinct speakers
    language:        str           = "en"


# ─────────────────────────────────────────────────────────────────────────────
#  Prompt Templates
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_BASE = (
    "You are an expert transcription editor specialising in transforming raw, "
    "imperfect voice-to-text output into polished, coherent written text. "
    "The input was captured from spoken audio and may contain filler words "
    "(um, uh, like), false starts, repeated phrases, mis-heard words, "
    "incomplete sentences, and missing punctuation. "
    "Preserve the speaker's original intent and all factual content."
)

MODE_PROMPTS: dict[str, str] = {
    "clean": (
        "Lightly clean the transcription: remove filler words (um, uh, er, like, "
        "you know), fix obvious spelling mistakes, and add basic punctuation. "
        "Make minimal structural changes — keep the original wording where possible."
    ),
    "enhance": (
        "Fully enhance the transcription: fix grammar, punctuation, sentence "
        "structure, and flow. Merge fragmented sentences. Remove redundant "
        "repetitions. Ensure the text reads as natural, well-written prose "
        "while strictly preserving the original meaning and all facts."
    ),
    "formal": (
        "Rewrite the transcription in a professional, formal tone suitable for "
        "business or academic communication. Fix all grammar and punctuation. "
        "Replace colloquial expressions with formal equivalents. Organise into "
        "clear paragraphs where appropriate."
    ),
    "casual": (
        "Rewrite the transcription in a friendly, natural, conversational tone. "
        "Fix grammar and add punctuation, but keep contractions and casual "
        "phrasing. The result should sound like a polished informal message."
    ),
    "summarize": (
        "Summarise the transcription into a concise paragraph that captures only "
        "the key information, main points, and any decisions or conclusions. "
        "Aim for roughly 20-30% of the original length."
    ),
    "bullets": (
        "Convert the transcription into a clean, structured bullet-point list. "
        "Each bullet should represent one distinct idea, fact, or action item. "
        "Group related points under sub-bullets if necessary."
    ),
    "meeting_notes": (
        "Format the transcription as professional meeting notes. Include sections "
        "for: Discussion Points, Decisions Made, and Action Items (with owners if "
        "mentioned). Use clear headings and bullet points."
    ),
    "technical": (
        "Rewrite the transcription as clear, precise technical documentation. "
        "Use active voice, define acronyms on first use, ensure consistent "
        "terminology, and structure content with numbered steps or sections where "
        "appropriate."
    ),
}


def _build_system_prompt(mode: str, config: EnhancerConfig) -> str:
    """Assemble the final system prompt from base + mode + optional hints."""
    mode_instruction = MODE_PROMPTS.get(mode, MODE_PROMPTS["enhance"])

    hint_parts = []
    if config.domain_hint:
        hint_parts.append(f"Domain context: {config.domain_hint}.")
    if config.speaker_count > 1:
        hint_parts.append(
            f"The audio contains {config.speaker_count} speakers; "
            "differentiate them with 'Speaker 1:', 'Speaker 2:', etc. if evident."
        )
    if config.language != "en":
        hint_parts.append(
            f"The transcription language is '{config.language}'; "
            "output in the same language."
        )

    hints = (" " + " ".join(hint_parts)) if hint_parts else ""
    return f"{SYSTEM_BASE}{hints}\n\n{mode_instruction}"


def _build_user_prompt(raw_text: str) -> str:
    return (
        "Please process the following raw voice transcription according to the "
        "instructions above. Return ONLY the processed text — no preamble, no "
        "explanations, no quotation marks around the output.\n\n"
        f"RAW TRANSCRIPTION:\n{raw_text}"
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Provider Adapters
# ─────────────────────────────────────────────────────────────────────────────

class _MoonshotAdapter:
    """
    Adapter for Moonshot AI (Kimi) — OpenAI-compatible API.

    Base URL : https://api.moonshot.ai/v1
    Docs     : https://platform.moonshot.ai/docs

    Available models:
      kimi-k2.5              — best quality  (default)
      kimi-k2-thinking-turbo — fast reasoning
      kimi-k2-thinking       — deep reasoning
      moonshot-v1-auto       — auto tier selection
      moonshot-v1-128k       — 128 k context window
      moonshot-v1-32k
      moonshot-v1-8k         — fastest / lightest
    """

    MOONSHOT_BASE_URL = "https://api.moonshot.ai/v1"

    def __init__(self, config: EnhancerConfig):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "openai package is not installed. Run: pip install openai"
            )
        api_key = (
            config.moonshot_api_key
            or os.getenv("MOONSHOT_API_KEY")
            or _MOONSHOT_API_KEY_DEFAULT
        )
        if not api_key:
            raise ValueError(
                "Moonshot API key not found. Set the MOONSHOT_API_KEY environment "
                "variable or pass it via EnhancerConfig.moonshot_api_key.\n"
                "Get a free key at: https://platform.moonshot.ai"
            )
        self.client = OpenAI(
            api_key=api_key,
            base_url=self.MOONSHOT_BASE_URL,
            timeout=config.timeout,
        )
        self.config = config

    def complete(self, system: str, user: str) -> tuple[str, int]:
        """Returns (text, tokens_used)."""
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
        text   = response.choices[0].message.content.strip()
        tokens = response.usage.total_tokens if response.usage else 0
        return text, tokens

    def stream(self, system: str, user: str) -> Generator[str, None, None]:
        """Yield text chunks as they arrive."""
        stream = self.client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta


class _OpenAIAdapter:
    """Adapter for OpenAI Chat Completions API."""

    def __init__(self, config: EnhancerConfig):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "openai package is not installed. Run: pip install openai"
            )
        api_key = config.openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OpenAI API key not found. Set the OPENAI_API_KEY environment "
                "variable or pass it via EnhancerConfig.openai_api_key."
            )
        self.client = OpenAI(api_key=api_key, timeout=config.timeout)
        self.config  = config

    def complete(self, system: str, user: str) -> tuple[str, int]:
        """Returns (text, tokens_used)."""
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
        text   = response.choices[0].message.content.strip()
        tokens = response.usage.total_tokens if response.usage else 0
        return text, tokens

    def stream(self, system: str, user: str) -> Generator[str, None, None]:
        """Yield text chunks as they arrive."""
        stream = self.client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta


class _AnthropicAdapter:
    """Adapter for Anthropic Messages API."""

    def __init__(self, config: EnhancerConfig):
        try:
            import anthropic
        except ImportError:
            raise ImportError(
                "anthropic package is not installed. Run: pip install anthropic"
            )
        api_key = config.anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "Anthropic API key not found. Set ANTHROPIC_API_KEY or pass via config."
            )
        self.client = anthropic.Anthropic(api_key=api_key)
        self.config  = config

    def complete(self, system: str, user: str) -> tuple[str, int]:
        response = self.client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
            temperature=self.config.temperature,
        )
        text   = response.content[0].text.strip()
        tokens = (response.usage.input_tokens + response.usage.output_tokens
                  if response.usage else 0)
        return text, tokens

    def stream(self, system: str, user: str) -> Generator[str, None, None]:
        with self.client.messages.stream(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
            temperature=self.config.temperature,
        ) as stream:
            for text in stream.text_stream:
                yield text


class _GoogleAdapter:
    """Adapter for Google Generative AI (Gemini)."""

    def __init__(self, config: EnhancerConfig):
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError(
                "google-generativeai package not installed. "
                "Run: pip install google-generativeai"
            )
        api_key = config.google_api_key or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "Google API key not found. Set GOOGLE_API_KEY or pass via config."
            )
        genai.configure(api_key=api_key)
        gen_cfg = genai.types.GenerationConfig(
            temperature=config.temperature,
            max_output_tokens=config.max_tokens,
        )
        self.model_obj = genai.GenerativeModel(
            model_name=config.model,
            generation_config=gen_cfg,
        )
        self.config = config

    def complete(self, system: str, user: str) -> tuple[str, int]:
        full_prompt = f"{system}\n\n{user}"
        response    = self.model_obj.generate_content(full_prompt)
        text        = response.text.strip()
        tokens      = 0  # Gemini SDK doesn't always expose token counts
        try:
            tokens = response.usage_metadata.total_token_count
        except Exception:
            pass
        return text, tokens

    def stream(self, system: str, user: str) -> Generator[str, None, None]:
        full_prompt = f"{system}\n\n{user}"
        for chunk in self.model_obj.generate_content(full_prompt, stream=True):
            if chunk.text:
                yield chunk.text


class _OllamaAdapter:
    """Adapter for Ollama (local inference server)."""

    def __init__(self, config: EnhancerConfig):
        try:
            import requests
            self._requests = requests
        except ImportError:
            raise ImportError(
                "requests package not installed. Run: pip install requests"
            )
        self.host   = config.ollama_host.rstrip("/")
        self.model  = config.ollama_model
        self.config = config

    def _post(self, payload: dict) -> dict:
        url = f"{self.host}/api/chat"
        r   = self._requests.post(url, json=payload, timeout=self.config.timeout)
        r.raise_for_status()
        return r.json()

    def complete(self, system: str, user: str) -> tuple[str, int]:
        payload = {
            "model":  self.model,
            "stream": False,
            "options": {"temperature": self.config.temperature},
            "messages": [
                {"role": "system",  "content": system},
                {"role": "user",    "content": user},
            ],
        }
        data   = self._post(payload)
        text   = data.get("message", {}).get("content", "").strip()
        tokens = (
            data.get("prompt_eval_count", 0) + data.get("eval_count", 0)
        )
        return text, tokens

    def stream(self, system: str, user: str) -> Generator[str, None, None]:
        url     = f"{self.host}/api/chat"
        payload = {
            "model":  self.model,
            "stream": True,
            "options": {"temperature": self.config.temperature},
            "messages": [
                {"role": "system",  "content": system},
                {"role": "user",    "content": user},
            ],
        }
        with self._requests.post(
            url, json=payload, stream=True, timeout=self.config.timeout
        ) as r:
            r.raise_for_status()
            for line in r.iter_lines():
                if line:
                    try:
                        data  = json.loads(line.decode("utf-8"))
                        delta = data.get("message", {}).get("content", "")
                        if delta:
                            yield delta
                    except json.JSONDecodeError:
                        continue


# ─────────────────────────────────────────────────────────────────────────────
#  Main Enhancer Class
# ─────────────────────────────────────────────────────────────────────────────

VALID_MODES = frozenset(MODE_PROMPTS.keys())

_ADAPTER_MAP = {
    "moonshot":  _MoonshotAdapter,
    "openai":    _OpenAIAdapter,
    "anthropic": _AnthropicAdapter,
    "google":    _GoogleAdapter,
    "ollama":    _OllamaAdapter,
}


class AITextEnhancer:
    """
    Main class for AI-powered voice transcription text enhancement.

    Quick start (Moonshot/Kimi — default):
        enhancer = AITextEnhancer()                          # uses MOONSHOT_API_KEY env var
        result   = enhancer.enhance("um so the the thing is uh we need to uh fix this")
        print(result.enhanced_text)

    Explicit Moonshot model:
        enhancer = AITextEnhancer(
            EnhancerConfig(provider="moonshot", model="kimi-k2-thinking")
        )

    Other providers:
        enhancer = AITextEnhancer(
            EnhancerConfig(provider="openai", model="gpt-4o")
        )
        result = enhancer.enhance(text, mode="formal")
    """

    def __init__(self, config: Optional[EnhancerConfig] = None):
        """
        Args:
            config: EnhancerConfig instance. If None, uses default OpenAI config
                    with model="gpt-4o" and reads OPENAI_API_KEY from environment.
        """
        self.config  = config or EnhancerConfig()
        self._adapter = self._build_adapter()
        self.history: list[EnhancementResult] = []
        logger.info(
            f"AITextEnhancer ready — provider={self.config.provider}, "
            f"model={self.config.model}"
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def enhance(
        self,
        raw_text: str,
        mode:     str = "enhance",
        context:  Optional[str] = None,
    ) -> EnhancementResult:
        """
        Enhance raw voice-transcribed text using the configured AI model.

        Args:
            raw_text: The raw voice-to-text output to be enhanced.
            mode:     Enhancement mode — one of:
                        clean | enhance | formal | casual |
                        summarize | bullets | meeting_notes | technical
            context:  Optional extra context injected into the prompt
                      (e.g. "This is a medical consultation recording").

        Returns:
            EnhancementResult with .enhanced_text and metadata.
        """
        if mode not in VALID_MODES:
            raise ValueError(
                f"Invalid mode '{mode}'. Choose from: {', '.join(sorted(VALID_MODES))}"
            )

        raw_text = raw_text.strip()
        if not raw_text:
            return EnhancementResult(
                original_text="",
                enhanced_text="",
                mode=mode,
                provider=self.config.provider,
                model=self.config.model,
                error="Input text is empty.",
            )

        system = _build_system_prompt(mode, self.config)
        if context:
            system += f"\n\nAdditional context: {context}"

        user = _build_user_prompt(raw_text)

        start = time.perf_counter()
        enhanced, tokens, err = self._call_with_retry(system, user)
        elapsed = time.perf_counter() - start

        result = EnhancementResult(
            original_text      = raw_text,
            enhanced_text      = enhanced,
            mode               = mode,
            provider           = self.config.provider,
            model              = self.config.model,
            processing_time    = round(elapsed, 3),
            tokens_used        = tokens,
            word_count_before  = len(raw_text.split()),
            word_count_after   = len(enhanced.split()) if enhanced else 0,
            changes_detected   = (enhanced != raw_text) if enhanced else False,
            error              = err,
        )
        self.history.append(result)
        logger.info(result.summary())
        return result

    def enhance_stream(
        self,
        raw_text: str,
        mode:     str = "enhance",
        context:  Optional[str] = None,
        on_chunk: Optional[Callable[[str], None]] = None,
    ) -> EnhancementResult:
        """
        Stream the enhanced text token-by-token for real-time display.

        Args:
            raw_text:  Raw transcription text.
            mode:      Enhancement mode.
            context:   Optional extra context.
            on_chunk:  Callback invoked with each text chunk as it arrives.
                       Useful for updating a GUI text widget live.

        Returns:
            EnhancementResult (populated after streaming completes).
        """
        if mode not in VALID_MODES:
            raise ValueError(f"Invalid mode '{mode}'.")

        raw_text = raw_text.strip()
        if not raw_text:
            return EnhancementResult(
                original_text="", enhanced_text="",
                mode=mode, provider=self.config.provider, model=self.config.model,
                error="Input text is empty.",
            )

        system   = _build_system_prompt(mode, self.config)
        if context:
            system += f"\n\nAdditional context: {context}"
        user     = _build_user_prompt(raw_text)

        chunks:  list[str] = []
        start    = time.perf_counter()
        err      = None

        try:
            for chunk in self._adapter.stream(system, user):
                chunks.append(chunk)
                if on_chunk:
                    on_chunk(chunk)
        except Exception as e:
            logger.error(f"Streaming enhancement failed: {e}")
            err = str(e)

        elapsed  = time.perf_counter() - start
        enhanced = "".join(chunks).strip()

        result = EnhancementResult(
            original_text      = raw_text,
            enhanced_text      = enhanced,
            mode               = mode,
            provider           = self.config.provider,
            model              = self.config.model,
            processing_time    = round(elapsed, 3),
            tokens_used        = 0,    # Not available for all streaming providers
            word_count_before  = len(raw_text.split()),
            word_count_after   = len(enhanced.split()) if enhanced else 0,
            changes_detected   = (enhanced != raw_text) if enhanced else False,
            error              = err,
        )
        self.history.append(result)
        logger.info(result.summary())
        return result

    def batch_enhance(
        self,
        texts:    list[str],
        mode:     str = "enhance",
        context:  Optional[str] = None,
        on_progress: Optional[Callable[[int, int], None]] = None,
    ) -> list[EnhancementResult]:
        """
        Enhance multiple transcription texts sequentially.

        Args:
            texts:       List of raw transcription strings.
            mode:        Enhancement mode applied to all texts.
            context:     Optional shared context.
            on_progress: Callback(current_index, total) called after each item.

        Returns:
            List of EnhancementResult objects in the same order as input.
        """
        results = []
        total   = len(texts)
        for i, text in enumerate(texts):
            logger.info(f"Batch enhancing item {i + 1}/{total}...")
            result = self.enhance(text, mode=mode, context=context)
            results.append(result)
            if on_progress:
                on_progress(i + 1, total)
        return results

    def get_history(self) -> list[EnhancementResult]:
        """Return a copy of all enhancement results produced this session."""
        return list(self.history)

    def clear_history(self) -> None:
        """Clear the in-memory enhancement history."""
        self.history.clear()
        logger.info("Enhancement history cleared.")

    def export_history(self, file_path: str, fmt: str = "json") -> None:
        """
        Export enhancement history to file.

        Args:
            file_path: Destination file path.
            fmt:       'json' or 'txt'
        """
        if fmt == "json":
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(
                    [r.to_dict() for r in self.history],
                    f, indent=2, ensure_ascii=False
                )
        elif fmt == "txt":
            with open(file_path, "w", encoding="utf-8") as f:
                for i, r in enumerate(self.history, 1):
                    f.write(f"{'='*60}\n")
                    f.write(f"Enhancement #{i}  [{r.timestamp}]\n")
                    f.write(f"Mode: {r.mode} | {r.provider}/{r.model}\n")
                    f.write(f"{'─'*60}\n")
                    f.write(f"ORIGINAL:\n{r.original_text}\n\n")
                    f.write(f"ENHANCED:\n{r.enhanced_text}\n\n")
        else:
            raise ValueError(f"Unsupported export format: '{fmt}'. Use 'json' or 'txt'.")
        logger.info(f"History exported to {file_path} ({fmt})")

    # ── Utility helpers ───────────────────────────────────────────────────────

    @staticmethod
    def available_modes() -> list[str]:
        """Return a list of all valid enhancement mode names."""
        return sorted(VALID_MODES)

    @staticmethod
    def mode_description(mode: str) -> str:
        """Return the prompt description for a given mode."""
        return MODE_PROMPTS.get(mode, "Unknown mode.")

    def set_domain_hint(self, hint: Optional[str]) -> None:
        """Update the domain hint used in all subsequent prompts."""
        self.config.domain_hint = hint
        logger.info(f"Domain hint set to: {hint!r}")

    def set_speaker_count(self, n: int) -> None:
        """Tell the model how many speakers are in the transcription."""
        self.config.speaker_count = n
        logger.info(f"Speaker count set to: {n}")

    # ── Private helpers ───────────────────────────────────────────────────────

    def _build_adapter(self):
        """Instantiate the correct provider adapter."""
        provider = self.config.provider.lower()
        cls = _ADAPTER_MAP.get(provider)
        if cls is None:
            raise ValueError(
                f"Unknown provider '{provider}'. "
                f"Choose from: {', '.join(_ADAPTER_MAP.keys())}"
            )
        # Apply provider-specific model defaults when the user hasn't overridden
        _provider_defaults = {
            "moonshot":  "kimi-k2.5",
            "openai":    "gpt-4o",
            "anthropic": "claude-3-5-sonnet-20241022",
            "google":    "gemini-1.5-flash",
            "ollama":    self.config.ollama_model,
        }
        if self.config.model in ("kimi-k2.5", "gpt-4o"):
            # Only override if the model is still set to its original default
            # and doesn't match the chosen provider's default
            expected_default = _provider_defaults.get(provider)
            if expected_default and self.config.model != expected_default:
                # model was set for a different provider — use provider default
                self.config.model = expected_default
        if provider == "ollama" and self.config.model == "kimi-k2.5":
            self.config.model = self.config.ollama_model
        return cls(self.config)

    def _call_with_retry(
        self, system: str, user: str
    ) -> tuple[str, int, Optional[str]]:
        """
        Call the adapter's complete() method with exponential-backoff retry.

        Returns:
            (enhanced_text, tokens_used, error_message_or_None)
        """
        last_err: Optional[Exception] = None
        for attempt in range(1, self.config.retry_attempts + 1):
            try:
                text, tokens = self._adapter.complete(system, user)
                return text, tokens, None
            except Exception as e:
                last_err = e
                if attempt < self.config.retry_attempts:
                    wait = self.config.retry_delay * (2 ** (attempt - 1))
                    logger.warning(
                        f"Enhancement attempt {attempt} failed: {e}. "
                        f"Retrying in {wait:.1f}s..."
                    )
                    time.sleep(wait)
                else:
                    logger.error(
                        f"All {self.config.retry_attempts} enhancement attempts failed."
                    )
        return "", 0, str(last_err)


# ─────────────────────────────────────────────────────────────────────────────
#  Factory helpers
# ─────────────────────────────────────────────────────────────────────────────

def create_enhancer(
    provider: str = "openai",
    model:    Optional[str] = None,
    **kwargs,
) -> AITextEnhancer:
    """
    Convenience factory for creating an AITextEnhancer with common providers.

    Args:
        provider: "moonshot" | "openai" | "anthropic" | "google" | "ollama"
        model:    Model name (uses sensible defaults per provider if None).
        **kwargs: Additional keyword arguments forwarded to EnhancerConfig.

    Examples:
        enhancer = create_enhancer()                                         # Moonshot kimi-k2.5
        enhancer = create_enhancer("moonshot", model="kimi-k2-thinking")
        enhancer = create_enhancer("moonshot", model="moonshot-v1-128k")     # long audio
        enhancer = create_enhancer("openai")
        enhancer = create_enhancer("anthropic", model="claude-3-5-sonnet-20241022")
        enhancer = create_enhancer("ollama", ollama_model="mistral")
        enhancer = create_enhancer("google", model="gemini-1.5-flash")
    """
    _defaults = {
        "moonshot":  "kimi-k2.5",
        "openai":    "gpt-4o",
        "anthropic": "claude-3-5-sonnet-20241022",
        "google":    "gemini-1.5-flash",
        "ollama":    kwargs.get("ollama_model", "llama3"),
    }
    resolved_model = model or _defaults.get(provider, "gpt-4o")
    cfg = EnhancerConfig(provider=provider, model=resolved_model, **kwargs)
    return AITextEnhancer(cfg)


# ─────────────────────────────────────────────────────────────────────────────
#  Standalone demo / test
# ─────────────────────────────────────────────────────────────────────────────

SAMPLE_TRANSCRIPTIONS = {
    "meeting": (
        "um so uh we we need to uh finalize the the budget for Q3 by like "
        "Friday I think um John was supposed to um send the spreadsheet but "
        "uh I haven't seen it yet so maybe uh Sarah can you follow up on that "
        "and uh also we need to decide about the the new office space uh "
        "downtown that that one on fifth avenue um it's cheaper than the "
        "current one but uh the commute might be an issue for some people"
    ),
    "technical": (
        "so the the API uh it returns a four oh four when uh when the user ID "
        "doesn't exist in the database and uh we should probably uh add better "
        "error handling there uh the the response body is just an empty JSON "
        "object right now which is uh not very helpful and uh we also need to "
        "um add rate limiting uh to prevent um abuse of the endpoint"
    ),
    "casual": (
        "yeah so I went to the the grocery store yesterday and uh they were "
        "completely out of like avocados which is uh super annoying because I "
        "was gonna make like guacamole for the party and um I had to get like "
        "the pre-made stuff from the deli which you know is not as good but "
        "uh what can you do right"
    ),
}


def _print_demo_result(result: EnhancementResult) -> None:
    """Pretty-print an EnhancementResult to the console."""
    sep = "─" * 70
    print(f"\n{sep}")
    print(f"  Mode     : {result.mode.upper()}")
    print(f"  Provider : {result.provider} / {result.model}")
    print(f"  Time     : {result.processing_time:.2f}s   Tokens: {result.tokens_used}")
    print(f"  Words    : {result.word_count_before} → {result.word_count_after}")
    print(sep)
    print("  ORIGINAL:")
    print(f"  {result.original_text}")
    print(f"\n  ENHANCED:")
    print(f"  {result.enhanced_text}")
    if result.error:
        print(f"\n  ⚠  ERROR: {result.error}")
    print(sep)


def demo(
    provider: str = "openai",
    model:    Optional[str] = None,
    modes:    Optional[list[str]] = None,
    sample:   str = "meeting",
) -> None:
    """
    Run a quick demo of the AITextEnhancer.

    Args:
        provider: AI provider to use.
        model:    Model name (uses provider default if None).
        modes:    List of modes to test (defaults to ["clean", "enhance", "bullets"]).
        sample:   Which sample transcription to use: "meeting" | "technical" | "casual"
    """
    print("\n" + "═" * 70)
    print("  AITextEnhancer — Demo")
    print("═" * 70)

    raw_text  = SAMPLE_TRANSCRIPTIONS.get(sample, SAMPLE_TRANSCRIPTIONS["meeting"])
    test_modes = modes or ["clean", "enhance", "bullets"]

    print(f"\nProvider : {provider}")
    print(f"Sample   : {sample}")
    print(f"Modes    : {', '.join(test_modes)}")

    try:
        enhancer = create_enhancer(provider=provider, model=model)
    except (ImportError, ValueError) as e:
        print(f"\n[ERROR] Could not initialise enhancer: {e}")
        return

    for mode in test_modes:
        result = enhancer.enhance(raw_text, mode=mode)
        _print_demo_result(result)

    # Export results
    out_json = os.path.join(os.path.dirname(__file__), "enhancement_demo_output.json")
    enhancer.export_history(out_json, fmt="json")
    print(f"\nResults exported to: {out_json}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="AI Text Enhancer — standalone demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ai_text_enhancer.py                                              # Moonshot kimi-k2.5
  python ai_text_enhancer.py --provider moonshot --model kimi-k2.5
  python ai_text_enhancer.py --provider moonshot --model kimi-k2-thinking
  python ai_text_enhancer.py --provider moonshot --model moonshot-v1-128k
  python ai_text_enhancer.py --provider openai --model gpt-4o
  python ai_text_enhancer.py --provider anthropic --model claude-3-5-sonnet-20241022
  python ai_text_enhancer.py --provider ollama --model llama3
  python ai_text_enhancer.py --provider google --model gemini-1.5-flash
  python ai_text_enhancer.py --modes enhance formal meeting_notes --sample technical
        """
    )
    parser.add_argument(
        "--provider", default="moonshot",
        choices=list(_ADAPTER_MAP.keys()),
        help="AI provider to use (default: moonshot)"
    )
    parser.add_argument(
        "--model", default=None,
        help="Model name (uses provider default if not specified)"
    )
    parser.add_argument(
        "--modes", nargs="+", default=None,
        choices=list(VALID_MODES),
        help="Enhancement modes to demonstrate (default: clean enhance bullets)"
    )
    parser.add_argument(
        "--sample", default="meeting",
        choices=list(SAMPLE_TRANSCRIPTIONS.keys()),
        help="Which sample transcription to use (default: meeting)"
    )
    parser.add_argument(
        "--list-modes", action="store_true",
        help="Print all available modes and exit"
    )
    args = parser.parse_args()

    if args.list_modes:
        print("\nAvailable enhancement modes:")
        for m in sorted(VALID_MODES):
            print(f"  {m:<15} — {MODE_PROMPTS[m][:80]}...")
    else:
        demo(
            provider=args.provider,
            model=args.model,
            modes=args.modes,
            sample=args.sample,
        )

