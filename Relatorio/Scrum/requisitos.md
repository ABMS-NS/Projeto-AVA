# Documento de requisitos do AVA (sofre alterações conforme o projeto avança)

## Requisitos Funcionais

- ✅ **RF01:** O sistema deve permitir que um aluno ou professor façam login. O aluno pode se autocadastrar, enquanto o professor precisa pedir o cadastro ao responsável pelo ambiente. *(Implementado — cadastro.py, login.py, gateway)*

- ✅ **RF02:** O sistema deve permitir que o aluno se cadastre e entre com sua senha sempre que quiser *(Implementado — cadastro.py, login.py)*

- 🔲 **RF03:** O sistema deve permitir que o professor publique notas e o aluno veja as mesmas *(Pendente — única funcionalidade não implementada)*

- ✅ **RF04:** O sistema deve permitir que o professor abra turmas e os alunos possam se cadastrar nelas *(Implementado — turma.py, gateway)*

- ✅ **RF05:** O sistema deve permitir a criação de sessões (ou aulas) dentro de cada turma, onde em cada aula os alunos tenham acesso aos materiais e instruções postas pelo professor em tempo real *(Implementado — criação de aulas, página da aula com assunto, timer e presença)*

- 🔲 **RF06:** O aluno deve ser capaz de visualizar suas notas em um ambiente apropriado *(Pendente — junto com RF03)*

- ✅ **RF07:** As sessões de aula devem conter um timer que, ao acabar o tempo, deve encerrar a aula e fazer a chamada *(Parcialmente Implementado — timer.py, contagem regressiva, registro de presença e frequência)*

## Requisitos Não Funcionais

- ✅ **RNF01**: O sistema deve contar com uma interface responsiva e rápida *(Implementado — CSS com media queries)*

- ✅ **RNF02:** O tempo de resposta para carregamento de páginas não deve exceder 3 segundos *(Implementado — microsserviços leves com Flask)*

- ✅ **RNF03:** O código deve estar documentado e postado em um repositório Git *(Implementado — repositório Git com documentação)*

- ✅ **RNF04:** O sistema deve ser compatível com navegadores modernos (Chrome, Firefox, Safari, Edge) *(Implementado — HTML/CSS/JS padrão)*

- ✅ **RNF05:** A interface deve ser intuitiva e não requer treinamento prévio do usuário *(Implementado)*

- ✅ **RNF08:** O sistema deve contar com permanência de dados *(Implementado — persistência em JSON)*
