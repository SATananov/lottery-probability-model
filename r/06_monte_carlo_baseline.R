set.seed(42)

project_root <- getwd()
data_path <- file.path(project_root, "data", "historical_draws.csv")
out_dir <- file.path(project_root, "reports", "r")
plot_dir <- file.path(out_dir, "plots")

dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(plot_dir, recursive = TRUE, showWarnings = FALSE)

draws <- read.csv(data_path, stringsAsFactors = FALSE, check.names = FALSE)
number_cols <- c("n1", "n2", "n3", "n4", "n5", "n6")
n_draws <- nrow(draws)
simulations <- 100

real_numbers <- as.integer(unlist(draws[number_cols], use.names = FALSE))
real_freq <- as.integer(table(factor(real_numbers, levels = 1:49)))
sim_freq_matrix <- matrix(0, nrow = simulations, ncol = 49)

for (s in seq_len(simulations)) {
  sampled_numbers <- integer(n_draws * 6)
  pos <- 1
  for (i in seq_len(n_draws)) {
    sampled_numbers[pos:(pos + 5)] <- sample(1:49, 6, replace = FALSE)
    pos <- pos + 6
  }
  sim_freq_matrix[s, ] <- as.integer(table(factor(sampled_numbers, levels = 1:49)))
}

baseline <- data.frame(
  number = 1:49,
  real_frequency = real_freq,
  simulated_mean = colMeans(sim_freq_matrix),
  simulated_p05 = apply(sim_freq_matrix, 2, quantile, probs = 0.05),
  simulated_p95 = apply(sim_freq_matrix, 2, quantile, probs = 0.95)
)
baseline$above_p95 <- baseline$real_frequency > baseline$simulated_p95
baseline$below_p05 <- baseline$real_frequency < baseline$simulated_p05
write.csv(baseline, file.path(out_dir, "r_monte_carlo_baseline.csv"), row.names = FALSE, fileEncoding = "UTF-8")

png(file.path(plot_dir, "monte_carlo_frequency_baseline.png"), width = 1400, height = 700)
plot(baseline$number, baseline$real_frequency, type = "p", main = "Monte Carlo baseline: real vs simulated band", xlab = "Number", ylab = "Frequency")
lines(baseline$number, baseline$simulated_mean, lty = 2)
lines(baseline$number, baseline$simulated_p05, lty = 3)
lines(baseline$number, baseline$simulated_p95, lty = 3)
legend("topright", legend = c("real", "simulated mean", "5%-95% band"), lty = c(NA, 2, 3), pch = c(1, NA, NA), bty = "n")
dev.off()

cat("Monte Carlo baseline generated.\n")
