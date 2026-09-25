# Análise e priorização de requisitos

## Contexto e objetivo

A rede Raízes do Nordeste atende por canais digitais e presenciais e opera mais de uma unidade. O back-end deve registrar a origem do pedido, consultar disponibilidade por unidade e coordenar pagamento e preparo sem permitir que um pedido ultrapasse o saldo disponível.

## Atores

| Ator | Responsabilidade no sistema |
|---|---|
| Cliente | Cadastrar-se, autenticar-se, criar e consultar os próprios pedidos, pagar pelo mock e escolher se participa do programa de fidelidade. |
| COZINHA | Consultar pedidos e estoque e marcar como pronto os pedidos em preparação. |
| ATENDENTE | Consultar pedidos e marcar como entregue os pedidos prontos. |
| GERENTE | Gerir catálogo e estoque e avançar as duas transições de status. |
| ADMIN | Provisionar contas internas, gerir catálogo/estoque, consultar auditoria e administrar status. |

## Requisitos funcionais priorizados

| ID | Prioridade | Requisito | Estado no MVP |
|---|---|---|---|
| RF01 | P0 | Cadastrar clientes e autenticar com token; nunca expor a senha armazenada. | Implementado |
| RF02 | P0 | Restringir operações por perfil e permitir provisionamento interno apenas por ADMIN. | Implementado |
| RF03 | P0 | Manter unidades, produtos e saldo de estoque por unidade. | Implementado |
| RF04 | P0 | Criar pedidos com `canalPedido`, validar unidade/produto/quantidade/saldo e guardar preço no momento da compra. | Implementado |
| RF05 | P0 | Reservar estoque de forma condicional; devolver o saldo em pagamento recusado. | Implementado |
| RF06 | P0 | Simular aprovação ou recusa do pagamento e registrar status, valor, referência e resposta mock. | Implementado |
| RF07 | P0 | Aplicar transições de pedido autorizadas conforme o perfil. | Implementado |
| RF08 | P0 | Consultar pedidos com filtros por canal/status e paginação; clientes veem somente os próprios. | Implementado |
| RF09 | P1 | Oferecer fidelidade opcional com consentimento histórico, acúmulo, resgate e estorno. | Implementado |
| RF10 | P1 | Auditar ações sensíveis e permitir consulta restrita a ADMIN. | Implementado |
| RF11 | P2 | Gerir campanhas promocionais por período, produtos/unidades e regra de desconto. | Proposta; não implementado |

## Requisitos não funcionais

| ID | Requisito | Decisão / evidência |
|---|---|---|
| RNF01 | Persistência relacional real e alterações reproduzíveis. | SQLite com SQLModel e migração Alembic versionada. |
| RNF02 | Integridade de valores e quantidades. | Decimal monetário, validações de contrato e restrições SQL para preço, quantidade e saldo. |
| RNF03 | Segurança das credenciais e endpoints. | Hash Argon2, JWT, validação de perfil e `.env` local fora do repositório. |
| RNF04 | Respostas previsíveis em falhas. | Envelope comum com código, mensagem, detalhes, rota, horário e `requestId`. |
| RNF05 | Evolução e manutenção do código. | Separação API, aplicação, domínio e infraestrutura; contratos e documentação dedicados. |
| RNF06 | Privacidade proporcional ao escopo. | Minimização de dados, fidelidade opcional, auditoria sem credenciais e estratégia de retenção documentada. |
| RNF07 | Correção reproduzível. | README, Swagger/OpenAPI, DER, plano e coleção de cenários Postman. |

## Desempenho, disponibilidade e falhas de integração

- RNF08 — Desempenho em horários de pico: listagens principais usam paginação e os campos de consulta têm índices. Testes de carga e dimensionamento de capacidade permanecem como evolução; a execução local não comprova desempenho em produção.
- RNF09 — Disponibilidade: a rota /health permite verificar a aplicação. Supervisão de processo, cópias de segurança e restauração do banco são medidas propostas para uma futura implantação. O MVP não estabelece acordo de nível de serviço.
- RNF10 — Falhas de pagamento: o mock permite aprovação e recusa, preservando transação, estoque e fidelidade. Uma integração real exigirá tempo limite, tratamento de indisponibilidade, reconciliação e identificador de idempotência. Não há chamadas a um provedor externo nesta versão.

## Recorte do MVP e justificativas

O caminho P0 é **pedido → reserva de estoque → pagamento mock → preparação → entrega**. Ele percorre autenticação, regras de negócio, persistência, multicanalidade e autorização de ponta a ponta. Fidelidade foi incluída como requisito P1 por sua relevância ao cenário, com participação voluntária para reduzir coleta desnecessária. A integração de pagamento é deliberadamente um mock: permite demonstrar sucesso e recusa sem armazenar dados de cartão nem depender de serviço externo.

Campanhas promocionais permanecem como proposta P2; a API não deve anunciar essa funcionalidade como disponível. O recorte deixa a solução demonstrável sem acrescentar lógica comercial ainda não necessária ao fluxo mínimo do roteiro.
