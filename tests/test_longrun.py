from backend.platform.runtime import RPGRuntime
from backend.platform.longrun import LongRunSimulator

def test_long_run_stays_consistent(tmp_path):
    runtime=RPGRuntime(str(tmp_path))
    world={'id':'001','nome':'Long Run','tipo':'real','regras':{},'tempo':{},'entidades':[],'populacao':{'total':100,'birth_rate':0.01,'death_rate':0.005},'economia':{'estoques':{'agua':100},'demanda':{'agua':10},'precos_base':{'agua':1}}}
    result=LongRunSimulator(runtime).run(world,240,24)
    assert result['ok'] and result['ciclos']==10
