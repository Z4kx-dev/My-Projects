# RPG Simulator — Contrato de Simulação

## Regra-mãe
O sistema deve SIMULAR um mundo vivo, persistente e causal, e não escrever uma história roteirizada. O narrador é imparcial. Não existe plot armor, deus ex machina ou favorecimento do jogador.

## Autoridade
O jogador controla somente o próprio personagem. NPCs, organizações, governos, mercados, clima, natureza e outros agentes continuam agindo independentemente do jogador.

## Tempo
O tempo é irreversível. Toda ação consome tempo. Enquanto o personagem age, o restante do mundo continua. Aprender, treinar, construir, pesquisar, viajar, trabalhar e se recuperar exigem tempo.

## Causalidade
Toda ação possui custo, risco e consequência. Nada é garantido. Resultados dependem de atributos, habilidades, experiência, saúde, estado mental, fadiga, fome, sede, sono, dor, equipamento, terreno, clima, circunstâncias e informação disponível.

## Realismo
Quando a campanha for realista, humanos, animais, ambiente, sociedade, economia, política, tecnologia, química, física e biologia devem obedecer às leis naturais e ao conhecimento da época. Quando houver fantasia, apenas os mecanismos explicitamente existentes no mundo podem contrariar essas leis.

## NPCs
NPCs têm livre-arbítrio, personalidade, memória imperfeita, rotina, necessidades, relações e objetivos. Eles aprendem, esquecem, envelhecem, adoecem, mudam de opinião, trabalham, descansam, cometem erros e podem morrer. NPCs não conhecem automaticamente pensamentos, estatísticas ou ações fora de sua percepção.

## Informação
Separar o estado real do mundo do que cada agente percebe e sabe. O narrador não deve revelar ao jogador informação que o personagem não poderia obter. Rumores podem ser incompletos, falsos ou distorcidos.

## Combate
Não usar níveis ou HP ocultos para decidir resultados. Força, atributos, habilidades, técnica, armas, posição, terreno, clima, fadiga, moral e oportunidade importam. Ferimentos, dor, sangramento, fraturas, infecções e traumas persistem. Morte é possível e permanente.

## Recursos
Recursos são finitos. Dinheiro, comida, água, materiais, munição, energia, tempo, espaço, atenção e capacidade física devem ser rastreáveis. Nada surge do nada.

## Atributos e habilidades
Atributos podem usar escala 0–100 conforme a campanha. Habilidades possuem progresso/maestria. Uso, treino e estudo produzem evolução de forma gradual; desuso pode produzir perda de desempenho. Não conceder progresso arbitrário.

## Estado persistente
Toda alteração relevante deve ser registrada no estado do mundo, memória estruturada ou log de eventos. Histórico, memória, estado e documento-base são camadas diferentes e não devem ser confundidos.

## Separação de responsabilidades
O jogador fornece intenção. O motor de simulação calcula/valida consequências. O narrador/LLM descreve o resultado. O LLM não deve criar ou modificar estado por conveniência narrativa.

## Segurança e consistência
Alterações devem ser validadas antes de serem persistidas. Rejeitar caminhos inseguros, alterações fora do mundo, corrupção de JSON, fatos contraditórios e mudanças sem causa rastreável. Manter backups e logs de eventos importantes.

## Interface
A interface deve iniciar as respostas da simulação com data/hora do mundo e manter, quando aplicável: status, vida, atributos, XP, habilidades, inventário, relações, reputação, economia, diário, quests/missões, eventos, condições e estado do mundo.

## Especificação funcional — 80 sistemas
1. Motor determinístico de simulação.
2. Estado físico completo.
3. Tempo contínuo e consumo de tempo.
4. Calendário persistente.
5. Clima dinâmico.
6. Necessidades humanas.
7. Saúde por sistemas corporais.
8. Ferimentos persistentes.
9. Medicina compatível com a época.
10. Psicologia.
11. Memória humana imperfeita.
12. Percepção e atenção.
13. Informação e conhecimento por agente.
14. NPCs autônomos.
15. Interações NPC-NPC.
16. Economia dinâmica.
17. Cadeias de suprimento.
18. Política dinâmica.
19. Sistema jurídico.
20. Crime e investigação.
21. Reputação por grupo.
22. Relações individuais.
23. Progressão por prática.
24. Equipamentos com desgaste.
25. Inventário físico.
26. Segurança contra alucinação do modelo.
27. Transações de estado auditáveis.
28. Event log imutável.
29. Backups e snapshots.
30. Separação jogador/simulador/narrador.
31. Tomada de decisão dos NPCs.
32. Personalidade contínua.
33. Conflitos internos de objetivos.
34. Estado emocional temporário.
35. Memória emocional.
36. Formação de hábitos.
37. Vieses cognitivos.
38. Capacidade cognitiva limitada.
39. Personalidade evolutiva.
40. Desenvolvimento infantil.
41. Campo visual.
42. Audição espacial.
43. Iluminação realista.
44. Linha de visão.
45. Rumores e transmissão de informação.
46. Confiabilidade e proveniência da informação.
47. Geografia simulada.
48. Hidrologia.
49. Solo e agricultura.
50. Vegetação dinâmica.
51. Fauna dinâmica.
52. Ecossistemas.
53. Incêndios e propagação.
54. Desastres naturais.
55. Erosão e degradação ambiental.
56. Poluição.
57. Integridade estrutural.
58. Manutenção de infraestrutura.
59. Saneamento.
60. Redes de água.
61. Energia.
62. Capacidade de transporte.
63. Congestionamento.
64. Logística.
65. Famílias dinâmicas.
66. Genealogia.
67. Herança.
68. Casamento e vínculos sociais.
69. Estratificação social.
70. Migração.
71. Urbanização.
72. Demografia.
73. Bancos e crédito.
74. Dívidas.
75. Falência.
76. Empresas.
77. Mercado de trabalho.
78. Tributação e orçamento público.
79. Mercados regionais.
80. Arbitragem e adaptação de mercado.

## Regras de interface e continuidade
O mundo deve permanecer consistente entre mensagens. A interface não deve ser confundida com o estado do mundo. IDs são a identidade primária dos mundos e chats. Cada mundo possui memória e histórico próprios. Não misturar dados entre mundos.
