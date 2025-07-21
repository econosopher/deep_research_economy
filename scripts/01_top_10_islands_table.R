# Generate Top 10 Islands table from Fortnite API
# This script creates a clean GT table with the top 10 islands by plays

# Load packages using pacman
if (!require(pacman)) install.packages("pacman")
pacman::p_load(devtools, dplyr, gt, scales, purrr)

# Load the fortniteR package from current directory
devtools::load_all(".")

# Helper function
`%||%` <- function(x, y) {
  if (is.null(x)) y else x
}

# Create output directory if it doesn't exist
if (!dir.exists("output")) {
  dir.create("output")
}

# Fetch islands from the API
message("Fetching Fortnite Creative islands from API...")
# The API returns islands sorted by release date (newest first)
# We'll fetch more islands and get metrics to find true top 10
all_islands <- get_islands(limit = 50)

# Get metrics for each island to find actual top performers
message("Fetching metrics for islands to determine top 10 by plays...")

# Get yesterday's date for metrics
end_date <- Sys.Date() - 1
start_date <- end_date

# Function to safely get full metrics for an island
get_island_kpis <- function(code) {
  tryCatch({
    metrics <- get_island_metrics(
      code = code,
      start_date = start_date,
      end_date = end_date,
      interval = "day"
    )
    if (nrow(metrics) > 0 && !is.null(metrics$plays)) {
      # Take the last available data point
      last_row <- nrow(metrics)
      return(list(
        plays = metrics$plays[last_row] %||% 0,
        unique_players = metrics$unique_players[last_row] %||% 0,
        avg_play_time_min = round((metrics$average_play_time_seconds[last_row] %||% 0) / 60, 1),
        retention_1d = metrics$retention_1_day[last_row] %||% NA,
        retention_7d = metrics$retention_7_days[last_row] %||% NA,
        peak_ccu = metrics$peak_ccu[last_row] %||% 0
      ))
    } else {
      return(list(
        plays = 0,
        unique_players = 0,
        avg_play_time_min = 0,
        retention_1d = NA,
        retention_7d = NA,
        peak_ccu = 0
      ))
    }
  }, error = function(e) {
    message(paste("Error fetching metrics for", code, ":", e$message))
    return(list(
      plays = 0,
      unique_players = 0,
      avg_play_time_min = 0,
      retention_1d = NA,
      retention_7d = NA,
      peak_ccu = 0
    ))
  })
}

# Get KPIs for each island
message("Fetching KPIs for each island...")
island_kpis <- purrr::map_df(
  all_islands$island_code,
  ~ get_island_kpis(.x)
)

# Combine with island data
all_islands <- bind_cols(all_islands, island_kpis)

# Sort by plays and take top 10
top_islands <- all_islands %>%
  arrange(desc(unique_players)) %>%
  head(10)

message(paste("Selected top", nrow(top_islands), "islands by plays"))

# Create a clean GT table with KPIs
gt_table <- top_islands %>%
  select(island_name, island_code, creator_name, unique_players, plays, 
         avg_play_time_min, peak_ccu, retention_1d, retention_7d, created_in) %>%
  gt() %>%
  tab_header(
    title = "Top Fortnite Creative Islands",
    subtitle = paste("Performance metrics for", 
                     format(end_date, "%B %d, %Y"))
  ) %>%
  cols_label(
    island_name = "Island Name",
    island_code = "Island Code",
    creator_name = "Creator",
    unique_players = "Unique Players",
    plays = "Plays",
    avg_play_time_min = "Avg Play Time (min)",
    peak_ccu = "Peak CCU",
    retention_1d = "D1 Retention",
    retention_7d = "D7 Retention",
    created_in = "Platform"
  ) %>%
  fmt_number(
    columns = c(plays, unique_players),
    decimals = 0,
    use_seps = TRUE
  ) %>%
  fmt_number(
    columns = avg_play_time_min,
    decimals = 1
  ) %>%
  fmt_percent(
    columns = c(retention_1d, retention_7d),
    decimals = 1
  ) %>%
  cols_width(
    island_name ~ px(250),
    island_code ~ px(120),
    creator_name ~ px(120),
    unique_players ~ px(120),
    plays ~ px(100),
    avg_play_time_min ~ px(130),
    peak_ccu ~ px(80),
    retention_1d ~ px(90),
    retention_7d ~ px(90),
    created_in ~ px(70)
  ) %>%
  tab_style(
    style = list(
      cell_fill(color = "#1e3a5f"),
      cell_text(color = "white", weight = "bold")
    ),
    locations = cells_column_labels()
  ) %>%
  tab_style(
    style = cell_fill(color = "#f0f9ff"),
    locations = cells_body(
      rows = seq(1, nrow(top_islands), 2)
    )
  ) %>%
  tab_spanner(
    label = "Engagement Metrics",
    columns = c(unique_players, plays, avg_play_time_min, peak_ccu)
  ) %>%
  tab_spanner(
    label = "Retention",
    columns = c(retention_1d, retention_7d)
  ) %>%
  cols_align(
    align = "center",
    columns = c(unique_players, plays, avg_play_time_min, peak_ccu, retention_1d, retention_7d, created_in)
  ) %>%
  tab_options(
    table.font.size = px(14),
    heading.title.font.size = px(24),
    heading.subtitle.font.size = px(16),
    column_labels.font.weight = "bold",
    table.width = pct(100)
  ) %>%
  tab_source_note(
    source_note = paste("Data from Fortnite Ecosystem API",
                        "(https://api.fortnite.com/ecosystem/v1)")
  )

# Save the table as PNG
gtsave(gt_table, "output/top_10_islands_table.png", 
       vwidth = 1400, vheight = 700)

message("Top 10 islands table saved to output/top_10_islands_table.png")

# Display the table
gt_table