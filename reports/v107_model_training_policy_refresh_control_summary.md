# Step 107 — Политика за обучение и refresh control

Статус: **TRAINING_POLICY_READY**
Blocking failures: **0**
Dataset rows: **10064**
Real result rows since active plan: **3**

## Текуща препоръка

**Не обучавай тежки модели сега**

Има твърде малко нови реални резултати. След всеки тираж правим само бърз синхрон, оценка и dashboard refresh.

Препоръчано действие: Изчакай поне 5 реални резултата преди лек статистически refresh.

## Прагове

- `auto_every_draw_bg`: dataset sync + active plan result + lifecycle/dashboard refresh
- `light_statistical_refresh_after_real_results`: 5
- `recommended_statistical_refresh_after_real_results`: 10
- `manual_heavy_lab_review_after_real_results`: 20

## Политика по групи

- **След всеки реален тираж** — Автоматично / бърз режим. Винаги да се пуска
- **Лек статистически refresh** — Ръчно след 5–10 реални резултата. Не е нужен след всеки един тираж
- **Тежки лабораторни модели** — Само ръчно / лабораторно. Да не се пуска автоматично
- **Активен план** — След нов checkpoint или доказана нужда. Не сменяй плана само заради един слаб/силен тираж

## Проверки

- OK: `datasets_synced` — historical=10064, normalized=10064, canonical=10064
- OK: `latest_draw_valid` — latest=2026-07-12 [16, 29, 35, 37, 44, 47]
- OK: `runtime_hardening_active` — Step102=RUNTIME_HARDENED
- OK: `post_draw_sync_active` — Step106=POST_DRAW_SYNCED
- OK: `heavy_labs_not_default` — v67/v75 са отделени от fast refresh режима.
- OK: `step107_page_wired` — Step 107 е достъпен в навигацията.
- OK: `step107_refresh_chain_wired` — Step 107 се обновява след бъдещ Add Draw fast refresh.

Step 107 не обучава модели. Той дефинира кога кое се обновява, за да няма тежко обучение след всеки единичен тираж.
