project_root <- getwd()
data_path <- file.path(project_root, "data", "historical_draws.csv")
out_dir <- file.path(project_root, "reports", "r")
plot_dir <- file.path(out_dir, "plots")

dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(plot_dir, recursive = TRUE, showWarnings = FALSE)

draws <- read.csv(data_path, stringsAsFactors = FALSE, check.names = FALSE)
number_cols <- c("n1", "n2", "n3", "n4", "n5", "n6")

latest <- draws[nrow(draws), ]
latest_numbers <- paste(as.integer(unlist(latest[number_cols])), collapse = ", ")
number_matrix <- as.matrix(draws[number_cols])
invalid_cells <- sum(number_matrix < 1 | number_matrix > 49, na.rm = TRUE)
duplicate_rows <- sum(apply(number_matrix, 1, function(x) length(unique(x)) != length(x)))
missing_dates <- sum(is.na(draws$date) | draws$date == "")

audit <- data.frame(
  metric = c(
    "rows",
    "latest_date",
    "latest_draw_number",
    "latest_numbers",
    "invalid_number_cells",
    "rows_with_duplicate_numbers",
    "missing_date_values"
  ),
  value = as.character(c(
    nrow(draws),
    latest$date,
    ifelse("draw_number" %in% names(latest), latest$draw_number, latest$draw_no),
    latest_numbers,
    invalid_cells,
    duplicate_rows,
    missing_dates
  )),
  stringsAsFactors = FALSE
)

write.csv(audit, file.path(out_dir, "r_data_audit.csv"), row.names = FALSE, fileEncoding = "UTF-8")

draw_sums <- rowSums(number_matrix)
summary_df <- data.frame(
  date = draws$date,
  draw_number = if ("draw_number" %in% names(draws)) draws$draw_number else draws$draw_no,
  draw_sum = draw_sums
)
write.csv(summary_df, file.path(out_dir, "r_draw_sum_history.csv"), row.names = FALSE, fileEncoding = "UTF-8")

png(file.path(plot_dir, "draw_sum_distribution.png"), width = 1200, height = 700)
hist(draw_sums, breaks = 30, main = "Distribution of draw sums", xlab = "Sum of six numbers", ylab = "Draw count")
dev.off()

cat("Data audit generated.\n")
