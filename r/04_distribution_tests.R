project_root <- getwd()
data_path <- file.path(project_root, "data", "historical_draws.csv")
out_dir <- file.path(project_root, "reports", "r")
plot_dir <- file.path(out_dir, "plots")

dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(plot_dir, recursive = TRUE, showWarnings = FALSE)

draws <- read.csv(data_path, stringsAsFactors = FALSE, check.names = FALSE)
number_cols <- c("n1", "n2", "n3", "n4", "n5", "n6")
number_matrix <- as.matrix(draws[number_cols])
numbers <- as.integer(unlist(draws[number_cols], use.names = FALSE))
frequency <- table(factor(numbers, levels = 1:49))
chi <- suppressWarnings(chisq.test(as.numeric(frequency), p = rep(1 / 49, 49)))

draw_sum <- rowSums(number_matrix)
odd_count <- apply(number_matrix, 1, function(row) sum(as.integer(row) %% 2 == 1))
even_count <- 6 - odd_count
low_count <- apply(number_matrix, 1, function(row) sum(as.integer(row) <= 24))
high_count <- 6 - low_count
spread <- apply(number_matrix, 1, function(row) max(as.integer(row)) - min(as.integer(row)))

patterns <- data.frame(
  date = draws$date,
  draw_number = if ("draw_number" %in% names(draws)) draws$draw_number else draws$draw_no,
  draw_sum = draw_sum,
  odd_count = odd_count,
  even_count = even_count,
  low_count = low_count,
  high_count = high_count,
  spread = spread
)

write.csv(patterns, file.path(out_dir, "r_pattern_analysis.csv"), row.names = FALSE, fileEncoding = "UTF-8")

distribution_tests <- data.frame(
  test = c("chi_square_uniform_number_frequency", "draw_sum_mean", "draw_sum_sd", "odd_count_mean", "low_count_mean", "spread_mean"),
  statistic = c(as.numeric(chi$statistic), mean(draw_sum), sd(draw_sum), mean(odd_count), mean(low_count), mean(spread)),
  p_value = c(chi$p.value, NA, NA, NA, NA, NA),
  note = c("Chi-square test against uniform number frequency.", "Average sum of six numbers.", "Standard deviation of draw sums.", "Average odd count.", "Average low count where low <= 24.", "Average spread between max and min number."),
  stringsAsFactors = FALSE
)
write.csv(distribution_tests, file.path(out_dir, "r_distribution_tests.csv"), row.names = FALSE, fileEncoding = "UTF-8")

png(file.path(plot_dir, "odd_count_distribution.png"), width = 900, height = 600)
barplot(table(odd_count), main = "Odd count distribution", xlab = "Odd numbers in draw", ylab = "Draw count")
dev.off()

png(file.path(plot_dir, "low_count_distribution.png"), width = 900, height = 600)
barplot(table(low_count), main = "Low count distribution", xlab = "Low numbers in draw", ylab = "Draw count")
dev.off()

cat("Distribution tests generated.\n")
