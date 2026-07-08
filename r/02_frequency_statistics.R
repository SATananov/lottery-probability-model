project_root <- getwd()
data_path <- file.path(project_root, "data", "historical_draws.csv")
out_dir <- file.path(project_root, "reports", "r")
plot_dir <- file.path(out_dir, "plots")

dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(plot_dir, recursive = TRUE, showWarnings = FALSE)

draws <- read.csv(data_path, stringsAsFactors = FALSE, check.names = FALSE)
number_cols <- c("n1", "n2", "n3", "n4", "n5", "n6")
numbers <- as.integer(unlist(draws[number_cols], use.names = FALSE))
frequency_values <- as.integer(table(factor(numbers, levels = 1:49)))
expected_uniform_count <- sum(frequency_values) / 49

frequency <- data.frame(
  number = 1:49,
  frequency = frequency_values,
  frequency_share = frequency_values / sum(frequency_values),
  expected_uniform_count = expected_uniform_count,
  diff_from_expected = frequency_values - expected_uniform_count
)
frequency <- frequency[order(-frequency$frequency, frequency$number), ]
frequency$rank_desc <- seq_len(nrow(frequency))

write.csv(frequency, file.path(out_dir, "r_frequency_statistics.csv"), row.names = FALSE, fileEncoding = "UTF-8")
write.csv(head(frequency[order(-frequency$frequency), ], 10), file.path(out_dir, "r_hot_numbers.csv"), row.names = FALSE, fileEncoding = "UTF-8")
write.csv(head(frequency[order(frequency$frequency), ], 10), file.path(out_dir, "r_cold_numbers.csv"), row.names = FALSE, fileEncoding = "UTF-8")

plot_df <- frequency[order(frequency$number), ]
png(file.path(plot_dir, "number_frequency.png"), width = 1400, height = 700)
barplot(plot_df$frequency, names.arg = plot_df$number, main = "Frequency of lottery numbers", xlab = "Number", ylab = "Frequency")
abline(h = expected_uniform_count, lty = 2)
dev.off()

cat("Frequency statistics generated.\n")
