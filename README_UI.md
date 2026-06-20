# Streamlit Visual App

This optional UI turns the lottery probability project into a local visual dashboard.

## Run

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Start the app:

```powershell
python -m streamlit run streamlit_app.py
```

The browser will open a local dashboard with:

- dataset audit summary;
- mathematical odds;
- combined model recommendations;
- hot, cold + gap, middle, and gap model explorer;
- historical number frequency charts;
- probability lab;
- markdown reports.

## Important note

This app does not make lottery results predictable. Every exact 6-number ticket still has the same fair jackpot odds: `1 in 13,983,816`.

The displayed confidence values are relative model scores among generated candidates, not guaranteed real-world probabilities.
