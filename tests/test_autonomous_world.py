from backend.platform.runtime import Entity, RPGRuntime


def test_entity_state_survives_simulation():
    runtime = RPGRuntime("/tmp/rpg-test")
    world = {"id": "001", "nome": "Teste", "tipo": "real", "regras": {}, "entidades": [
        {"id": "npc-1", "name": "Ana", "kind": "npc", "world_id": "001", "needs": {"fome": 0}, "goals": [{"nome": "trabalhar"}], "attributes": {"atividade": "trabalho"}}
    ]}
    result = runtime.simulate(world, 2)
    assert result["entidades_simuladas"] == 1
    assert world["entidades"][0]["needs"]["fome"] > 0
    assert world["entidades"][0]["attributes"]["horas_simuladas"] == 2
    assert world["entidades"][0]["attributes"]["prioridade_atual"] == "trabalhar"


def test_snapshot_has_integrity_hash(tmp_path):
    runtime = RPGRuntime(str(tmp_path))
    snapshot = runtime.snapshots.save("001", {"id": "001", "nome": "X", "tipo": "real"}, "teste")
    assert len(snapshot["sha256"]) == 64
