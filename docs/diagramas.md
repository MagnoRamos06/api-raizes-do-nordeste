# Diagramas do sistema

Os diagramas usam uma paleta consistente, limites de sistema e rótulos de relação. Foram alinhados às rotas, perfis, entidades e transições descritas no código.

## Casos de uso

![Diagrama de casos de uso](casos-de-uso.svg)

As associações mostram o que cada ator pode fazer. Cliente atua nos próprios pedidos e na adesão opcional à fidelidade. COZINHA e ATENDENTE compartilham consulta, mas cada perfil executa sua transição. GERENTE e ADMIN têm as permissões de gestão descritas na referência da API.

## Modelo de dados

![Diagrama Entidade-Relacionamento](der.svg)

O DER mostra PK, FK, campos relevantes e cardinalidades. As chaves estão diferenciadas por cor; restrições de unicidade e integridade aparecem no atributo ou na legenda. `ItemPedido.preco_unitario` preserva o preço no momento da compra; consentimentos e movimentos de fidelidade são históricos.

## Sequência do fluxo crítico

![Sequência do pedido e pagamento mock](sequencia-pedido.svg)

O fluxo usa mensagens numeradas e um fragmento alternativo para separar aprovação e recusa. A aprovação encaminha para preparo; a recusa cancela e restaura estoque, além de estornar pontos se houver resgate. O preparo e a entrega dependem dos respectivos perfis.
