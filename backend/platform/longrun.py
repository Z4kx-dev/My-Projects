from __future__ import annotations
from typing import Any
from backend.platform.validation import WorldAudit

class LongRunSimulator:
    def __init__(self, runtime): self.runtime=runtime
    def run(self, world: dict[str,Any], hours: float, step: float=24) -> dict[str,Any]:
        if hours<=0 or step<=0: raise ValueError('hours e step devem ser positivos')
        elapsed=0.0; cycles=0; failures=[]
        while elapsed<hours:
            delta=min(step,hours-elapsed)
            try: self.runtime.simulate(world,delta)
            except Exception as exc: failures.append({'hora':elapsed,'erro':str(exc)}); break
            errors=WorldAudit().validate(world)
            if errors: failures.append({'hora':elapsed,'erros':errors}); break
            elapsed+=delta; cycles+=1
        return {'ok':not failures,'horas_simuladas':elapsed,'ciclos':cycles,'falhas':failures}
