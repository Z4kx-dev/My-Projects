from backend.platform.runtime import RPGRuntime, Entity
from backend.platform.rag import RAGStore
from backend.platform.memory_layers import Memory, MemoryLayers
from backend.platform.ai_guard import Decision, DecisionGuard
from backend.platform.world_systems import Weather, ClimateEngine, Location, GeographyEngine, SocietyEngine, DiplomacyEngine, Faction


def test_runtime_entity_and_time(tmp_path):
    rt = RPGRuntime(str(tmp_path))
    e = rt.register_entity(Entity("npc-1", "Ana", "npc", "001", {"forca": 40}))
    assert e.id == "npc-1"
    world = {"id": "001", "nome": "Teste", "tipo": "real", "regras": {}}
    result = rt.advance(world, 2)
    assert result["tempo"]["horas_decorridas"] == 2


def test_rag_search():
    rag = RAGStore()
    rag.add_source("s1", "Cronica", "Raphael vive em Aster. A cidade possui muralhas e um mercado.")
    result = rag.search("muralhas Aster")
    assert result["results"]


def test_memory_layers():
    m = MemoryLayers()
    m.add(Memory("1", "001", "semantica", "Aster possui muralhas", 0.9))
    assert m.rank("Aster muralhas", "001")


def test_guard_rejects_mutation_without_reason():
    guard = DecisionGuard(lambda name, args: {"ok": True})
    result = guard.execute(Decision("alterar_estado", {}, ""))
    assert result.accepted is False


def test_climate_and_geography():
    weather = ClimateEngine().tick(Weather(), 23, 100)
    assert -100 < weather.temperature_c < 100
    a = Location("a", "A", "cidade", 0, 0)
    b = Location("b", "B", "cidade", 3, 4)
    assert GeographyEngine().distance(a, b) == 5


def test_society_and_diplomacy():
    society = SocietyEngine()
    assert society.update_population(100, 5, 2, 1, 3) == 101
    dip = DiplomacyEngine()
    a = Faction("a", "A", treasury=100)
    b = Faction("b", "B", treasury=100)
    assert 0 <= dip.war_pressure(a, b, 50, 50) <= 100
