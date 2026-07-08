# Streamlit App Guide

The Streamlit app is the visual dashboard for the Lottery Probability Model 6/49 project. It is intended for local use, model review, controlled data updates, ticket-pack preparation, and report inspection.

## Start the app

From the project root:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The browser normally opens at:

```text
http://localhost:8501
```

## What to check first

Open the user menu/dashboard and confirm:

```text
Dataset rows: 10062
Latest draw: 2026-07-05 · Draw 52 · 4, 11, 21, 28, 36, 49
Ready ticket pack: 3 tickets × 4 lines = 12 combinations
Total price: 10.80 EUR
```

## Main UI areas

- User menu and dashboard status.
- Add Draw controlled workflow.
- Real ticket-pack builder.
- Model system ticket builder.
- Played-ticket journal.
- Historical analysis and prize history sections.
- Model comparison, registry, reliability, and weighting sections.
- Probability and ML laboratories.
- Reports and final plan views.

## Notes

The app displays statistical analysis and model scores only. It does not make lottery results predictable and does not change the theoretical chance of a 6/49 ticket.
