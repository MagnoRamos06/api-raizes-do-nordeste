# API Raízes do Nordeste

Projeto acadêmico de back-end para gestão de uma rede de alimentação regional.

| Informação | Dados |
|---|---|
| Instituição | UNINTER — Centro Universitário Internacional |
| Acadêmico | Magno Rodrigues Ramos Filho |
| RU | 5023493 |
| Localidade | Goiânia, Goiás |

## Apresentação

A API Raízes do Nordeste organiza as operações centrais de uma rede com mais de uma unidade. O sistema registra clientes, catálogo, cardápios e estoque por unidade, acompanha pedidos desde a criação até a entrega e identifica o canal em que cada pedido foi realizado.

O projeto demonstra um fluxo completo de back-end: autenticação, autorização por perfil, validação de regras de negócio, persistência relacional, auditoria e documentação de endpoints. A integração financeira é simulada para permitir a demonstração de aprovação e recusa sem armazenar dados de cartão ou depender de um serviço externo.

## Objetivo

Desenvolver uma API documentada e reproduzível para apoiar as operações de uma rede de alimentação, mantendo o estoque consistente durante o fluxo de pedidos e restringindo cada operação ao perfil autorizado.

## Funcionalidades

- Cadastro de clientes e autenticação com token Bearer.
- Criação de contas operacionais por um administrador.
- Cadastro e consulta de unidades e produtos.
- Consulta de cardápio e preços por unidade.
- Controle de entradas e saídas de estoque.
- Criação de pedidos com canal de origem e validação de disponibilidade.
- Reserva de estoque durante o processamento do pedido.
- Simulação de pagamento aprovado ou recusado, com cancelamento e estorno quando necessário.
- Atualização do pedido pela cozinha e pelo atendimento, respeitando as transições permitidas.
- Programa de fidelidade opcional, com consentimento, saldo, extrato, resgate e estorno.
- Registro de ações sensíveis e consulta de auditoria restrita ao administrador.
- Respostas padronizadas para erros e rota de verificação da API.

Campanhas promocionais permanecem como proposta de evolução e não fazem parte das funcionalidades disponíveis neste MVP.

## Perfis de acesso

| Perfil | Operações principais |
|---|---|
| CLIENTE | Gerenciar o próprio acesso, consultar informações e acompanhar os próprios pedidos. |
| COZINHA | Consultar pedidos e marcar como prontos. |
| ATENDENTE | Consultar pedidos e marcar como entregues. |
| GERENTE | Gerenciar catálogo e estoque e avançar as etapas do pedido. |
| ADMIN | Provisionar contas internas, gerenciar operações e consultar auditoria. |

O cadastro público sempre cria uma conta de cliente. O perfil administrativo não pode ser escolhido pelo próprio usuário.

## Tecnologias

- Python 3.10 ou superior
- FastAPI
- SQLModel
- SQLite
- Alembic
- Postman

## Organização do código

```text
app/
  api/              rotas HTTP, contratos e dependências
  application/      casos de uso e regras de aplicação
  domain/           tipos e estados centrais do negócio
  infrastructure/   conexão SQLite e modelos persistidos
  config.py         configurações da aplicação
  main.py           criação da aplicação FastAPI
  seed.py           preparação dos dados iniciais
docs/               requisitos, decisões, testes e diagramas
migrations/         histórico de alterações do banco
postman/            coleção e ambiente de demonstração
```

As rotas recebem as solicitações HTTP e encaminham o trabalho para os casos de uso. A aplicação aplica as regras de negócio e utiliza a infraestrutura para persistir os dados. A justificativa dessa organização está em [decisões de projeto](docs/decisoes-de-projeto.md), e os relacionamentos estão nos [diagramas](docs/diagramas.md).

## Preparação do ambiente

### Requisitos

Tenha Python 3.10 ou superior e o `pip` instalados. Os comandos a seguir consideram o PowerShell do Windows.

### Instalação

Na pasta do projeto, crie e ative um ambiente virtual:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

Instale as dependências e crie o arquivo local de configuração:

```powershell
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edite o `.env` e informe uma chave `JWT_SECRET_KEY` exclusiva com pelo menos 32 caracteres, além de um e-mail e uma senha próprios para a conta inicial de administrador. Não publique esse arquivo nem reutilize os valores de exemplo em um servidor acessível pela internet.

Aplique a migração do banco e prepare os dados iniciais:

```powershell
alembic upgrade head
python -m app.seed
```

Inicie a API localmente:

```powershell
uvicorn app.main:app --reload
```

O banco será criado em `data/raizes.db`. Para encerrar o servidor, use `Ctrl+C` no terminal.

## Acessar e demonstrar a API

Com o servidor em execução, use estes endereços no navegador:

- API: http://127.0.0.1:8000
- Documentação interativa: http://127.0.0.1:8000/docs
- Esquema OpenAPI: http://127.0.0.1:8000/openapi.json
- Verificação de saúde: http://127.0.0.1:8000/health

A documentação interativa permite consultar contratos e enviar requisições. Para rotas protegidas, faça login e informe o token Bearer no botão de autorização.

### Percurso de demonstração

1. Use as credenciais definidas no `.env` para entrar como administrador.
2. Cadastre perfis de cozinha e atendimento e consulte ou prepare o catálogo e o estoque da unidade inicial.
3. Cadastre um cliente e entre com a conta criada.
4. Consulte unidades e produtos e crie um pedido informando o canal de origem.
5. Simule a aprovação ou recusa do pagamento e observe o resultado no pedido e no estoque.
6. Com os perfis de cozinha e atendimento, avance o pedido até a entrega.
7. Se desejar demonstrar fidelidade, registre o consentimento, acumule pontos e faça um resgate antes do pagamento.

O saldo inicial de uma unidade é preparado pelo seed. Os IDs usados nas requisições devem ser os retornados pela própria API durante a demonstração.

## Rotas principais

| Método | Rota | Finalidade |
|---|---|---|
| `POST` | `/auth/cadastro` | Cadastrar cliente. |
| `POST` | `/auth/login` | Autenticar e obter token. |
| `GET` | `/auth/me` | Consultar a conta autenticada. |
| `POST` | `/auth/usuarios-operacionais` | Criar conta interna; somente ADMIN. |
| `GET` / `POST` | `/unidades` | Consultar e cadastrar unidades. |
| `GET` / `POST` | `/produtos` | Consultar e cadastrar produtos. |
| `GET` | `/unidades/{unidade_id}/cardapio` | Consultar o cardápio da unidade. |
| `GET` | `/unidades/{unidade_id}/estoque` | Consultar o estoque. |
| `POST` | `/unidades/{unidade_id}/estoque/{produto_id}/movimentacoes` | Registrar movimentação de estoque. |
| `POST` | `/pedidos` | Criar pedido e reservar itens disponíveis. |
| `GET` | `/pedidos` | Consultar pedidos conforme perfil e filtros. |
| `POST` | `/pedidos/{pedido_id}/pagamento-mock` | Simular o resultado do pagamento. |
| `PATCH` | `/pedidos/{pedido_id}/status` | Avançar o pedido conforme perfil. |
| `GET` | `/fidelidade/me` | Consultar saldo e extrato do cliente. |
| `POST` | `/fidelidade/consentimento` | Registrar adesão ou retirada do consentimento. |
| `POST` | `/fidelidade/resgates` | Resgatar pontos antes do pagamento. |
| `GET` | `/auditoria` | Consultar eventos; somente ADMIN. |
| `GET` | `/health` | Verificar se a API está ativa. |

A referência de permissões, parâmetros, respostas e erros está em [documentação da API](docs/api.md). Os erros seguem um formato comum com código, mensagem, detalhes, horário, rota e identificador da solicitação.

## Testar com Postman

Os arquivos da coleção e do ambiente local estão em `postman/`:

- `raizes-api.postman_collection.json`: sequência de requisições e verificações.
- `ambiente-local.template.json`: endereço e variáveis do ambiente local.

Importe os dois arquivos no Postman, configure o endereço como `http://127.0.0.1:8000`, informe as credenciais locais do administrador e execute as requisições na ordem da coleção. A coleção prepara os demais usuários e dados necessários aos cenários.

O resultado registrado em [evidência de testes](docs/evidencia-testes.md) apresenta 31 requisições e 31 verificações aprovadas, sem falhas, além das validações manuais de `/health`, `/docs` e `/openapi.json`. A execução foi realizada em 24/09/2026, após aplicar a migração e o seed em um banco SQLite vazio.

## Banco de dados

O SQLite mantém os dados localmente. A estrutura inicial está versionada em `migrations/versions/0001_initial_schema.py`. Para atualizar o banco, aplique as migrações pendentes com `alembic upgrade head`.

Para criar uma nova revisão após alterar os modelos, use `alembic revision --autogenerate -m "descricao da alteracao"`, confira o arquivo gerado e aplique a revisão. O arquivo `.env` e o banco local não devem ser enviados ao repositório.

## Documentação

- [Referência da API](docs/api.md)
- [Análise e requisitos](docs/requisitos.md)
- [Decisões de projeto](docs/decisoes-de-projeto.md)
- [Diagramas](docs/diagramas.md)
- [Plano de testes](docs/plano-de-testes.md)
- [Evidência da execução](docs/evidencia-testes.md)
- [Relatório técnico](docs/relatorio-tecnico.md)

O DER, o diagrama de casos de uso e a sequência de criação do pedido estão disponíveis em `docs/` nos formatos SVG.

## Segurança e privacidade

As senhas são armazenadas com hash e as rotas verificam o perfil antes de executar ações restritas. O segredo JWT e as credenciais administrativas ficam em variáveis locais do `.env`. O programa de fidelidade depende de consentimento, e os registros de auditoria não armazenam credenciais.

O projeto deve ser executado com credenciais próprias. Não use os dados de exemplo fora do ambiente local.
