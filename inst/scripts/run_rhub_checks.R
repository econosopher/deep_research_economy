#!/usr/bin/env Rscript

# Simple script to run rhub checks on key platforms

library(rhub)

message("Running rhub checks on Linux, Windows, and macOS...")

# Submit to rhub using the correct platform names
rhub::rhub_check(
  platforms = c(
    "linux",          # GitHub Actions ubuntu-latest
    "windows",        # GitHub Actions windows-latest  
    "macos"           # GitHub Actions macos-13 (Intel)
  )
)