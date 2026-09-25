# Plano de testes da API

## Preparação e execução

1. Configure `.env`, aplique `alembic upgrade head` e execute `python -m app.seed`.
2. Inicie a API e confirme que `http://127.0.0.1:8000/docs` está acessível.
3. Importe `postman/raizes-api.postman_collection.json` e `postman/ambiente-local.template.json` no Postman.
4. Preencha `adminEmail` e `adminPassword` com os valores usados no seed. Selecione esse ambiente.
5. Execute a coleção na ordem apresentada; os scripts guardam tokens e IDs de resposta.

O primeiro usuário cliente consente com fidelidade, compra de demonstração de R$ 100,00, recebe 100 pontos, aplica R$ 5,00 no pedido seguinte e recebe os pontos de volta após a recusa simulada.

## Cenários executáveis

| ID | Cenário / endpoint | Pré-condição e entrada | Resultado esperado | Evidência na coleção |
|---|---|---|---|---|
| T01 | Cadastro de cliente — `POST /auth/cadastro` | Seed aplicado; consentimento opcional aceito | 201, perfil CLIENTE, senha ausente da resposta | T01 - Cadastrar cliente com consentimento opcional |
| T02 | Login cliente — `POST /auth/login` | Conta T01 | 200 e `access_token` | T02 - Login do cliente |
| T03 | Consultar unidade — `GET /unidades` | Seed aplicado | 200 e ID disponível | T03 - Listar unidades e guardar ID do seed |
| T04 | Cardápio da unidade — `GET /unidades/{id}/cardapio` | Unidade ativa com produto em estoque | 200 e lista de itens disponíveis | T04 - Cardápio da unidade |
| T05 | Rota protegida sem token — `GET /pedidos` | Nenhum token | 401 e envelope `UNAUTHENTICATED` | T05 - Rota protegida sem token |
| T06 | Login administrativo — `POST /auth/login` | Credenciais de seed | 200 e token ADMIN | T06 - Login do administrador do seed |
| T07 | Criar COZINHA — `POST /auth/usuarios-operacionais` | Token ADMIN | 201 e perfil COZINHA | T07 - Criar usuário de cozinha |
| T08 | Criar ATENDENTE — mesma rota | Token ADMIN | 201 e perfil ATENDENTE | T08 - Criar usuário de atendimento |
| T09 | Criar produto — `POST /produtos` | Token ADMIN | 201 e preço R$ 100,00 | T09 - Criar produto de teste para fluxo e pontos |
| T10 | Entrada de estoque — `POST /unidades/{id}/estoque/{id}/movimentacoes` | Unidade do seed, produto T09, token ADMIN | 200 e saldo 20 | T10 - Entrada inicial de estoque |
| T12 | Campo obrigatório ausente — `POST /pedidos` | Cliente autenticado; request sem `canalPedido` | 422 `VALIDATION_ERROR` | T12 - Canal obrigatório ausente |
| T13 | Produto inexistente — `POST /pedidos` | Cliente autenticado; `produtoId=999999999` | 404 e erro padronizado | T13 - Produto inexistente |
| T14 | Estoque insuficiente — `POST /pedidos` | Cliente autenticado; quantidade 1000 | 409 e estoque inalterado | T14 - Estoque insuficiente |
| T14B | Quantidade negativa — `POST /pedidos` | Cliente autenticado; quantidade -1 | 422 `VALIDATION_ERROR` | T14B - Quantidade negativa |
| T15 | Criar pedido — `POST /pedidos` | Cliente, produto e unidade válidos; canal TOTEM | 201, status AGUARDANDO_PAGAMENTO e `canalPedido=TOTEM` | T15 - Criar pedido válido |
| T15B | Filtrar canal — `GET /pedidos?canalPedido=TOTEM` | Pedido T15 | 200 e pedido presente | T15B - Filtrar pedidos por canalPedido |
| T16 | Pagamento aprovado — `POST /pedidos/{id}/pagamento-mock` | Pedido T15, resultado APROVADO | 200, pagamento MOCK e pedido EM_PREPARACAO | T16 - Aprovar pagamento mock |
| T17 | Perfil sem permissão — `PATCH /pedidos/{id}/status` | Cliente tenta mudar pedido em preparação | 403 | T17 - Cliente não pode avançar status |
| T18 | Pagamento repetido — mesma rota de pagamento | Pedido já aprovado | 409; não cria outro pagamento | T18 - Pagamento repetido é bloqueado |
| T19 | Login COZINHA — `POST /auth/login` | Conta T07 | 200 e token COZINHA | T19 - Login da cozinha |
| T20 | Pedido pronto — `PATCH /pedidos/{id}/status` | Pedido em preparação, token COZINHA | 200 e status PRONTO | T20 - Cozinha marca pedido pronto |
| T21 | Login ATENDENTE — `POST /auth/login` | Conta T08 | 200 e token ATENDENTE | T21 - Login do atendente |
| T22 | Entregar pedido — `PATCH /pedidos/{id}/status` | Pedido PRONTO, token ATENDENTE | 200 e status ENTREGUE | T22 - Atendente entrega pedido |
| T24 | Segundo pedido — `POST /pedidos` | Cliente com pelo menos 100 pontos | 201 e status AGUARDANDO_PAGAMENTO | T24 - Criar pedido para resgatar pontos |
| T25 | Resgatar pontos — `POST /fidelidade/resgates` | Pedido T24; 100 pontos disponíveis | 200, desconto R$ 5,00 e total R$ 95,00 | T25 - Resgatar 100 pontos |
| T26 | Pagamento recusado — rota de pagamento mock | Pedido T24 com resgate | 200, status CANCELADO, pagamento RECUSADO; estoque e pontos estornados | T26 - Recusar pagamento e estornar pontos |
| T27 | Consultar saldo — `GET /fidelidade/me` | Cliente autenticado | 200 e saldo restaurado a 100 pontos | T27 - Conferir estorno no saldo de fidelidade |
| T29 | Evidência de auditoria — `GET /auditoria` | Token ADMIN; filtro pelo pedido T15 | 200 e evento PEDIDO_CRIADO | T29 - Evidenciar criação de pedido na auditoria |

O conjunto contém mais que os 10 cenários mínimos e cobre casos positivos e negativos, autenticação, autorização, validação, estoque, pagamento recusado, canal do pedido e auditoria. A execução local da coleção foi confirmada em 25/09/2026: 35 chamadas, 35 scripts de teste e nenhuma falha. O resumo está em [evidência de testes](evidencia-testes.md).

## Regressão de validações e documentação

| ID | Cenário / endpoint | Pré-condição e entrada | Resultado esperado | Evidência na coleção |
|---|---|---|---|---|
| T30 | Nome curto — POST /produtos | ADMIN autenticado; nome " a ", preço 10 | 422; mensagem em português; mínimo dois caracteres após normalização | T30 - Rejeitar nome curto após remover espaços |
| T31 | Endereço curto — POST /unidades | ADMIN autenticado; nome válido e endereço " a   " | 422; mínimo cinco caracteres após normalização | T31 - Rejeitar endereço curto após remover espaços |
| T32 | E-mail inválido — POST /auth/cadastro | Nome e senha válidos; e-mail "invalido" | 422; mensagem de e-mail em português | T32 - Validar e-mail com mensagem em português |
| T33 | Contrato de erros — GET /openapi.json | API iniciada | 200; erros 401, 403, 404, 409 e 422 do pedido usam RespostaErro | T33 - Conferir erros no contrato OpenAPI |
