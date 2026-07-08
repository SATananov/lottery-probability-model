# R Statistical Analysis Layer

This optional layer adds statistical checks and visualizations written in base R.

It reads the project datasets and writes outputs under:

```text
reports/r/
reports/r/plots/
```

No external R packages are required.

## Run

From the project root:

```powershell
& "C:\\Program Files\\R\\R-4.6.0\\bin\\Rscript.exe" r/run_all_r_reports.R
```

Or:

```powershell
powershell -ExecutionPolicy Bypass -File tools/run_r_statistics.ps1
```
