args <- commandArgs(trailingOnly = FALSE)
file_arg <- grep("^--file=", args, value = TRUE)

if (length(file_arg) > 0) {
  r_dir <- dirname(normalizePath(sub("^--file=", "", file_arg[1])))
} else {
  r_dir <- file.path(getwd(), "r")
}

project_root <- normalizePath(file.path(r_dir, ".."), mustWork = FALSE)
setwd(project_root)

scripts <- c(
  "01_data_audit.R",
  "02_frequency_statistics.R",
  "03_gap_statistics.R",
  "04_distribution_tests.R",
  "05_pair_and_pattern_analysis.R",
  "06_monte_carlo_baseline.R",
  "07_r_statistical_summary.R"
)

cat("Project root:", project_root, "\n")

for (script in scripts) {
  script_path <- file.path(project_root, "r", script)
  if (!file.exists(script_path)) {
    cat("Missing:", script, "\n")
    next
  }
  cat("\nRunning:", script, "\n")
  source(script_path, local = new.env())
}

cat("\nAll base R statistical reports generated.\n")
