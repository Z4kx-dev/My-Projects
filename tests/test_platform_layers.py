from backend.engine.combat import Combatant, estimate_advantage
from backend.engine.needs import Needs
from backend.engine.scheduler import Scheduler
from backend.memory.embeddings import cosine_similarity, lexical_vector
from backend.platform.invariants import clamp, require_probability


def test_invariants():
    assert clamp(150, 0, 100) == 100
    assert require_probability(.5) == .5


def test_needs_advance_and_sleep():
    n = Needs()
    n.advance(60)
    assert n.fome > 0 and n.sede > 0
    n.sleep(60)
    assert n.sono == 0


def test_scheduler_due():
    s = Scheduler()
    s.schedule(10, "a")
    assert s.due(9) == []
    assert len(s.due(10)) == 1


def test_similarity():
    assert cosine_similarity(lexical_vector("espada longa"), lexical_vector("espada longa")) == 1


def test_combat_has_no_hidden_hp():
    a = Combatant("a", forca=70)
    b = Combatant("b", resistencia=30)
    assert estimate_advantage(a, b) > 0
