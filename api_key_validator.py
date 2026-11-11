#!/usr/bin/env python3
"""
Validador sencillo y portable de API keys para servicios de IA.

No necesita paquetes externos: usa solamente la biblioteca estándar de Python.
Las claves se mantienen en memoria y nunca se guardan ni se muestran completas.
"""

from __future__ import annotations

import argparse
import getpass
import ipaddress
import json
import os
import shutil
import socket
import ssl
import sys
import textwrap
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit, urlunsplit
from urllib.request import Request, urlopen


ANTHROPIC_VERSION = "2023-06-01"
USER_AGENT = "api-key-validator/1.0"


@dataclass(frozen=True)
class Provider:
    name: str
    protocol: str
    base_url: str
    env_var: str
    token_parameter: str = "max_tokens"
    validation_path: str = ""


PROVIDERS: dict[str, Provider] = {
    "openai": Provider(
        "OpenAI",
        "openai",
        "https://api.openai.com",
        "OPENAI_API_KEY",
        "max_completion_tokens",
    ),
    "anthropic": Provider(
        "Anthropic",
        "anthropic",
        "https://api.anthropic.com",
        "ANTHROPIC_API_KEY",
    ),
    "nvidia": Provider(
        "NVIDIA NIM",
        "openai",
        "https://integrate.api.nvidia.com",
        "NVIDIA_API_KEY",
    ),
    "deepseek": Provider(
        "DeepSeek",
        "openai",
        "https://api.deepseek.com",
        "DEEPSEEK_API_KEY",
    ),
    "gemini": Provider(
        "Google Gemini",
        "gemini",
        "https://generativelanguage.googleapis.com",
        "GEMINI_API_KEY",
    ),
    "openrouter": Provider(
        "OpenRouter",
        "openai",
        "https://openrouter.ai/api",
        "OPENROUTER_API_KEY",
        validation_path="/v1/key",
    ),
}

PROTOCOL_NAMES = {
    "openai": "OpenAI-compatible",
    "anthropic": "Anthropic Messages",
    "gemini": "Google Gemini",
}

# Preferencias revisadas contra los catálogos oficiales el 2026-07-29.
# Solo se usan si el propio proveedor devuelve el ID como disponible.
AUTO_MODEL_PREFERENCES = {
    "openai": (
        "gpt-6-luna",
        "gpt-6.1-sol",
        "gpt-5.6-luna",
        "gpt-5.4-nano",
        "gpt-5-nano",
        "gpt-4o-mini",
    ),
    "anthropic": (
        "claude-haiku-4-5-20251001",
        "claude-haiku-4-5",
    ),
    "nvidia": (
        "nvidia/nemotron-3-nano-30b-a3b",
        "nvidia/nemotron-3-nano",
    ),
    "deepseek": ("deepseek-v4-flash", "deepseek-v4-pro"),
    "gemini": (
        "gemini-3.8-flash",
        "gemini-3.7-flash",
        "gemini-3.5-flash-lite",
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-3.1-flash-lite",
    ),
    "openrouter": ("openrouter/free",),
}

NON_TEXT_MODEL_MARKERS = (
    "audio",
    "embed",
    "image",
    "moderation",
    "realtime",
    "search",
    "speech",
    "transcribe",
    "tts",
    "whisper",
)

EXCLUDED_AUTO_MODEL_IDS = {
    "claude-3-5-haiku-latest",
    "claude-3-5-haiku-20241022",
    "claude-3-haiku-20240307",
    "deepseek-chat",
    "deepseek-reasoner",
    "gemini-2.0-flash",
    "gemini-2.0-flash-001",
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash-lite-001",
    "gpt-4.1-nano",
}

EXCLUDED_AUTO_MODEL_PREFIXES = (
    "claude-3-5-haiku",
    "claude-3-haiku",
    "gemini-2.0-flash",
    "gemini-3.1-flash-lite-preview",
    "gpt-4.1-nano",
)


@dataclass
class Result:
    ok: bool
    status: int | None
    data: Any = None
    message: str = ""
    latency_ms: int = 0


def endpoint(base_url: str, path: str) -> str:
    """Une una URL base con una ruta sin duplicar /v1 o /v1beta."""
    base_url = base_url.strip().rstrip("/")
    if not base_url:
        raise ValueError("La base URL no puede estar vacía.")

    parsed = urlsplit(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("La base URL debe comenzar por http:// o https://.")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("No incluyas credenciales en la base URL.")
    if parsed.query or parsed.fragment:
        raise ValueError("La base URL no debe incluir parámetros ni fragmentos.")

    hostname = (parsed.hostname or "").lower()
    try:
        loopback = ipaddress.ip_address(hostname).is_loopback
    except ValueError:
        loopback = hostname == "localhost"
    if parsed.scheme == "http" and not loopback:
        raise ValueError("Usa HTTPS para endpoints remotos; HTTP solo se permite en localhost.")

    base_path = parsed.path.rstrip("/")
    requested = "/" + path.lstrip("/")
    for version in ("/v1beta", "/v1"):
        if base_path.endswith(version) and requested.startswith(version + "/"):
            requested = requested[len(version) :]
            break

    return urlunsplit(
        (parsed.scheme, parsed.netloc, base_path + requested, "", "")
    )


def headers_for(protocol: str, api_key: str) -> dict[str, str]:
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
    }
    if protocol == "anthropic":
        headers["x-api-key"] = api_key
        headers["anthropic-version"] = ANTHROPIC_VERSION
    elif protocol == "gemini":
        headers["x-goog-api-key"] = api_key
    else:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def error_message(payload: Any, fallback: str) -> str:
    if isinstance(payload, dict):
        error = payload.get("error", payload)
        if isinstance(error, dict):
            for key in ("message", "detail", "type"):
                if error.get(key):
                    return str(error[key])
        if isinstance(error, str):
            return error
        if payload.get("message"):
            return str(payload["message"])
    return fallback


def request_json(
    method: str,
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any] | None,
    timeout: float,
) -> Result:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(url, data=body, headers=headers, method=method)
    started = time.perf_counter()

    try:
        with urlopen(request, timeout=timeout, context=ssl.create_default_context()) as response:
            raw = response.read().decode("utf-8", errors="replace")
            data = json.loads(raw) if raw else {}
            return Result(
                True,
                response.status,
                data,
                latency_ms=round((time.perf_counter() - started) * 1000),
            )
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            data = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            data = {}
        return Result(
            False,
            exc.code,
            data,
            error_message(data, exc.reason or "Error HTTP"),
            round((time.perf_counter() - started) * 1000),
        )
    except (URLError, socket.timeout, TimeoutError) as exc:
        reason = getattr(exc, "reason", exc)
        return Result(
            False,
            None,
            message=f"No fue posible conectar: {reason}",
            latency_ms=round((time.perf_counter() - started) * 1000),
        )
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return Result(
            False,
            None,
            message=f"La API respondió, pero no devolvió JSON válido: {exc}",
            latency_ms=round((time.perf_counter() - started) * 1000),
        )


def list_models(
    protocol: str, base_url: str, api_key: str, timeout: float
) -> Result:
    path = "/v1beta/models" if protocol == "gemini" else "/v1/models"
    return request_json(
        "GET", endpoint(base_url, path), headers_for(protocol, api_key), None, timeout
    )


def validate_credentials(
    protocol: str,
    base_url: str,
    api_key: str,
    timeout: float,
    validation_path: str = "",
) -> Result:
    """Valida con un endpoint autenticado; por defecto, usa la lista de modelos."""
    if not validation_path:
        return list_models(protocol, base_url, api_key, timeout)
    return request_json(
        "GET",
        endpoint(base_url, validation_path),
        headers_for(protocol, api_key),
        None,
        timeout,
    )


def model_ids(protocol: str, data: Any) -> list[str]:
    if not isinstance(data, dict):
        return []

    items = data.get("models" if protocol == "gemini" else "data", [])
    if not isinstance(items, list):
        return []

    found: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        model_id = item.get("name" if protocol == "gemini" else "id")
        if isinstance(model_id, str):
            found.append(model_id.removeprefix("models/"))
    return sorted(set(found), key=str.lower)


def inference_payload(
    protocol: str, model: str, token_parameter: str
) -> dict[str, Any]:
    if protocol == "gemini":
        return {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": "Responde solamente con un saludo breve."}],
                }
            ],
            "generationConfig": {"maxOutputTokens": 8},
        }
    if protocol == "anthropic":
        return {
            "model": model,
            "max_tokens": 8,
            "temperature": 0,
            "messages": [
                {"role": "user", "content": "Responde solo con un saludo breve."}
            ],
        }
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Responde solo con un saludo breve."}
        ],
        token_parameter: 8,
    }
    if model.startswith("deepseek-v4-"):
        payload["thinking"] = {"type": "disabled"}
    elif model.startswith(("gpt-5.4-", "gpt-5.6-")):
        payload["reasoning_effort"] = "none"
    elif model.startswith("nvidia/nemotron-3-nano"):
        payload["chat_template_kwargs"] = {"enable_thinking": False}
    return payload


def test_model(
    protocol: str,
    base_url: str,
    api_key: str,
    model: str,
    token_parameter: str,
    timeout: float,
) -> Result:
    if protocol == "gemini":
        safe_model = quote(model.removeprefix("models/"), safe="")
        path = f"/v1beta/models/{safe_model}:generateContent"
    elif protocol == "anthropic":
        path = "/v1/messages"
    else:
        path = "/v1/chat/completions"

    return request_json(
        "POST",
        endpoint(base_url, path),
        headers_for(protocol, api_key),
        inference_payload(protocol, model, token_parameter),
        timeout,
    )


def response_text(protocol: str, data: Any) -> str:
    try:
        if protocol == "gemini":
            return str(data["candidates"][0]["content"]["parts"][0]["text"]).strip()
        if protocol == "anthropic":
            blocks = data.get("content", [])
            return " ".join(
                str(block["text"]).strip()
                for block in blocks
                if isinstance(block, dict) and block.get("type") == "text"
            )
        return str(data["choices"][0]["message"]["content"]).strip()
    except (KeyError, IndexError, TypeError):
        return "(respuesta recibida sin texto reconocible)"


def automatic_model(provider: str, models: list[str]) -> str:
    """Elige un modelo de texto pequeño entre los realmente disponibles."""
    by_lowercase = {model.lower(): model for model in models}
    for preferred in AUTO_MODEL_PREFERENCES.get(provider, ()):
        if preferred in by_lowercase:
            return by_lowercase[preferred]

    candidates = [
        model
        for model in models
        if model.lower() not in EXCLUDED_AUTO_MODEL_IDS
        if not any(
            model.lower().startswith(prefix)
            for prefix in EXCLUDED_AUTO_MODEL_PREFIXES
        )
        if not any(marker in model.lower() for marker in NON_TEXT_MODEL_MARKERS)
    ]
    if not candidates:
        return ""

    def score(model: str) -> tuple[int, str]:
        name = model.lower()
        useful_markers = ("free", "nano", "lite", "mini", "flash", "haiku")
        text_markers = ("chat", "claude", "gemini", "gpt", "instruct", "llama")
        value = sum(10 for marker in useful_markers if marker in name)
        value += sum(3 for marker in text_markers if marker in name)
        return value, name

    return max(candidates, key=score)


def print_summary_columns(
    test: Result | None,
    model: str,
    protocol: str,
    models: list[str],
    limit: int = 20,
) -> None:
    """Muestra el resultado de consumo y los modelos en dos columnas."""
    if test is None:
        left = [
            "Estado: NO PROBADO",
            "No se encontró un modelo de texto apto para la prueba automática.",
        ]
    elif test.ok:
        left = [
            "Estado: DISPONIBLE",
            f"Modelo: {model}",
            f"HTTP: {test.status} ({test.latency_ms} ms)",
            f"Mensaje: {response_text(protocol, test.data)}",
        ]
    else:
        left = [
            "Estado: NO DISPONIBLE",
            f"Modelo: {model}",
            f"HTTP: {test.status or 'sin respuesta'}",
            f"Error: {test.message}",
        ]

    right = [f"Total: {len(models)}"]
    right.extend(f"- {item}" for item in models[:limit])
    if len(models) > limit:
        right.append(f"... y {len(models) - limit} más.")
    if not models:
        right.append("La API no devolvió modelos reconocibles.")

    terminal_width = max(80, min(shutil.get_terminal_size((100, 24)).columns, 140))
    column_width = (terminal_width - 7) // 2

    def wrapped(lines: list[str]) -> list[str]:
        output: list[str] = []
        for line in lines:
            output.extend(textwrap.wrap(line, width=column_width) or [""])
        return output

    left = wrapped(left)
    right = wrapped(right)
    border = f"+-{'-' * column_width}-+-{'-' * column_width}-+"
    print(f"\n{border}")
    print(
        f"| {'PRUEBA DE CONSUMO':<{column_width}} "
        f"| {'MODELOS DISPONIBLES':<{column_width}} |"
    )
    print(border)
    for index in range(max(len(left), len(right))):
        left_line = left[index] if index < len(left) else ""
        right_line = right[index] if index < len(right) else ""
        print(
            f"| {left_line:<{column_width}} "
            f"| {right_line:<{column_width}} |"
        )
    print(border)


def choose(label: str, options: list[tuple[str, str]]) -> str:
    while True:
        print(f"\n{label}")
        for number, (_, description) in enumerate(options, 1):
            print(f"  {number}. {description}")
        answer = input("> ").strip()
        if answer.isdigit() and 1 <= int(answer) <= len(options):
            return options[int(answer) - 1][0]
        print("Elige un número válido.")


def interactive_settings() -> argparse.Namespace | None:
    print("\n=== Validador de API Keys ===")
    print("La clave se escribe de forma oculta y no se guarda.\n")

    choices = [(key, provider.name) for key, provider in PROVIDERS.items()]
    choices.append(("custom", "Personalizada"))
    choices.append(("exit", "Salir"))
    provider_key = choose("Selecciona un proveedor:", choices)
    if provider_key == "exit":
        return None

    if provider_key == "custom":
        protocol = choose(
            "SDK/protocolo compatible:",
            [(key, name) for key, name in PROTOCOL_NAMES.items()],
        )
        base_url = input("Base URL (por ejemplo, http://localhost:8000/v1):\n> ").strip()
        name = "API personalizada"
        env_var = ""
        token_parameter = "max_tokens"
        validation_path = ""
    else:
        provider = PROVIDERS[provider_key]
        protocol = provider.protocol
        base_url = provider.base_url
        name = provider.name
        env_var = provider.env_var
        token_parameter = provider.token_parameter
        validation_path = provider.validation_path

    env_key = os.getenv(env_var, "") if env_var else ""
    if env_key:
        use_env = input(f"Se encontró {env_var}. ¿Usarla? [S/n]: ").strip().lower()
        api_key = env_key if use_env not in {"n", "no"} else getpass.getpass("API key: ")
    else:
        api_key = getpass.getpass("API key: ")

    model = input(
        "Modelo para prueba real (Enter = elegir automáticamente):\n> "
    ).strip()
    return argparse.Namespace(
        provider=provider_key,
        protocol=protocol,
        base_url=base_url,
        api_key=api_key,
        model=model,
        timeout=30.0,
        name=name,
        token_parameter=token_parameter,
        validation_path=validation_path,
    )


def run_interactive() -> int:
    """Mantiene abierto el menú aunque una validación falle."""
    while True:
        settings = interactive_settings()
        if settings is None:
            print("\nHasta luego.")
            return 0

        run(settings)
        input("\nPresiona Enter para volver al menú...")


def settings_from_args(args: argparse.Namespace) -> argparse.Namespace:
    if args.provider == "custom":
        if not args.base_url or not args.protocol:
            raise ValueError(
                "Con --provider custom debes indicar --base-url y --sdk."
            )
        name = "API personalizada"
        env_var = ""
        token_parameter = args.token_parameter
        validation_path = ""
        protocol = args.protocol
        base_url = args.base_url
    else:
        provider = PROVIDERS[args.provider]
        name = provider.name
        env_var = provider.env_var
        token_parameter = provider.token_parameter
        validation_path = provider.validation_path
        protocol = provider.protocol
        base_url = args.base_url or provider.base_url

    api_key = args.api_key or (os.getenv(env_var, "") if env_var else "")
    if not api_key:
        api_key = getpass.getpass("API key: ")

    return argparse.Namespace(
        provider=args.provider,
        protocol=protocol,
        base_url=base_url,
        api_key=api_key.strip(),
        model=(args.model or "").strip(),
        timeout=args.timeout,
        name=name,
        token_parameter=token_parameter,
        validation_path=validation_path,
    )


def run(settings: argparse.Namespace) -> int:
    if not settings.api_key:
        print("ERROR: La API key está vacía.", file=sys.stderr)
        return 2
    if settings.timeout <= 0:
        print("ERROR: El timeout debe ser mayor que cero.", file=sys.stderr)
        return 2
    try:
        endpoint(settings.base_url, "/v1/models")
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(f"\nProveedor: {settings.name}")
    print(f"Protocolo: {PROTOCOL_NAMES[settings.protocol]}")
    print(f"Base URL:  {settings.base_url.rstrip('/')}")
    print("\nValidando credenciales...")

    try:
        validation = validate_credentials(
            settings.protocol,
            settings.base_url,
            settings.api_key,
            settings.timeout,
            settings.validation_path,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if validation.ok:
        print(
            f"VALIDA: la API aceptó la clave "
            f"(HTTP {validation.status}, {validation.latency_ms} ms)."
        )
        if settings.validation_path:
            listing = list_models(
                settings.protocol,
                settings.base_url,
                settings.api_key,
                settings.timeout,
            )
        else:
            listing = validation

        if listing.ok:
            models = model_ids(settings.protocol, listing.data)
        else:
            models = []
            print(f"  No se pudieron listar modelos: {listing.message}")
    else:
        status = validation.status
        if status in {401, 403}:
            print(f"INVALIDA: {validation.message} (HTTP {status}).")
            return 1
        if status in {402, 429}:
            print(
                f"INDETERMINADA: la API respondió HTTP {status}. "
                "La clave pudo ser reconocida, pero hay un problema de cuota, "
                f"crédito o límite: {validation.message}"
            )
            return 3
        print(
            "NO SE PUDO VALIDAR: "
            f"{validation.message}"
            + (f" (HTTP {status})" if status else "")
        )
        return 3

    selected_model = settings.model or automatic_model(settings.provider, models)
    test = None
    if selected_model:
        print(f"\nProbando consumo con el modelo '{selected_model}'...")
        test = test_model(
            settings.protocol,
            settings.base_url,
            settings.api_key,
            selected_model,
            settings.token_parameter,
            settings.timeout,
        )

    print_summary_columns(
        test,
        selected_model,
        settings.protocol,
        models,
    )

    if test is None:
        print(
            "\nNo fue posible confirmar consumo. "
            "Escribe manualmente un modelo de texto e inténtalo de nuevo."
        )
        return 4
    if not test.ok:
        print("\nLa clave fue aceptada, pero no pudo consumir el modelo probado.")
        return 4

    print("\nConsumo confirmado para esta solicitud mínima.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Valida API keys de IA sin dependencias externas.",
        epilog=(
            "Sin argumentos abre el menú interactivo. "
            "Evita --key en equipos compartidos; usa la variable de entorno "
            "del proveedor o deja que el programa la solicite de forma oculta."
        ),
    )
    parser.add_argument(
        "--provider",
        choices=[*PROVIDERS, "custom"],
        help="Proveedor preconfigurado o custom.",
    )
    parser.add_argument(
        "--sdk",
        dest="protocol",
        choices=list(PROTOCOL_NAMES),
        help="SDK/protocolo para custom: openai, anthropic o gemini.",
    )
    parser.add_argument("--base-url", help="Sobrescribe la URL base.")
    parser.add_argument("--model", help="Modelo para una inferencia mínima opcional.")
    parser.add_argument(
        "--key",
        dest="api_key",
        help="API key (menos seguro que variable de entorno o entrada oculta).",
    )
    parser.add_argument(
        "--timeout", type=float, default=30.0, help="Timeout en segundos (30)."
    )
    parser.add_argument(
        "--token-parameter",
        choices=["max_tokens", "max_completion_tokens"],
        default="max_tokens",
        help="Parámetro de límite para un endpoint OpenAI-compatible custom.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.provider is None:
            return run_interactive()
        return run(settings_from_args(args))
    except (KeyboardInterrupt, EOFError):
        print("\nCancelado.")
        return 130
    except ValueError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
