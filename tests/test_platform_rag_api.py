def test_platform_api_importa_sem_instanciar_dependencia_invalida():
    from backend.platform.api import install
    assert callable(install)
