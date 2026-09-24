# Especificação do caso de uso crítico

## UC01 — Criar pedido e processar pagamento

| Campo | Descrição |
|---|---|
| Objetivo | Registrar um pedido multicanal, reservar o estoque da unidade escolhida e encaminhar o pedido para preparo após a aprovação do pagamento simulado. |
| Ator principal | Cliente autenticado. |
| Participantes | API, aplicação, banco SQLite e simulador interno de pagamento. |
| Gatilho | Cliente envia uma solicitação para criar um pedido. |
| Prioridade | Essencial para o fluxo mínimo do projeto. |

### Pré-condições

1. O cliente está cadastrado e autenticado com um token válido.
2. A unidade existe e está ativa.
3. Cada produto informado existe, está ativo e possui saldo suficiente na unidade.
4. O pedido contém ao menos um item, quantidades positivas e um valor final maior que zero.
5. O canal de origem foi informado com um dos valores aceitos: `APP`, `TOTEM`, `BALCAO`, `PICKUP` ou `WEB`.

### Pós-condições

**Em caso de aprovação:** o pedido fica em `EM_PREPARACAO`, o pagamento mock fica `APROVADO`, o estoque reservado permanece abatido e, se o cliente tiver consentimento ativo, os pontos correspondentes ao valor efetivamente pago são registrados.

**Em caso de recusa:** o pedido fica `CANCELADO`, o pagamento mock fica `RECUSADO`, o estoque reservado é devolvido e qualquer ponto usado no pedido é estornado. O saldo final de estoque e fidelidade fica registrado no banco.

**Em falha antes da criação:** não deve permanecer pedido parcial nem reserva de estoque sem pedido correspondente.

### Fluxo principal

1. O cliente informa a unidade, o canal e os produtos com suas quantidades.
2. A API valida o token, o contrato e os campos obrigatórios.
3. A aplicação verifica a unidade, a disponibilidade dos produtos e o saldo de cada item.
4. A aplicação calcula os valores com o preço vigente do catálogo.
5. Em uma transação, a aplicação reserva o estoque, cria o pedido e seus itens com o preço unitário registrado no momento da compra e grava a ação na auditoria.
6. A API devolve o pedido em `AGUARDANDO_PAGAMENTO`.
7. O cliente pode resgatar pontos antes do pagamento, se tiver consentimento e saldo. Em seguida, solicita a simulação com resultado `APROVADO`.
8. A aplicação cria a referência e a resposta fictícias do pagamento e atualiza o pedido para `EM_PREPARACAO`.
9. Com consentimento ativo, a aplicação registra os pontos do valor pago, sem incluir o desconto resgatado na base de cálculo.
10. A API retorna o pedido atualizado e o resultado do pagamento.
11. COZINHA, autenticada com seu perfil, altera o pedido de `EM_PREPARACAO` para `PRONTO`.
12. ATENDENTE, autenticado com seu perfil, altera o pedido de `PRONTO` para `ENTREGUE`.

### Fluxos alternativos e exceções

| Situação | Comportamento esperado |
|---|---|
| A unidade ou um produto não existe ou não está disponível | A API responde `404`; pedido e estoque permanecem inalterados. |
| O estoque é insuficiente | A API responde `409`; nenhuma parte do pedido fica reservada. |
| Falta canal, item ou quantidade válida | A API responde `422` com o envelope de erro padronizado; não há gravação. |
| O cliente tenta pagar pedido de outra pessoa | A API responde `403` e não altera o pedido. A listagem de pedidos filtra os registros pelo próprio cliente. |
| O pagamento é recusado | A aplicação grava a recusa, cancela o pedido, devolve o estoque e estorna eventual resgate de pontos. |
| O pedido já teve o pagamento processado | A nova tentativa responde `409`; não cria pagamento, não altera estoque e não credita pontos de novo. |
| Um perfil sem permissão tenta avançar o pedido | A API responde `403`; o estado permanece igual. |
| A transição pedida não corresponde ao estado atual | A API responde `409`; o pedido mantém o estado anterior. |
| Ocorre falha inesperada durante a gravação | A transação deve ser revertida; a resposta não expõe detalhes internos e inclui `requestId` para rastreio. |

### Regras de negócio

| ID | Regra |
|---|---|
| RN01 | `canalPedido` é obrigatório e deve corresponder a um canal permitido pelo domínio. |
| RN02 | O cliente só cria e consulta os próprios pedidos; perfis internos consultam conforme as permissões documentadas na API. |
| RN03 | A disponibilidade é validada por combinação de unidade e produto. O saldo não pode ficar negativo. |
| RN04 | Pedido e reserva devem ser gravados de forma transacional. Se qualquer item falhar, a operação inteira é desfeita. |
| RN05 | O preço unitário de cada item é uma cópia do preço vigente no momento da criação; alterações posteriores no catálogo não modificam o pedido. |
| RN06 | Cada pedido recebe no máximo um processamento de pagamento. Uma segunda tentativa não gera efeitos colaterais. |
| RN07 | Somente o resultado aprovado leva o pedido para preparação; a recusa cancela e devolve a reserva de estoque. |
| RN08 | COZINHA executa a transição para `PRONTO`; ATENDENTE executa a transição para `ENTREGUE`. GERENTE e ADMIN podem executar ambas. |
| RN09 | A fidelidade é opcional. Apenas clientes com consentimento ativo acumulam pontos; resgate recusado é estornado uma única vez. |
| RN10 | A simulação de pagamento não recebe nem armazena número de cartão, código de segurança ou credenciais financeiras. |
| RN11 | Cada operação sensível gera auditoria sem guardar senha, token ou conteúdo pessoal desnecessário. |

### Pós-condição do ciclo operacional

O pedido aprovado passa por `AGUARDANDO_PAGAMENTO → EM_PREPARACAO → PRONTO → ENTREGUE`. Se o pagamento for recusado, passa para `CANCELADO`; não há transição posterior para preparo ou entrega.

### Rastreabilidade

- Criação e pagamento: `app/application/orders.py` e rotas em `app/api/routes/orders.py`.
- Tipos e estados: `app/domain/enums.py`.
- Permissões e contratos HTTP: [`api.md`](api.md).
- Diagrama visual do fluxo: [`sequencia-pedido.svg`](sequencia-pedido.svg).
- Cenários executáveis: [`plano-de-testes.md`](plano-de-testes.md) e coleção Postman.
