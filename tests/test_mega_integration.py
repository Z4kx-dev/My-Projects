from pathlib import Path
from backend.engine.autonomy import AutonomyEngine
from backend.engine.simulation_systems import ProductionSystem, EconomySystem, DiplomacySystem
from backend.platform.runtime import RPGRuntime
from backend.platform.backup import BackupManager
from backend.platform.validation import WorldAudit

def world():
    return {'id':'999','nome':'Teste','tipo':'fantasia','regras':{},'tempo':{},'entidades':[{'id':'n1','name':'Ana','kind':'npc','world_id':'999','needs':{'fome':10,'sede':10,'sono':0,'estresse':0},'goals':[{'nome':'trabalhar','prioridade':30}],'attributes':{},'alive':True}], 'populacao':{'total':100,'birth_rate':.01,'death_rate':.005},'economia':{'estoques':{'madeira':10},'demanda':{'madeira':3},'precos_base':{'madeira':2}}}

def test_autonomy_prioritizes_thirst():
    d=AutonomyEngine().decide({'id':'1','alive':True,'needs':{'sede':90,'fome':0}})
    assert d.action=='buscar_agua'

def test_production_consumes_inputs():
    stock={'madeira':10}
    r=ProductionSystem().produce(stock,{'insumos':{'madeira':2},'produto':'tora_processada','quantidade':1},2,1)
    assert r['ok'] and stock['madeira']==6 and stock['tora_processada']==2

def test_economy_and_diplomacy():
    e=EconomySystem().tick({'estoques':{'a':1},'demanda':{'a':10},'precos_base':{'a':2}})
    assert e['precos']['a']>2
    d=DiplomacySystem().classify(DiplomacySystem().score(90,1,90))
    assert d=='aliado'

def test_runtime_persists_autonomous_state(tmp_path):
    r=RPGRuntime(str(tmp_path)); w=world(); result=r.simulate(w,2); assert result['entidades_simuladas']==1; assert 'decisao_atual' in w['entidades'][0]['attributes']; assert w['tempo']['horas_decorridas']==2

def test_audit_detects_bad_state():
    w=world(); w['entidades'].append({'id':'n1','world_id':'999'}); assert WorldAudit().validate(w)

def test_backup_creates_manifest(tmp_path):
    root=Path(tmp_path)/'worlds'/'999'; root.mkdir(parents=True); (root/'state.json').write_text('{}',encoding='utf-8')
    b=BackupManager(str(tmp_path)).backup_world('999'); assert Path(b['path'],'manifest.json').exists()
