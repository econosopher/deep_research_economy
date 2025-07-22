#!/usr/bin/env Rscript

# Install required packages if needed
if (!requireNamespace("rhub", quietly = TRUE)) {
  install.packages("rhub")
}
if (!requireNamespace("rcmdcheck", quietly = TRUE)) {
  install.packages("rcmdcheck")
}

library(rhub)

message("=== Running CRAN checks for fortniteR ===\n")

# First, let's see available platforms
message("Available rhub platforms:")
platforms <- rhub::rhub_platforms()
print(platforms)

message("\n=== Running local R CMD check --as-cran ===")
# Run local check first
local_check <- rcmdcheck::rcmdcheck(args = "--as-cran", error_on = "never")
print(local_check)

message("\n=== Submitting to rhub for cross-platform testing ===")
# Run on key CRAN-like platforms
# Using the new rhub v2 syntax
rhub_results <- rhub::rhub_check(
  platforms = c(
    "ubuntu-release",    # Ubuntu with current R
    "windows-release",   # Windows with current R  
    "macos-release"      # macOS with current R
  )
)

message("\nCross-platform checks submitted!")
message("Results will appear in your console as they complete.")
message("\nFor additional platforms, you can run:")
message("  rhub::rhub_platforms()  # to see all available platforms")
message("  rhub::rhub_check(platforms = c('platform1', 'platform2'))  # to check specific platforms")