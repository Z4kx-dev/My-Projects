# Plano de implementação — 250 etapas

Cada etapa é independente, objetiva e deve terminar com testes, revisão e documentação do que mudou.

## Fase 01 — Fundação e diagnóstico
1. Congelar a versão funcional atual.
2. Registrar arquitetura existente.
3. Identificar entrypoints.
4. Mapear endpoints.
5. Mapear arquivos JSON.
6. Mapear módulos Guardian.
7. Mapear dependências frontend.
8. Mapear dependências backend.
9. Registrar variáveis de ambiente.
10. Criar `.gitignore` robusto.
11. Remover artefatos gerados do versionamento.
12. Definir Python suportado.
13. Definir navegador suportado.
14. Definir política de compatibilidade.
15. Criar convenções de nomes.
16. Criar convenções de commits.
17. Criar convenções de branches.
18. Criar estrutura de testes.
19. Criar ambiente de desenvolvimento documentado.
20. Criar configuração de lint.
21. Criar configuração de testes.
22. Criar checagem de sintaxe.
23. Criar checagem de JSON.
24. Criar diagnóstico automático.
25. Aprovar baseline.

## Fase 02 — Contratos e schemas
26. Definir schema de mundo.
27. Definir schema de personagem.
28. Definir schema de NPC.
29. Definir schema de local.
30. Definir schema de item.
31. Definir schema de habilidade.
32. Definir schema de atributo.
33. Definir schema de relação.
34. Definir schema de facção.
35. Definir schema de economia.
36. Definir schema de clima.
37. Definir schema de evento.
38. Definir schema de tempo.
39. Definir schema de chat.
40. Definir schema de mensagem.
41. Definir schema de memória.
42. Definir schema de missão.
43. Definir schema de inventário.
44. Definir schema de combate.
45. Definir schema de produção.
46. Definir schema de recurso.
47. Definir schema de configuração.
48. Definir schema de anexos.
49. Definir versionamento dos schemas.
50. Criar validador central.

## Fase 03 — Persistência
51. Criar camada Repository.
52. Isolar acesso ao JSON.
53. Implementar escrita atômica.
54. Implementar locks de arquivo.
55. Implementar recuperação de corrupção.
56. Implementar backups.
57. Implementar snapshots.
58. Implementar migrações.
59. Implementar versionamento de estado.
60. Implementar IDs estáveis.
61. Implementar índice de mundos.
62. Implementar índice de chats.
63. Implementar índice de entidades.
64. Implementar índice de eventos.
65. Implementar histórico append-only.
66. Implementar auditoria.
67. Implementar restauração de snapshot.
68. Implementar exportação JSON.
69. Implementar importação JSON.
70. Testar concorrência.
71. Testar corrupção.
72. Testar reinício.
73. Testar grandes históricos.
74. Medir I/O.
75. Aprovar persistência.

## Fase 04 — Memória
76. Separar memória de chat e memória de mundo.
77. Implementar memória de curto prazo.
78. Implementar memória episódica.
79. Implementar memória semântica.
80. Implementar fatos persistentes.
81. Implementar estado atual.
82. Implementar eventos históricos.
83. Implementar importância de memória.
84. Implementar confiança da memória.
85. Implementar origem da memória.
86. Implementar timestamps.
87. Implementar expiração configurável.
88. Implementar consolidação.
89. Implementar deduplicação.
90. Implementar resolução de conflito.
91. Implementar recuperação lexical.
92. Preparar recuperação vetorial.
93. Implementar ranking de contexto.
94. Implementar orçamento de tokens.
95. Implementar memória de preferências do jogador.
96. Implementar memória de NPC.
97. Separar conhecimento público e privado.
98. Implementar memória por mundo.
99. Implementar memória por chat.
100. Testar continuidade após reinício.

## Fase 05 — Motor de simulação
101. Criar relógio do mundo.
102. Implementar avanço temporal.
103. Implementar duração de ações.
104. Implementar agenda de eventos.
105. Implementar eventos concorrentes.
106. Implementar entidades vivas.
107. Implementar necessidades biológicas.
108. Implementar fadiga.
109. Implementar fome.
110. Implementar sede.
111. Implementar sono.
112. Implementar dor.
113. Implementar saúde.
114. Implementar ferimentos persistentes.
115. Implementar recuperação.
116. Implementar envelhecimento.
117. Implementar morte.
118. Implementar equipamento e desgaste.
119. Implementar clima.
120. Implementar ambiente.
121. Implementar percepção.
122. Implementar informação limitada.
123. Implementar causalidade.
124. Implementar probabilidades.
125. Testar determinismo quando seed for fixa.

## Fase 06 — NPCs e sociedade
126. Criar modelo de personalidade.
127. Criar objetivos individuais.
128. Criar necessidades individuais.
129. Criar memória de NPC.
130. Criar rotina de NPC.
131. Criar relações direcionais.
132. Criar reputação.
133. Criar confiança.
134. Criar medo.
135. Criar lealdade.
136. Criar conflitos.
137. Criar famílias.
138. Criar profissões.
139. Criar instituições.
140. Criar facções.
141. Criar governos.
142. Criar leis.
143. Criar crimes.
144. Criar justiça.
145. Criar religião/cultura quando o mundo permitir.
146. Criar migração.
147. Criar nascimento.
148. Criar morte social e sucessão.
149. Criar propagação de informação.
150. Testar autonomia dos NPCs.

## Fase 07 — Economia e mundo
151. Criar moeda.
152. Criar preços.
153. Criar salários.
154. Criar emprego.
155. Criar oferta e demanda.
156. Criar produção.
157. Criar consumo.
158. Criar estoques.
159. Criar comércio.
160. Criar rotas.
161. Criar impostos.
162. Criar tesouro.
163. Criar despesas.
164. Criar inflação.
165. Criar escassez.
166. Criar agricultura.
167. Criar indústria adequada à época.
168. Criar recursos naturais.
169. Criar infraestrutura.
170. Criar manutenção.
171. Criar população.
172. Criar urbanização.
173. Criar geografia.
174. Criar fronteiras.
175. Testar equilíbrio econômico.

## Fase 08 — IA e orquestração
176. Criar interface abstrata de LLM.
177. Manter Ollama como backend local.
178. Adicionar configuração de modelo.
179. Adicionar temperatura configurável.
180. Adicionar limites de contexto.
181. Criar prompt de sistema modular.
182. Separar regras de simulação do prompt.
183. Criar classificador de intenção.
184. Criar planejador de ferramentas.
185. Criar executor de ferramentas.
186. Criar recuperador de memória.
187. Criar construtor de contexto.
188. Criar gerador de resposta.
189. Criar validador pós-resposta.
190. Criar corretor de continuidade.
191. Criar detector de contradição.
192. Criar detector de informação não fundamentada.
193. Criar política de privacidade do contexto.
194. Criar fallback de modelo.
195. Criar timeout e retry.
196. Criar cancelamento.
197. Criar streaming robusto.
198. Criar telemetria de inferência.
199. Criar medição de tokens.
200. Testar prompts adversariais.

## Fase 09 — Ferramentas RPG
201. Ferramenta de inspeção de estado.
202. Ferramenta de avanço de tempo.
203. Ferramenta de criação de entidade.
204. Ferramenta de atualização de entidade.
205. Ferramenta de consulta de NPC.
206. Ferramenta de consulta de local.
207. Ferramenta de consulta de economia.
208. Ferramenta de inventário.
209. Ferramenta de combate.
210. Ferramenta de testes probabilísticos.
211. Ferramenta de cálculo.
212. Ferramenta de calendário.
213. Ferramenta de clima.
214. Ferramenta de eventos.
215. Ferramenta de missões.
216. Ferramenta de relações.
217. Ferramenta de produção.
218. Ferramenta de comércio.
219. Ferramenta de diário.
220. Ferramenta de snapshot.
221. Ferramenta de rollback administrativo.
222. Ferramenta de importação.
223. Ferramenta de exportação.
224. Permissões por ferramenta.
225. Auditoria de ferramentas.

## Fase 10 — Interface
226. Consolidar layout slim.
227. Melhorar sidebar.
228. Melhorar seletor de mundos.
229. Melhorar seletor de chats.
230. Criar busca global.
231. Criar painel de estado.
232. Criar painel de memória.
233. Criar visualizador JSON.
234. Criar editor de mundo.
235. Criar editor de entidades.
236. Criar painel de eventos.
237. Criar diário.
238. Criar missões.
239. Criar inventário.
240. Criar mapa.
241. Criar painel econômico.
242. Criar configurações completas.
243. Criar atalhos de teclado.
244. Criar responsividade.
245. Criar acessibilidade.
246. Criar estados de carregamento.
247. Criar tratamento de erros.
248. Criar exportação de conversa.
249. Criar limpeza e compactação de histórico.
250. Fazer auditoria final integrada.

## Regra de revisão de cada fase
Ao concluir cada fase: (1) revisar arquitetura; (2) revisar lógica; (3) revisar integração; (4) revisar persistência; (5) revisar segurança e UX; (6) executar testes automatizados; (7) testar caminhos de erro; (8) corrigir regressões; (9) revisar diff; (10) só então liberar a fase seguinte.
