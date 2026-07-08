project_root <- getwd()
data_path <- file.path(project_root, "data", "historical_draws.csv")
out_dir <- file.path(project_root, "reports", "r")
plot_dir <- file.path(out_dir, "plots")

dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(plot_dir, recursive = TRUE, showWarnings = FALSE)

draws <- read.csv(data_path, stringsAsFactors = FALSE, check.names = FALSE)
number_cols <- c("n1", "n2", "n3", "n4", "n5", "n6")
number_matrix <- as.matrix(draws[number_cols])

pairs <- character(0)
for (i in seq_len(nrow(number_matrix))) {
  nums <- sort(as.integer(number_matrix[i, ]))
  pair_matrix <- combn(nums, 2)
  pairs <- c(pairs, apply(pair_matrix, 2, function(x) paste(x[1], x[2], sep = "-")))
}

pair_table <- sort(table(pairs), decreasing = TRUE)
pair_names <- names(pair_table)
pair_split <- do.call(rbind, strsplit(pair_names, "-"))
pair_analysis <- data.frame(
  pair_a = as.integer(pair_split[, 1]),
  pair_b = as.integer(pair_split[, 2]),
  pair = pair_names,
  frequency = as.integer(pair_table),
  stringsAsFactors = FALSE
)
write.csv(pair_analysis, file.path(out_dir, "r_pair_analysis.csv"), row.names = FALSE, fileEncoding = "UTF-8")

top <- head(pair_analysis, 25)
png(file.path(plot_dir, "top_pairs.png"), width = 1200, height = 800)
barplot(top$frequency, names.arg = top$pair, horiz = TRUE, las = 1, main = "Top repeated number pairs", xlab = "Frequency")
dev.off()

cat("Pair and pattern analysis generated.\n")
