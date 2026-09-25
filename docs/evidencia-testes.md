# Evidência da execução local

**Revisão:** 25/09/2026.

## Ambiente e método

Banco SQLite novo e isolado, preparado com a migração Alembic e o seed. A coleção Postman foi executada por Newman contra a API local. Os dados são fictícios e as credenciais de execução não fazem parte da entrega.

## Resultado da coleção

- 35 requisições executadas.
- 35 verificações aprovadas.
- 0 falhas.
- Fluxo principal, cenários negativos, fidelidade e auditoria executados.
- Quatro cenários de regressão incluídos para normalização de texto, mensagens em português e contrato OpenAPI.

## Verificação complementar

Uma rodada independente confirmou 11 casos: nome de produto curto após retirar espaços, endereço curto após retirar espaços, e-mail inválido, senha incorreta, token inválido, paginação inválida, cadastro válido, cadastro duplicado, canal inválido, produto duplicado no pedido e tentativa de cadastro de produto por cliente. Os 11 casos retornaram os códigos esperados. Esses casos complementares não são somados às 35 verificações da coleção.

## Reproduzir

Siga o README, aplique a migração e o seed, inicie a API e importe a coleção e o ambiente em `postman/`. Preencha as credenciais locais do administrador e execute as pastas na ordem. Os cenários T30 a T33 dependem do token administrativo obtido no fim do fluxo anterior.

O resultado demonstra somente os comportamentos cobertos. Não representa teste de carga nem certificação de segurança em produção.

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
| T30 - Rejeitar nome curto após remover espaços | 422 | Passou |
| T31 - Rejeitar endereço curto após remover espaços | 422 | Passou |
| T32 - Validar e-mail com mensagem em português | 422 | Passou |
| T33 - Conferir erros no contrato OpenAPI | 200 | Passou |
