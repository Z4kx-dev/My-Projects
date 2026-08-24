from backend.core.schema import validate_world


def test_world_schema_accepts_base_world():
    validate_world({
        "id": "001",
        "nome": "Mundo de teste",
        "tipo": "real",
        "versao": 1,
        "tempo": {"ano": 1},
    })
