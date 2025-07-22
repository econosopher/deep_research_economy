#!/usr/bin/env Rscript

# Install rhub if needed
if (!requireNamespace("rhub", quietly = TRUE)) {
  install.packages("rhub")
}

library(rhub)

message("Running cross-platform CRAN checks using rhub v2...")
message("This will test the package on Windows, Linux, and macOS")

# Use the new rhub v2 check function
# This will check on multiple platforms automatically
rhub::rhub_check()

message("\nCheck initiated! Results will be displayed in your R console.")
message("You can also use rhub::rhub_check() interactively for more control.")