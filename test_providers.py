#!/usr/bin/env python3
"""Quick test of provider structure and imports."""

import asyncio
from src.providers import all_providers, get_provider, PROVIDERS
from src.utils.key_detector import detect_provider


def test_imports():
    """Test that all providers are importable."""
    print("✓ All provider imports successful")


def test_registry():
    """Test the provider registry."""
    providers = all_providers()
    print(f"✓ Providers available: {', '.join(providers)}")
    assert len(providers) == 5, f"Expected 5 providers, got {len(providers)}"


def test_key_detection():
    """Test key prefix detection."""
    test_cases = [
        ("sk-proj-abc123", "openai"),
        ("sk-or-abc123", "openrouter"),
        ("AIzaSyDiT-abc123", "gemini"),
        ("nvapi-abc123", "nvidia_nim"),
        ("sk-abc123", "openai"),  # ambiguous, defaults to openai
    ]
    for key, expected in test_cases:
        detected = detect_provider(key)
        assert detected == expected, f"Key {key} detected as {detected}, expected {expected}"
        print(f"✓ Key detection: {key[:15]}... → {detected}")


def test_provider_interface():
    """Test that all providers have required methods."""
    for provider_name, provider in PROVIDERS.items():
        assert hasattr(provider, "list_models"), f"{provider_name} missing list_models"
        assert hasattr(provider, "test_key"), f"{provider_name} missing test_key"
        assert hasattr(provider, "name"), f"{provider_name} missing name"
        assert hasattr(provider, "key_prefixes"), f"{provider_name} missing key_prefixes"
        print(f"✓ {provider_name}: name='{provider.name}', prefixes={provider.key_prefixes}")


if __name__ == "__main__":
    print("Testing API Keys Testing TUI - Provider Structure\n")
    test_imports()
    test_registry()
    test_key_detection()
    test_provider_interface()
    print("\n✓ All tests passed!")
