project_root <- getwd()
data_path <- file.path(project_root, "data", "historical_draws.csv")
out_dir <- file.path(project_root, "reports", "r")
plot_dir <- file.path(out_dir, "plots")

dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(plot_dir, recursive = TRUE, showWarnings = FALSE)

draws <- read.csv(data_path, stringsAsFactors = FALSE, check.names = FALSE)
number_cols <- c("n1", "n2", "n3", "n4", "n5", "n6")
number_matrix <- as.matrix(draws[number_cols])

rows <- lapply(1:49, function(number) {
  hit_index <- which(apply(number_matrix, 1, function(row) number %in% as.integer(row)))
  if (length(hit_index) == 0) {
    return(data.frame(number = number, appearances = 0, current_gap = NA, average_gap = NA, max_gap = NA, gap_ratio = NA))
  }
  gaps <- diff(hit_index)
  current_gap <- nrow(draws) - tail(hit_index, 1)
  average_gap <- if (length(gaps) > 0) mean(gaps) else NA
  max_gap <- if (length(gaps) > 0) max(gaps) else NA
  gap_ratio <- if (!is.na(average_gap) && average_gap > 0) current_gap / average_gap else NA
  data.frame(number = number, appearances = length(hit_index), current_gap = current_gap, average_gap = average_gap, max_gap = max_gap, gap_ratio = gap_ratio)
})

gap_stats <- do.call(rbind, rows)
gap_stats <- gap_stats[order(-gap_stats$current_gap), ]
write.csv(gap_stats, file.path(out_dir, "r_gap_statistics.csv"), row.names = FALSE, fileEncoding = "UTF-8")

top <- head(gap_stats, 15)
png(file.path(plot_dir, "largest_current_gaps.png"), width = 1100, height = 750)
barplot(top$current_gap, names.arg = top$number, horiz = TRUE, las = 1, main = "Numbers with largest current gap", xlab = "Current gap")
dev.off()

cat("Gap statistics generated.\n")
