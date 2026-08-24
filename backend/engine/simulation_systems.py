from __future__ import annotations
from typing import Any
from math import exp


def clamp(v: float, lo=0.0, hi=100.0): return max(lo, min(hi, float(v)))

class PopulationSystem:
    def tick(self, population: dict[str, Any], years: float) -> dict[str, Any]:
        total=max(0,int(population.get('total',0))); birth=float(population.get('birth_rate',0.012)); death=float(population.get('death_rate',0.009))
        births=max(0,round(total*birth*years)); deaths=max(0,round(total*death*years))
        population['nascimentos']=int(population.get('nascimentos',0))+births; population['mortes']=int(population.get('mortes',0))+deaths
        population['total']=max(0,total+births-deaths); return population

class EconomySystem:
    def tick(self, economy: dict[str, Any], periods: float=1) -> dict[str, Any]:
        economy.setdefault('mercados',{}); economy.setdefault('precos',{}); economy.setdefault('estoques',{})
        for item, stock in list(economy['estoques'].items()):
            demand=float(economy.get('demanda',{}).get(item,1)); base=float(economy.get('precos_base',{}).get(item,1))
            scarcity=demand/max(float(stock),0.1); economy['precos'][item]=round(max(.01,base*(1+.25*min(3,scarcity-1))),2)
        economy['inflacao']=round(float(economy.get('inflacao',0))*0.98 + max(0,float(economy.get('inflacao_alvo',0.02))*periods),4)
        return economy

class ProductionSystem:
    def produce(self, stock: dict[str, Any], recipe: dict[str, Any], workers: int=1, periods: float=1) -> dict[str, Any]:
        workers=max(0,int(workers)); periods=max(0,float(periods)); scale=workers*periods
        for item, qty in (recipe.get('insumos') or {}).items():
            if float(stock.get(item,0)) < float(qty)*scale: return {'ok':False,'motivo':f'insumo insuficiente: {item}'}
        for item, qty in (recipe.get('insumos') or {}).items(): stock[item]=round(float(stock.get(item,0))-float(qty)*scale,4)
        out=recipe.get('produto'); qty=float(recipe.get('quantidade',1))*scale
        if out: stock[out]=round(float(stock.get(out,0))+qty,4)
        return {'ok':True,'produto':out,'quantidade':qty}

class DiplomacySystem:
    def score(self, relation: float, power_ratio: float=1.0, trust: float=50) -> float:
        return clamp(relation*.6 + trust*.25 + clamp(power_ratio*50)*.15)
    def classify(self, score: float) -> str:
        if score>=80:return 'aliado'
        if score>=60:return 'amistoso'
        if score>=40:return 'neutro'
        if score>=20:return 'hostil'
        return 'inimigo'

class ClimateSystem:
    def tick(self, climate: dict[str, Any], hours: float) -> dict[str, Any]:
        climate.setdefault('temperatura_c',20.0); climate.setdefault('umidade',60.0); climate.setdefault('chuva_mm',0.0)
        season=str(climate.get('estacao','normal')).lower(); seasonal={'verao':5,'inverno':-5,'primavera':0,'outono':-1}.get(season,0)
        target=20+seasonal; climate['temperatura_c']=round(climate['temperatura_c']+(target-climate['temperatura_c'])*(1-exp(-hours/24)),2)
        climate['umidade']=clamp(climate['umidade']+(60-climate['umidade'])*0.05)
        return climate

class GovernmentSystem:
    def budget(self, government: dict[str, Any]) -> dict[str, Any]:
        revenue=sum(float(x) for x in (government.get('receitas') or {}).values()); spending=sum(float(x) for x in (government.get('despesas') or {}).values())
        government['receita_total']=round(revenue,2); government['despesa_total']=round(spending,2); government['saldo']=round(revenue-spending,2)
        government['tesouro']=round(float(government.get('tesouro',0))+revenue-spending,2); return government
