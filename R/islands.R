#' Get list of Fortnite Creative islands
#'
#' @param limit Maximum number of results (default: 50)
#' @param offset Number of results to skip
#' @param order_by Field to order by ("plays", "lastPlayed", etc.)
#' @param order Sort order ("asc" or "desc")
#'
#' @return A tibble with island data
#' @export
#'
#' @examples
#' \dontrun{
#' islands <- get_islands(limit = 50)
#' }
get_islands <- function(limit = 50, offset = 0, order_by = "plays", order = "desc") {
  # Create request
  req <- fortnite_request("islands")
  
  # Add query parameters
  resp <- req |>
    httr2::req_url_query(
      limit = limit,
      offset = offset,
      orderBy = order_by,
      order = order
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
#' \dontrun{
#' metrics <- get_island_metrics(
#'   code = "1234-5678-9012",
#'   start_date = Sys.Date() - 7,
#'   end_date = Sys.Date(),
#'   interval = "day"
#' )
#' }
get_island_metrics <- function(code, start_date, end_date, interval = "day") {
  # Convert dates to ISO 8601 format
  if (inherits(start_date, "Date")) {
    start_date <- format(start_date, "%Y-%m-%dT00:00:00Z")
  }
  if (inherits(end_date, "Date")) {
    end_date <- format(end_date, "%Y-%m-%dT23:59:59Z")
  }
  
  # Create request
  req <- fortnite_request(paste0("islands/", code, "/metrics"))
  
  # Add query parameters
  resp <- req |>
    httr2::req_url_query(
      startDate = start_date,
      endDate = end_date,
      interval = interval
    ) |>
    httr2::req_perform() |>
    httr2::resp_body_json()
  
  # Parse metrics - API returns metrics organized by type, not by timestamp
  if (is.null(resp) || length(resp) == 0) {
    return(tibble::tibble())
  }
  
  # Extract timestamps from any metric array
  timestamps <- if (!is.null(resp$plays)) {
    purrr::map_chr(resp$plays, ~ .x$timestamp %||% NA_character_)
  } else if (!is.null(resp$uniquePlayers)) {
    purrr::map_chr(resp$uniquePlayers, ~ .x$timestamp %||% NA_character_)
  } else {
    character(0)
  }
  
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

#' Helper function to handle NULL values
#' @noRd
#' Get all islands with pagination support
#'
#' @param max_pages Maximum number of pages to fetch (default: 10)
#' @param page_size Number of islands per page (default: 100)
#'
#' @return A tibble with all island data
#' @export
#'
#' @examples
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