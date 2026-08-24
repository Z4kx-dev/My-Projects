from __future__ import annotations

import platform


def test_stdlib_platform_is_not_shadowed():
    # backend/platform existe como pacote interno; a stdlib deve continuar
    # sendo resolvida para o módulo platform.py do Python.
    assert hasattr(platform, "system")
    assert platform.system()


def test_application_imports():
    from backend.app import app

    assert app is not None
    assert "/api/health" in {rule.rule for rule in app.url_map.iter_rules()}
