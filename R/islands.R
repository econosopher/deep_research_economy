#' Get list of Fortnite Creative islands
#'
#' @param limit Maximum number of results (default: 50, max: 1000)
#' @param offset Deprecated and ignored. Kept for backward compatibility.
#' @param order_by Deprecated and ignored. Kept for backward compatibility.
#' @param order Deprecated and ignored. Kept for backward compatibility.
#' @param after Cursor for fetching results after a given island.
#' @param before Cursor for fetching results before a given island.
#'
#' @return A tibble with island data
#' @export
#'
#' @examples
#' # Example with mock response
#' mock_response <- list(
#'   islands = list(
#'     list(code = "1234-5678-9012", title = "Mock Island"),
#'     list(code = "2345-6789-0123", title = "Test Island")
#'   )
#' )
#' # In practice, this would come from the API
#' 
#' \dontrun{
#' islands <- get_islands(limit = 50)
#' islands_page_2 <- get_islands(limit = 50, after = "cursor_value")
#' }
get_islands <- function(
  limit = 50,
  offset = 0,
  order_by = "plays",
  order = "desc",
  after = NULL,
  before = NULL
) {
  # Validate and map to API parameter names.
  if (!is.numeric(limit) || length(limit) != 1 || is.na(limit)) {
    stop("`limit` must be a single numeric value.", call. = FALSE)
  }
  size <- as.integer(limit)
  if (size < 1 || size > 1000) {
    stop("`limit` must be between 1 and 1000.", call. = FALSE)
  }

  if (!is.null(after) && !is.null(before)) {
    stop("Use only one of `after` or `before` in a single request.", call. = FALSE)
  }

  if (!identical(offset, 0)) {
    warning("`offset` is no longer supported by the API and will be ignored.", call. = FALSE)
  }
  if (!identical(order_by, "plays") || !identical(order, "desc")) {
    warning("`order_by` and `order` are no longer supported by the API and will be ignored.", call. = FALSE)
  }

  # Create request
  req <- fortnite_request("islands")
  
  # Add query parameters
  resp <- req |>
    httr2::req_url_query(
      size = size,
      after = after,
      before = before
    ) |>
    httr2::req_perform() |>
    httr2::resp_body_json()
  
  # Parse results
  if (length(resp$data) == 0) {
    return(tibble::tibble())
  }
  
  islands_data <- resp$data |>
    purrr::map_df(~ {
      tibble::tibble(
        island_code = .x$code %||% NA_character_,
        island_name = .x$title %||% NA_character_,
        creator_name = .x$creatorCode %||% NA_character_,
        created_in = .x$createdIn %||% NA_character_,
        category = .x$category %||% NA_character_,
        tags = list(.x$tags %||% character(0))
      )
    })
  
  return(islands_data)
}

#' Get specific island metadata
#'
#' @param code Island code (e.g., "XXXX-XXXX-XXXX")
#'
#' @return A list with detailed island metadata
#' @export
#'
#' @examples
#' # Example with mock metadata structure
#' mock_metadata <- list(
#'   code = "1234-5678-9012",
#'   title = "Mock Island",
#'   description = "A test island",
#'   tags = c("adventure", "multiplayer")
#' )
#' # In practice, this would come from the API
#' 
#' \dontrun{
#' island <- get_island_metadata("1234-5678-9012")
#' }
get_island_metadata <- function(code) {
  # Create request
  req <- fortnite_request(paste0("islands/", code))
  
  # Make request
  resp <- req |>
    httr2::req_perform() |>
    httr2::resp_body_json()
  
  return(resp)
}

#' Get island engagement metrics
#'
#' @param code Island code
#' @param start_date Start date for metrics (Date or character)
#' @param end_date End date for metrics (Date or character)
#' @param interval Time interval ("minute", "hour", "day")
#'
#' @return A tibble with engagement metrics
#' @export
#'
#' @examples
#' # Example with mock metrics structure
#' mock_metrics <- tibble::tibble(
#'   date = as.Date(c("2024-01-01", "2024-01-02")),
#'   dau = c(1000, 1200),
#'   play_duration = c(45.5, 48.2)
#' )
#' # In practice, this would come from the API
#' 
#' \dontrun{
#' metrics <- get_island_metrics(
#'   code = "1234-5678-9012",
#'   start_date = Sys.Date() - 7,
#'   end_date = Sys.Date(),
#'   interval = "day"
#' )
#' }
get_island_metrics <- function(code, start_date, end_date, interval = "day") {
  interval <- match.arg(interval, c("day", "hour", "minute"))
  from <- normalize_api_datetime(start_date, boundary = "start")
  to <- normalize_api_datetime(end_date, boundary = "end")
  
  # Create request
  req <- fortnite_request(paste0("islands/", code, "/metrics/", interval))
  
  # Add query parameters
  resp <- req |>
    httr2::req_url_query(
      from = from,
      to = to
    ) |>
    httr2::req_perform() |>
    httr2::resp_body_json()
  
  # Parse metrics - API returns metrics organized by type, not by timestamp
  if (is.null(resp) || length(resp) == 0) {
    return(tibble::tibble())
  }
  
  # Extract timestamps from the first available metric array.
  timestamps <- extract_metric_timestamps(resp)
  
  if (length(timestamps) == 0) {
    return(tibble::tibble())
  }
  
  # Build metrics data frame
  metrics_data <- tibble::tibble(
    timestamp = as.POSIXct(timestamps)
  )
  
  # Add plays
  if (!is.null(resp$plays)) {
    metrics_data$plays <- purrr::map_dbl(resp$plays, ~ .x$value %||% NA_real_)
  }
  
  # Add unique players
  if (!is.null(resp$uniquePlayers)) {
    metrics_data$unique_players <- purrr::map_dbl(resp$uniquePlayers, ~ .x$value %||% NA_real_)
  }
  
  # Add average minutes per player (convert to seconds)
  if (!is.null(resp$averageMinutesPerPlayer)) {
    metrics_data$average_play_time_seconds <- purrr::map_dbl(
      resp$averageMinutesPerPlayer, 
      ~ (.x$value %||% NA_real_) * 60
    )
  }

  # Add peak concurrent users
  if (!is.null(resp$peakCCU)) {
    metrics_data$peak_ccu <- purrr::map_dbl(resp$peakCCU, ~ .x$value %||% NA_real_)
  }

  # Add minutes played
  if (!is.null(resp$minutesPlayed)) {
    metrics_data$minutes_played <- purrr::map_dbl(resp$minutesPlayed, ~ .x$value %||% NA_real_)
  }
  
  # Add favorites
  if (!is.null(resp$favorites)) {
    metrics_data$favorites <- purrr::map_dbl(resp$favorites, ~ .x$value %||% NA_real_)
  }
  
  # Add recommendations
  if (!is.null(resp$recommendations)) {
    metrics_data$recommendations <- purrr::map_dbl(resp$recommendations, ~ .x$value %||% NA_real_)
  }
  
  # Add retention (these come in a different format)
  if (!is.null(resp$retention)) {
    metrics_data$retention_1_day <- purrr::map_dbl(resp$retention, ~ .x$d1 %||% NA_real_)
    metrics_data$retention_7_days <- purrr::map_dbl(resp$retention, ~ .x$d7 %||% NA_real_)
  }
  
  return(metrics_data)
}

#' Get all islands with pagination support
#'
#' @param max_pages Maximum number of pages to fetch (default: 10)
#' @param page_size Number of islands per page (default: 100)
#'
#' @return A tibble with all island data
#' @export
#'
#' @examples
#' # Example showing expected output structure
#' mock_all_islands <- tibble::tibble(
#'   code = c("1234-5678-9012", "2345-6789-0123"),
#'   title = c("Island 1", "Island 2"),
#'   page_fetched = c(1, 1)
#' )
#' # In practice, this would aggregate results from multiple API pages
#' 
#' \dontrun{
#' # Get all islands (up to 1000)
#' all_islands <- get_all_islands()
#' 
#' # Get more islands
#' many_islands <- get_all_islands(max_pages = 20)
#' }
get_all_islands <- function(max_pages = 10, page_size = 100) {
  all_data <- list()
  next_cursor <- NULL
  pages_fetched <- 0
  
  message("Fetching islands data...")
  
  while (pages_fetched < max_pages) {
    # Create request
    req <- fortnite_request("islands")
    
    # Add pagination parameters
    if (!is.null(next_cursor)) {
      req <- req |> httr2::req_url_query(after = next_cursor, size = page_size)
    } else {
      req <- req |> httr2::req_url_query(size = page_size)
    }
    
    # Make request
    resp <- req |> 
      httr2::req_perform() |>
      httr2::resp_body_json()
    
    # Extract data
    if (length(resp$data) == 0) {
      break
    }
    
    # Parse this page's data
    page_data <- resp$data |>
      purrr::map_df(~ {
        tibble::tibble(
          island_code = .x$code %||% NA_character_,
          island_name = .x$title %||% NA_character_,
          creator_name = .x$creatorCode %||% NA_character_,
          created_in = .x$createdIn %||% NA_character_,
          category = .x$category %||% NA_character_,
          tags = list(.x$tags %||% character(0))
        )
      })
    
    all_data[[length(all_data) + 1]] <- page_data
    pages_fetched <- pages_fetched + 1
    
    # Check for next page
    next_cursor <- resp$meta$page$nextCursor
    if (is.null(next_cursor)) {
      break
    }
    
    message(sprintf("Fetched page %d (%d islands)...", pages_fetched, nrow(page_data)))
  }
  
  # Combine all pages
  if (length(all_data) == 0) {
    return(tibble::tibble())
  }
  
  result <- dplyr::bind_rows(all_data)
  message(sprintf("Total islands fetched: %d", nrow(result)))
  
  return(result)
}

#' Helper function to handle NULL values
#' @noRd
`%||%` <- function(x, y) {
  if (is.null(x)) y else x
}

#' Normalize date/time for API query parameters.
#' @noRd
normalize_api_datetime <- function(x, boundary = c("start", "end")) {
  boundary <- match.arg(boundary)

  if (inherits(x, "Date")) {
    if (boundary == "start") {
      return(sprintf("%sT00:00:00.000Z", format(x, "%Y-%m-%d")))
    }

    # API `to` is exclusive and must not be in the future.
    today_utc <- as.Date(Sys.time(), tz = "UTC")
    if (x >= today_utc) {
      return(format(as.POSIXct(Sys.time(), tz = "UTC"), "%Y-%m-%dT%H:%M:%SZ", tz = "UTC"))
    }

    return(sprintf("%sT00:00:00.000Z", format(x + 1, "%Y-%m-%d")))
  }

  if (inherits(x, c("POSIXct", "POSIXt"))) {
    return(format(as.POSIXct(x, tz = "UTC"), "%Y-%m-%dT%H:%M:%SZ", tz = "UTC"))
  }

  as.character(x)
}

#' Return timestamps from the first populated metric series.
#' @noRd
extract_metric_timestamps <- function(resp) {
  metric_fields <- c(
    "plays",
    "uniquePlayers",
    "averageMinutesPerPlayer",
    "peakCCU",
    "favorites",
    "minutesPlayed",
    "recommendations",
    "retention"
  )

  for (field in metric_fields) {
    values <- resp[[field]]
    if (!is.null(values) && length(values) > 0) {
      return(purrr::map_chr(values, ~ .x$timestamp %||% NA_character_))
    }
  }

  character(0)
}
