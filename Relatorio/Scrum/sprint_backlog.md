# Sprint Backlog

## Sprint 1 — Login e Cadastro [RF01/RF02]
**Período:** 02/05/2026 — 05/05/2026  
**Status:** ✅ Concluída

### Planejado:
- Diagrama de casos de uso do sistema de login e cadastro
- Diagrama de componentes desse sistema
- Implementação do gateway (porta 5000)
- Criação das páginas HTML e CSS (cadastro, dashboard, login e página inicial)
- Implementação do microsserviço de login (porta 5002)
- Implementação do microsserviço de cadastro (porta 5001)
- Testes unitários

### Entregue:
- ✅ Diagrama de Caso de Uso — `Relatorio/Scrum/Diagrama de Caso de Uso 1.png`
- ✅ Gateway implementado — `Controller/Gateway/gateway.py`
- ✅ Páginas: `pag_inicial.html`, `cadastro.html`, `login.html`, `dashboard.html`, `styles.css`
- ✅ Login — `Controller/Login/login.py`
- ✅ Cadastro — `Controller/Cadastro/cadastro.py`
- ✅ Testes unitários — `tests/test_gateway.py`, `tests/test_login.py`, `tests/test_cadastro.py` (67 testes)

---

## Sprint 2 — Turmas, Aulas e Timer [RF04/RF05/RF07]
**Período:** 05/05/2026 — 18/05/2026  
**Status:** ✅ Pendente

### Planejado:
- Diagrama de sequência do sistema de Turmas e Aulas
- Diagrama de componentes desse sistema (RF07 incluso para facilitar entendimento)
- Implementação das turmas
- Implementação das aulas (sessões)
- Implementação do timer e chamada automática
- Páginas de visualização de turma e aula
- Testes unitários

### Entregue:
- ✅ Diagrama de Sequência — diagrama com fluxos: Criar Turma, Começar Aula, Entrar Turma, Entrar Aula, Encerrar Aula
- ✅ Microsserviço de Turmas e Aulas — `Controller/Turmas e Aulas/turma.py` (porta 5003)
  - `POST /registro_turma` — criar turma
  - `POST /adicionar_aluno_turma` — aluno entrar na turma
  - `GET /listar_turmas` — listar turmas
  - `POST /iniciar_aula` — iniciar sessão com assunto e duração
  - `POST /registrar_presenca_aula` — registrar presença do aluno
  - `POST /terminar_aula` — encerrar aula e gerar frequência
  - `GET /listar_aulas`, `GET /listar_aulas_turma` — listar aulas
  - `GET /listar_frequencias`, `GET /listar_frequencias_aula` — consultar frequências
  - `GET /buscar_usuario` — buscar nome de usuário por email
- ✅ Microsserviço de Timer — `Controller/Timer/timer.py` (porta 5004)
  - `POST /timer/iniciar` — Iniciar_Timer
  - `POST /timer/registrar_presenca` — Registrar_Frequencia
  - `POST /timer/encerrar` — Encerrar_Timer
  - `GET /timer/status` — consultar estado do timer
  - Persistência em `database/timer.json`
- ✅ Páginas:
  - `Views/turma.html` — detalhes da turma, listagem de aulas, iniciar nova aula (professor), entrar na aula (aluno)
  - `Views/aula.html` — página da aula com: nome do professor, assunto, timer regressivo, registrar presença, encerrar aula, exibir frequência
- ✅ Frequência no Dashboard do professor — `dashboard.html` (#frequencia) exibe frequências por aula ordenadas por data
- ✅ Gateway atualizado com proxies para todos os novos endpoints
- ✅ Banco de dados JSON: `database/classes.json`, `database/aula.json`, `database/frequences.json`, `database/timer.json`

---

## Sprint 3 — Sistema de Notas [RF03/RF06] (Pendente)
**Período:** Não iniciada  
**Status:** 🔲 Pendente

### Planejado:
- Implementar publicação de notas pelo professor
- Implementar visualização de notas pelo aluno
- Páginas e APIs necessárias
- Testes unitários
