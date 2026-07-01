# Step 117.1 — Add Draw Ticket Pack Price Sync

Hotfix слой: синхронизира визуалния Add Draw статус с реалния Step 117 пакет. Не променя числата и не обещава печалба.

- Status: `ADD_DRAW_TICKET_PACK_PRICE_SYNC_READY`
- Blocking failures: `0`
- Очаквани редове: `12`
- Очаквана цена: `10.80 EUR`
- Add Draw snapshot: `12` реда / `10.80 EUR`
- Lifecycle snapshot: `12` реда / `10.80 EUR`

## Проверки

- `OK` — v117_total_lines_is_12: v117 total_lines=12
- `OK` — v117_total_price_is_10_80: v117 total_price_eur=10.8
- `OK` — v96_add_draw_snapshot_uses_12_lines: v96 active_plan_combinations=12
- `OK` — v96_add_draw_snapshot_uses_10_80: v96 active_plan_cost_eur=10.8
- `OK` — v97_lifecycle_plan_uses_12_lines: v97 combination_count=12
- `OK` — v97_lifecycle_plan_uses_10_80: v97 cost_eur=10.8
- `OK` — add_draw_info_label_is_generic_pack_label: Add Draw reads active_plan_label_bg instead of hard-coded budget-plan text.
