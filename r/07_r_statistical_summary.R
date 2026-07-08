project_root <- getwd()
out_dir <- file.path(project_root, "reports", "r")
summary_path <- file.path(out_dir, "r_statistical_summary.md")

read_csv_safe <- function(path) {
  if (!file.exists(path)) return(data.frame())
  read.csv(path, stringsAsFactors = FALSE, check.names = FALSE)
}

audit <- read_csv_safe(file.path(out_dir, "r_data_audit.csv"))
frequency <- read_csv_safe(file.path(out_dir, "r_frequency_statistics.csv"))
gap_stats <- read_csv_safe(file.path(out_dir, "r_gap_statistics.csv"))
tests <- read_csv_safe(file.path(out_dir, "r_distribution_tests.csv"))
baseline <- read_csv_safe(file.path(out_dir, "r_monte_carlo_baseline.csv"))

get_audit <- function(metric) {
  value <- audit$value[audit$metric == metric]
  if (length(value) == 0) return("n/a")
  as.character(value[1])
}

rows <- get_audit("rows")
latest_date <- get_audit("latest_date")
latest_numbers <- get_audit("latest_numbers")

top_hot <- head(frequency[order(-frequency$frequency), "number"], 10)
top_gap <- head(gap_stats[order(-gap_stats$current_gap), "number"], 10)
chi_row <- tests[tests$test == "chi_square_uniform_number_frequency", ]

above_band <- baseline[baseline$above_p95 == TRUE, "number"]
below_band <- baseline[baseline$below_p05 == TRUE, "number"]

lines <- c(
  "# R Statistical Summary",
  "",
  paste0("Dataset rows: ", rows),
  paste0("Latest draw date: ", latest_date),
  paste0("Latest numbers: ", latest_numbers),
  "",
  "## Frequency",
  "",
  paste0("Top frequent numbers: ", paste(top_hot, collapse = ", ")),
  "",
  "## Gap analysis",
  "",
  paste0("Largest current gap numbers: ", paste(top_gap, collapse = ", ")),
  "",
  "## Distribution test",
  "",
  paste0("Chi-square statistic: ", if (nrow(chi_row) > 0) round(chi_row$statistic[1], 4) else "n/a"),
  paste0("Chi-square p-value: ", if (nrow(chi_row) > 0) signif(chi_row$p_value[1], 4) else "n/a"),
  "",
  "## Monte Carlo baseline",
  "",
  paste0("Numbers above simulated 95% band: ", if (length(above_band) > 0) paste(above_band, collapse = ", ") else "none"),
  paste0("Numbers below simulated 5% band: ", if (length(below_band) > 0) paste(below_band, collapse = ", ") else "none"),
  "",
  "## Interpretation",
  "",
  "The R layer provides additional statistical visibility over the lottery dataset.",
  "It should be used for validation, diagnostics, visualization, and model review.",
  "It does not guarantee future lottery outcomes."
)

writeLines(lines, summary_path, useBytes = TRUE)

cat("R statistical summary generated.\n")
