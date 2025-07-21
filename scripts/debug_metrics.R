# Debug script to check what metrics API returns

# Load packages using pacman
if (!require(pacman)) install.packages("pacman")
pacman::p_load(devtools, dplyr, jsonlite)

# Load the fortniteR package from current directory
devtools::load_all(".")

# Get one island
islands <- get_islands(limit = 1)
print("Island data:")
print(islands)

if (nrow(islands) > 0) {
  # Get a popular island that's more likely to have data
  code <- "7222-5238-3746"  # SIMPLE RED VS BLUE
  print(paste("Getting metrics for island:", code))
  
  # Try to get raw response
  req <- fortnite_request(paste0("islands/", code, "/metrics"))
  
  # Try a week ago to ensure data availability
  end_date <- Sys.Date() - 2
  start_date <- Sys.Date() - 7
  
  resp <- req |>
    httr2::req_url_query(
      startDate = format(start_date, "%Y-%m-%dT00:00:00Z"),
      endDate = format(end_date, "%Y-%m-%dT23:59:59Z"),
      interval = "day"
    ) |>
    httr2::req_perform() |>
    httr2::resp_body_json()
  
  print("Raw API response structure:")
  print(names(resp))
  
  if (!is.null(resp)) {
    # Pretty print the response
    print("Full response:")
    print(jsonlite::toJSON(resp, pretty = TRUE, auto_unbox = TRUE))
  }
}