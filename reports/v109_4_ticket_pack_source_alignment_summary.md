# Step 109.4 — Ticket Pack Source Alignment

- Status: `TICKET_PACK_SOURCES_ALIGNED`
- Blocking failures: `0`
- Само финален план: `2` фиша / `8` комбинации
- Разширен пакет: `3` фиша / `12` комбинации

## Проверки

- `OK` — final_plan_only_has_two_tickets: final_cards=2
- `OK` — final_plan_tickets_have_four_lines: [4, 4]
- `OK` — extended_has_three_tickets: extended_cards=3
- `OK` — extended_tickets_have_four_lines: [4, 4, 4]
- `OK` — third_ticket_is_marked_supplementary: third_scope=supplementary
- `OK` — extended_lines_are_unique: unique=12, total=12
