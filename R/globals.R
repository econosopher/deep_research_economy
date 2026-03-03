# Silence R CMD check NOTEs for non-standard evaluation variables in dplyr
utils::globalVariables(c(
    "island_code",
    "sample_size",
    "adjustment",
    "estimated_total",
    "lower_total",
    "upper_total",
    "estimated_adjusted_total",
    "lower_adjusted_total",
    "upper_adjusted_total"
))
