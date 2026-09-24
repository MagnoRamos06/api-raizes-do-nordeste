# Referência da API

Base local: `http://127.0.0.1:8000`. A documentação interativa gerada pelo FastAPI fica em `/docs`; OpenAPI em `/openapi.json`. Para rotas protegidas, envie `Authorization: Bearer <token>`.

Os corpos e respostas usam nomes JSON em camelCase quando indicado no contrato. Campos monetários são decimais em reais. Todas as falhas tratadas pela API seguem este envelope:

```json
{
  "error": "VALIDATION_ERROR",
  "message": "Um ou mais campos são inválidos.",
  "details": [{"field": "canalPedido", "issue": "Field required"}],
  "timestamp": "2026-09-24T12:00:00+00:00",
  "path": "/pedidos",
  "requestId": "identificador-da-requisicao"
}
```

## Autenticação

| Método e rota | Acesso | Entrada principal | Sucesso | Erros relevantes |
|---|---|---|---|---|
| `POST /auth/cadastro` | Público | `{"nome":"Ana Silva","email":"ana@example.com","senha":"senha-segura","consentimento_fidelidade":true}` | `201`: usuário público com `id`, `nome`, `email`, `perfil=CLIENTE` | `409` e-mail cadastrado; `422` campos inválidos |
| `POST /auth/login` | Público | `{"email":"ana@example.com","senha":"senha-segura"}` | `200`: `{"access_token":"…","token_type":"bearer"}` | `401` credenciais inválidas |
| `GET /auth/me` | Bearer, qualquer perfil | — | `200`: dados públicos do usuário autenticado | `401` token ausente, inválido ou expirado |
| `POST /auth/usuarios-operacionais` | ADMIN | Cadastro com `perfil` igual a `ATENDENTE`, `COZINHA` ou `GERENTE` | `201`: usuário público | `401`, `403`, `409` e-mail duplicado, `422` perfil/campos inválidos |

O cadastro público sempre cria `CLIENTE`; só ADMIN pode provisionar os perfis operacionais.

Exemplos de resposta de sucesso (IDs e token ilustrativos):

```json
{"id":1,"nome":"Ana Silva","email":"ana@example.com","perfil":"CLIENTE"}
{"access_token":"<jwt>","token_type":"bearer"}
```

O primeiro objeto é usado no cadastro, na consulta `/auth/me` e no provisionamento operacional (com o perfil correspondente).

## Catálogo e estoque

| Método e rota | Acesso | Entrada principal | Sucesso | Erros relevantes |
|---|---|---|---|---|
| `GET /unidades` | Público | — | `200`: lista de unidades ativas | — |
| `POST /unidades` | GERENTE ou ADMIN | `{"nome":"Centro","endereco":"Rua Exemplo, 100"}` | `201`: unidade criada | `401`, `403`, `422` |
| `GET /produtos?page=1&limit=20` | Público | `page` ≥ 1; `limit` entre 1 e 100 | `200`: lista paginada de produtos ativos | `422` paginação inválida |
| `POST /produtos` | GERENTE ou ADMIN | `{"nome":"Sanduíche","descricao":"Pão, queijo e tomate","preco":"25.00"}` | `201`: produto criado | `401`, `403`, `422` |
| `GET /unidades/{unidade_id}/cardapio` | Público | ID da unidade no path | `200`: produtos ativos com saldo positivo, preço e disponibilidade | `404` unidade ausente/inativa |
| `POST /unidades/{unidade_id}/estoque/{produto_id}/movimentacoes` | GERENTE ou ADMIN | `{"tipo":"ENTRADA","quantidade":20}` ou `SAIDA` | `200`: `{"unidadeId":1,"produtoId":2,"quantidade":20}` | `401`, `403`, `404`, `409` saída maior que saldo, `422` |
| `GET /unidades/{unidade_id}/estoque` | COZINHA, GERENTE ou ADMIN | ID da unidade no path | `200`: saldos da unidade | `401`, `403`, `404` unidade inexistente |

Exemplos de respostas: `GET /unidades` retorna `[ {"id":1,"nome":"Centro","endereco":"Rua Exemplo, 100","ativa":true} ]`; cadastrar unidade retorna o mesmo objeto. `GET /produtos` retorna `[ {"id":2,"nome":"Sanduíche","descricao":"Pão, queijo e tomate","preco":"25.00","ativo":true} ]`; cadastrar produto retorna o mesmo objeto. O cardápio retorna `[ {"produtoId":2,"nome":"Sanduíche","descricao":"Pão, queijo e tomate","preco":"25.00","disponivel":true} ]`. Consulta de estoque retorna `[ {"unidadeId":1,"produtoId":2,"quantidade":20} ]`; movimentação retorna um objeto com esse formato.

## Pedidos e pagamento simulado

| Método e rota | Acesso | Entrada principal | Sucesso | Erros relevantes |
|---|---|---|---|---|
| `POST /pedidos` | CLIENTE | `{"unidadeId":1,"canalPedido":"TOTEM","itens":[{"produtoId":2,"quantidade":1}]}` | `201`: pedido em `AGUARDANDO_PAGAMENTO`, itens com preço congelado e total | `401`, `404` unidade/produto, `409` estoque insuficiente, `422` contrato inválido |
| `POST /pedidos/{pedido_id}/pagamento-mock` | CLIENTE dono do pedido ou ADMIN | `{"resultado":"APROVADO"}` ou `{"resultado":"RECUSADO"}` | `200`: pedido e pagamento simulado; aprovado inicia preparação, recusado cancela e devolve estoque | `401`, `403`, `404`, `409` pedido fora do estado esperado, `422` |
| `PATCH /pedidos/{pedido_id}/status` | COZINHA/GERENTE/ADMIN para `PRONTO`; ATENDENTE/GERENTE/ADMIN para `ENTREGUE` | `{"status":"PRONTO"}` ou `{"status":"ENTREGUE"}` | `200`: pedido com status atualizado | `401`, `403`, `404`, `409` transição incompatível, `422` |
| `GET /pedidos?canalPedido=TOTEM&status=AGUARDANDO_PAGAMENTO&page=1&limit=10` | Bearer; CLIENTE vê apenas os próprios, equipe vê todos | Filtros opcionais `canalPedido`, `status`, `page` ≥ 1, `limit` entre 1 e 100 | `200`: lista de pedidos | `401`, `422` filtro/paginação inválidos |

Estados previstos: `AGUARDANDO_PAGAMENTO → EM_PREPARACAO → PRONTO → ENTREGUE`; uma recusa de pagamento leva a `CANCELADO`. O pagamento é somente um mock e não processa dados de cartão.

Exemplo de resposta de pedido criado ou atualizado:

```json
{
  "id": 3,
  "unidadeId": 1,
  "canalPedido": "TOTEM",
  "status": "AGUARDANDO_PAGAMENTO",
  "total": "25.00",
  "descontoFidelidade": "0.00",
  "itens": [{"produtoId": 2, "quantidade": 1, "precoUnitario": "25.00"}],
  "pagamento": null
}
```

No pagamento, `pagamento` passa a incluir `status`, `referencia`, `valor` e `payload`; a lista de pedidos devolve uma lista dos objetos de pedido. Os valores permitidos para `canalPedido` são `APP`, `TOTEM`, `BALCAO`, `PICKUP` e `WEB`.

## Fidelidade e consentimento

| Método e rota | Acesso | Entrada principal | Sucesso | Erros relevantes |
|---|---|---|---|---|
| `GET /fidelidade/me` | CLIENTE | — | `200`: consentimento atual, saldo e até 50 movimentos recentes | `401`, `403` perfil diferente de cliente |
| `POST /fidelidade/consentimento` | CLIENTE | `{"consentido":true}` ou `false` | `200`: resumo atualizado; cada escolha é registrada | `401`, `403` |
| `POST /fidelidade/resgates` | CLIENTE | `{"pedidoId":3,"pontos":100}`; múltiplos de 100 | `200`: pedido, pontos usados, desconto e total após desconto | `401`, `403`, `404`, `409` consentimento/saldo/estado/resgate inválido, `422` |

Com consentimento ativo, cada R$ 1,00 pago gera 1 ponto; 100 pontos geram R$ 5,00 de desconto. Resgate ocorre antes do pagamento e é estornado quando o mock recusa o pagamento.

Exemplos de sucesso: o resumo retorna `{"consentido":true,"pontos":100,"extrato":[{"tipo":"GANHO","pontos":100,"pedidoId":2,"criadoEm":"2026-09-24T12:00:00+00:00"}]}`; o resgate retorna `{"pedidoId":3,"pontosResgatados":100,"desconto":"5.00","totalAtualizado":"20.00"}`. Atualizar consentimento retorna o resumo no mesmo formato.

## Auditoria e saúde

| Método e rota | Acesso | Entrada principal | Sucesso | Erros relevantes |
|---|---|---|---|---|
| `GET /auditoria?entidade=PEDIDO&entidade_id=3&page=1&limit=50` | ADMIN | Filtros opcionais; `page` ≥ 1; `limit` entre 1 e 200 | `200`: eventos mais recentes primeiro | `401`, `403`, `422` paginação inválida |
| `GET /health` | Público | — | `200`: `{"status":"ok"}` | — |

Auditoria retorna uma lista como `[ {"id":8,"usuarioId":1,"acao":"PEDIDO_CRIADO","entidade":"PEDIDO","entidadeId":"3","detalhes":"canal=TOTEM;total=25.00","criadoEm":"2026-09-24T12:00:00+00:00"} ]`.

## Códigos usados

`200` consulta/atualização bem-sucedida; `201` recurso criado; `401` sem autenticação válida; `403` perfil sem permissão; `404` recurso ausente; `409` conflito com regra de negócio ou unicidade; `422` entrada inválida; `500` falha inesperada com mensagem genérica e `requestId` para rastreio.
