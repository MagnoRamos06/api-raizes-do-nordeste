# Diagramas do sistema

Os diagramas usam uma paleta consistente, limites de sistema e rótulos de relação. Foram alinhados às rotas, perfis, entidades e transições descritas no código.

## Casos de uso

![Diagrama de casos de uso](casos-de-uso.svg)

As associações distinguem Cliente, COZINHA, ATENDENTE, GERENTE, ADMIN e o sistema externo de pagamento representado no exercício. O cliente atua nos próprios pedidos e na adesão opcional à fidelidade. COZINHA conclui o preparo; ATENDENTE registra a entrega. GERENTE e ADMIN têm as permissões de gestão descritas na referência da API.

O participante externo é conceitual: no MVP, o caso de uso é atendido por um simulador interno, sem integração de rede nem dados de cartão. O diagrama apresenta o ator esperado numa evolução com provedor real e identifica claramente o limite do que foi implementado.

## Modelo de dados

![Diagrama Entidade-Relacionamento](der.svg)

O DER mostra PK, FK, campos relevantes e cardinalidades. As chaves estão diferenciadas por cor; restrições de unicidade e integridade aparecem no atributo ou na legenda. `ItemPedido.preco_unitario` preserva o preço no momento da compra; consentimentos e movimentos de fidelidade são históricos.

## Classes

![Diagrama de classes](classes.svg)

O diagrama de classes complementa o DER com os atributos principais, tipos de domínio e associações presentes nos modelos SQLModel. As classes e relações foram conferidas com `app/infrastructure/models.py`; os enums de perfil, canal e estado estão em `app/domain/enums.py`.

## Especificação do caso de uso crítico

A especificação completa de **Criar pedido e processar pagamento** está em [`fluxo-critico.md`](fluxo-critico.md). Ela reúne pré-condições, pós-condições, fluxo principal, alternativas e exceções e regras de negócio, incluindo reserva de estoque, recusa do pagamento e idempotência.

## Sequência do fluxo crítico

![Sequência do pedido e pagamento mock](sequencia-pedido.svg)

O fluxo usa mensagens numeradas e um fragmento alternativo para separar aprovação e recusa. A aprovação encaminha para preparo; a recusa cancela e restaura estoque, além de estornar pontos se houver resgate. O preparo e a entrega dependem dos respectivos perfis. A descrição textual das regras e exceções complementa o desenho.
