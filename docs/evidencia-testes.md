# Evidência da execução local

**Data:** 24/09/2026
**Base:** banco SQLite isolado e vazio, preparado com a migração Alembic e o seed do projeto.
**Execução:** coleção Postman `raizes-api.postman_collection.json` via Newman, contra a API local.

## Resultado

- 31 requisições executadas.
- 31 scripts de teste executados.
- 0 falhas.
- Migração Alembic e seed concluídos antes do início da API.
- Verificação manual adicional: `/health`, `/docs` e `/openapi.json` responderam HTTP 200.

## Comportamentos verificados

- Cadastro/login de cliente e login ADMIN.
- Proteção de rota sem token (401) e bloqueio de ação sem permissão (403).
- Validação de campo obrigatório e quantidade negativa (422).
- Produto inexistente (404) e estoque insuficiente (409).
- Criação de pedido, filtro por canal, pagamento aprovado e bloqueio de pagamento repetido.
- Transições de pedido feitas pelos perfis COZINHA e ATENDENTE.
- Resgate de pontos, recusa do pagamento, cancelamento e estorno de estoque/pontos.
- Consulta do evento de criação na auditoria.

Uma asserção de fidelidade foi ajustada para comparar valores monetários decimais como números, pois a resposta JSON da API os representa como texto decimal (por exemplo, `"5.00"`). A coleção passou integralmente após o ajuste.

## Reproduzir

Siga os passos de instalação e execução do [README](../README.md), importe a coleção e o ambiente modelo do Postman e execute os itens na ordem apresentada. Preencha as credenciais do ADMIN com os valores configurados no seed. Não use as credenciais temporárias usadas nesta validação.

## Resultado por requisição

| Cenário | HTTP observado | Verificação |
|---|---:|---|
| T01 - Cadastrar cliente com consentimento opcional | 201 | Passou |
| T02 - Login do cliente | 200 | Passou |
| T03 - Listar unidades e guardar ID do seed | 200 | Passou |
| T04 - Cardápio da unidade | 200 | Passou |
| T05 - Rota protegida sem token | 401 | Passou |
| T06 - Login do administrador do seed | 200 | Passou |
| T07 - Criar usuário de cozinha | 201 | Passou |
| T08 - Criar usuário de atendimento | 201 | Passou |
| T09 - Criar produto de teste para fluxo e pontos | 201 | Passou |
| T10 - Entrada inicial de estoque | 200 | Passou |
| T11 - Login do cliente antes do fluxo | 200 | Passou |
| T12 - Canal obrigatório ausente | 422 | Passou |
| T13 - Produto inexistente | 404 | Passou |
| T14 - Estoque insuficiente | 409 | Passou |
| T14B - Quantidade negativa | 422 | Passou |
| T15 - Criar pedido válido | 201 | Passou |
| T15B - Filtrar pedidos por canalPedido | 200 | Passou |
| T16 - Aprovar pagamento mock | 200 | Passou |
| T17 - Cliente não pode avançar status | 403 | Passou |
| T18 - Pagamento repetido é bloqueado | 409 | Passou |
| T19 - Login da cozinha | 200 | Passou |
| T20 - Cozinha marca pedido pronto | 200 | Passou |
| T21 - Login do atendente | 200 | Passou |
| T22 - Atendente entrega pedido | 200 | Passou |
| T23 - Login do cliente para segundo pedido | 200 | Passou |
| T24 - Criar pedido para resgatar pontos | 201 | Passou |
| T25 - Resgatar 100 pontos | 200 | Passou |
| T26 - Recusar pagamento e estornar pontos | 200 | Passou |
| T27 - Conferir estorno no saldo de fidelidade | 200 | Passou |
| T28 - Login administrativo para consultar auditoria | 200 | Passou |
| T29 - Evidenciar criação de pedido na auditoria | 200 | Passou |
