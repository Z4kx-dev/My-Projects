import platform


def test_stdlib_platform_is_not_shadowed():
    assert hasattr(platform, "system")
    assert platform.system()


def test_application_routes_are_registered():
    from backend.app import app

    paths = {rule.rule for rule in app.url_map.iter_rules()}
    assert "/api/health" in paths
    assert "/api/chat" in paths
    assert "/api/agent" in paths
    assert "/api/v2/status" in paths
