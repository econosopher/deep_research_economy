#' Estimate Fortnite DAU from a random island sample
#'
#' This function estimates daily active users (DAU) using a random sample of
#' islands from the Fortnite Data API. The estimate is based on island-level
#' `uniquePlayers` and includes a confidence interval that can be tuned with
#' `confidence_level`.
#'
#' Important: this is an estimator, not an official platform DAU metric.
#' Island-level unique players are not de-duplicated across islands. Use
#' `overlap_adjustment` (> 1) to approximate cross-island player overlap when
#' converting to a platform-level DAU estimate.
#'
#' @param date Date to estimate DAU for. Defaults to yesterday.
#' @param sample_size Number of islands to sample from the frame.
#' @param confidence_level Confidence level for the interval (e.g., 0.9, 0.95, 0.99).
#'   Defaults to `getOption("fortniteR.confidence_level", 0.95)`.
#' @param max_pages Maximum number of pages to pull for the sampling frame.
#' @param page_size Number of islands per page for the sampling frame.
#' @param overlap_adjustment Divide the island-level estimate by this value to
#'   approximate platform-level DAU. Set to 1 for no adjustment.
#' @param na_as_zero If `TRUE`, missing/null `uniquePlayers` are treated as 0.
#' @param seed Optional random seed for reproducibility.
#' @param quiet If `FALSE`, prints progress messages.
#'
#' @return A list with:
#' \describe{
#'   \item{summary}{A one-row tibble with point estimate and confidence bounds.}
#'   \item{sample}{A tibble with sampled islands and per-island values used.}
#' }
#' @export
#'
#' @examples
#' \dontrun{
#' est <- estimate_fortnite_dau(
#'   date = Sys.Date() - 1,
#'   sample_size = 100,
#'   confidence_level = getOption("fortniteR.confidence_level", 0.95),
#'   overlap_adjustment = 1.4,
#'   seed = 42
#' )
#'
#' est$summary
#' }
estimate_fortnite_dau <- function(
  date = Sys.Date() - 1,
  sample_size = 100,
  confidence_level = getOption("fortniteR.confidence_level", 0.95),
  max_pages = 20,
  page_size = 100,
  overlap_adjustment = 1,
  na_as_zero = TRUE,
  seed = NULL,
  quiet = FALSE
) {
  if (is.character(date)) {
    date <- as.Date(date)
  }
  if (!inherits(date, "Date") || is.na(date)) {
    stop("`date` must be a valid Date or date string (YYYY-MM-DD).", call. = FALSE)
  }
  if (date > as.Date(Sys.time(), tz = "UTC")) {
    stop("`date` cannot be in the future (UTC).", call. = FALSE)
  }
  if (!is.numeric(sample_size) || length(sample_size) != 1 || is.na(sample_size) || sample_size < 2) {
    stop("`sample_size` must be a single numeric value >= 2.", call. = FALSE)
  }
  sample_size <- as.integer(sample_size)

  if (!is.numeric(confidence_level) || length(confidence_level) != 1 ||
      is.na(confidence_level) || confidence_level <= 0 || confidence_level >= 1) {
    stop("`confidence_level` must be between 0 and 1.", call. = FALSE)
  }

  if (!is.numeric(max_pages) || length(max_pages) != 1 || is.na(max_pages) || max_pages < 1) {
    stop("`max_pages` must be a single numeric value >= 1.", call. = FALSE)
  }
  max_pages <- as.integer(max_pages)

  if (!is.numeric(page_size) || length(page_size) != 1 || is.na(page_size) || page_size < 1 || page_size > 1000) {
    stop("`page_size` must be between 1 and 1000.", call. = FALSE)
  }
  page_size <- as.integer(page_size)

  if (!is.numeric(overlap_adjustment) || length(overlap_adjustment) != 1 ||
      is.na(overlap_adjustment) || overlap_adjustment <= 0) {
    stop("`overlap_adjustment` must be a single positive number.", call. = FALSE)
  }

  if (!quiet) {
    message("Building sampling frame from islands API...")
  }

  frame <- if (isTRUE(quiet)) {
    suppressMessages(get_all_islands(max_pages = max_pages, page_size = page_size))
  } else {
    get_all_islands(max_pages = max_pages, page_size = page_size)
  }
  frame <- dplyr::distinct(frame, island_code, .keep_all = TRUE)

  frame_size <- nrow(frame)
  if (frame_size == 0) {
    stop("No islands returned for the sampling frame.", call. = FALSE)
  }
  if (frame_size == (max_pages * page_size)) {
    warning(
      "Sampling frame hit `max_pages * page_size`; the frame may be truncated and estimates may be biased.",
      call. = FALSE
    )
  }

  if (sample_size > frame_size) {
    warning(
      sprintf("`sample_size` (%d) is larger than frame size (%d); using full frame.", sample_size, frame_size),
      call. = FALSE
    )
    sample_size <- frame_size
  }
  if (sample_size < 2) {
    stop("Sampling frame is too small to compute a confidence interval (need at least 2 islands).", call. = FALSE)
  }

  if (!is.null(seed)) {
    set.seed(seed)
  }

  sample_idx <- sample.int(frame_size, size = sample_size, replace = FALSE)
  sampled <- frame[sample_idx, , drop = FALSE]

  if (!quiet) {
    message(sprintf("Fetching daily unique player metrics for %d sampled islands...", sample_size))
  }

  sampled$unique_players <- NA_real_
  sampled$request_failed <- FALSE

  for (i in seq_len(nrow(sampled))) {
    code <- sampled$island_code[[i]]

    metric_tbl <- tryCatch(
      get_island_metrics(code = code, start_date = date, end_date = date, interval = "day"),
      error = function(e) NULL
    )

    if (is.null(metric_tbl) || nrow(metric_tbl) == 0 || !("unique_players" %in% names(metric_tbl))) {
      sampled$request_failed[[i]] <- TRUE
      next
    }

    day_rows <- metric_tbl[as.Date(metric_tbl$timestamp, tz = "UTC") == date, , drop = FALSE]
    if (nrow(day_rows) == 0) {
      day_rows <- metric_tbl[1, , drop = FALSE]
    }

    sampled$unique_players[[i]] <- as.numeric(day_rows$unique_players[[1]])

    if (!quiet && (i %% 25 == 0 || i == nrow(sampled))) {
      message(sprintf("Processed %d/%d islands", i, nrow(sampled)))
    }
  }

  sampled$value_for_estimate <- sampled$unique_players
  if (isTRUE(na_as_zero)) {
    sampled$value_for_estimate[is.na(sampled$value_for_estimate)] <- 0
  }

  stats_tbl <- summarize_sample_estimate(
    sample_values = sampled$value_for_estimate,
    frame_size = frame_size,
    confidence_level = confidence_level,
    overlap_adjustment = overlap_adjustment
  )

  stats_tbl$date <- date
  stats_tbl$null_or_missing_metrics <- sum(is.na(sampled$unique_players))
  stats_tbl$request_failures <- sum(sampled$request_failed)

  stats_tbl <- dplyr::relocate(stats_tbl, date)

  return(list(
    summary = stats_tbl,
    sample = sampled
  ))
}

#' Estimate sampled Fortnite metrics over time
#'
#' Estimates one or more metrics over a daily time series using a single random
#' island sample. This reduces API stress versus re-sampling each day because
#' each sampled island is queried once for the whole date range.
#'
#' For `metric = "unique_players"`, this can be interpreted as a DAU time series
#' estimate (after optional `overlap_adjustment`).
#'
#' @param start_date Start date (inclusive). Defaults to 6 days ago.
#' @param end_date End date (inclusive). Defaults to yesterday.
#' @param metrics Character vector of metrics to estimate. Supported values:
#'   `"unique_players"`, `"plays"`, `"peak_ccu"`, `"minutes_played"`,
#'   `"average_play_time_seconds"`, `"favorites"`, `"recommendations"`,
#'   `"retention_1_day"`, `"retention_7_days"`.
#' @param sample_size Number of islands to sample from the frame.
#' @param confidence_level Confidence level for intervals. Defaults to
#'   `getOption("fortniteR.confidence_level", 0.95)`.
#' @param max_pages Maximum number of pages to pull for the sampling frame.
#' @param page_size Number of islands per page for the sampling frame.
#' @param overlap_adjustment Divide total estimates by this value to produce
#'   adjusted estimates (for DAU de-dup approximation, for example).
#' @param na_as_zero If `TRUE`, missing/null metric values are treated as 0.
#' @param seed Optional random seed for reproducibility.
#' @param quiet If `FALSE`, prints progress messages.
#'
#' @return A list with:
#' \describe{
#'   \item{summary}{A tibble with one row per `date` and `metric`.}
#'   \item{sample}{A tibble of sampled islands by date with raw metric values.}
#' }
#' @export
#'
#' @examples
#' \dontrun{
#' ts_est <- estimate_fortnite_timeseries(
#'   start_date = Sys.Date() - 6,
#'   end_date = Sys.Date() - 1,
#'   metrics = c("unique_players", "plays"),
#'   sample_size = 150,
#'   confidence_level = 0.95,
#'   overlap_adjustment = 1.4,
#'   seed = 42
#' )
#'
#' ts_est$summary
#' }
estimate_fortnite_timeseries <- function(
  start_date = Sys.Date() - 6,
  end_date = Sys.Date() - 1,
  metrics = c("unique_players"),
  sample_size = 100,
  confidence_level = getOption("fortniteR.confidence_level", 0.95),
  max_pages = 20,
  page_size = 100,
  overlap_adjustment = 1,
  na_as_zero = TRUE,
  seed = NULL,
  quiet = FALSE
) {
  if (is.character(start_date)) {
    start_date <- as.Date(start_date)
  }
  if (is.character(end_date)) {
    end_date <- as.Date(end_date)
  }
  if (!inherits(start_date, "Date") || is.na(start_date)) {
    stop("`start_date` must be a valid Date or date string (YYYY-MM-DD).", call. = FALSE)
  }
  if (!inherits(end_date, "Date") || is.na(end_date)) {
    stop("`end_date` must be a valid Date or date string (YYYY-MM-DD).", call. = FALSE)
  }
  if (end_date < start_date) {
    stop("`end_date` must be on or after `start_date`.", call. = FALSE)
  }

  today_utc <- as.Date(Sys.time(), tz = "UTC")
  if (end_date > today_utc) {
    stop("`end_date` cannot be in the future (UTC).", call. = FALSE)
  }

  # API documentation currently limits historical data to the latest 7 days.
  n_days <- as.integer(end_date - start_date) + 1
  if (n_days > 7) {
    stop("Date range too wide. Use at most 7 days to match API historical limits.", call. = FALSE)
  }

  if (!is.character(metrics) || length(metrics) < 1) {
    stop("`metrics` must be a non-empty character vector.", call. = FALSE)
  }
  metrics <- unique(metrics)
  allowed_metrics <- c(
    "unique_players",
    "plays",
    "peak_ccu",
    "minutes_played",
    "average_play_time_seconds",
    "favorites",
    "recommendations",
    "retention_1_day",
    "retention_7_days"
  )
  invalid_metrics <- setdiff(metrics, allowed_metrics)
  if (length(invalid_metrics) > 0) {
    stop(
      sprintf(
        "Unsupported metric(s): %s. Allowed metrics: %s",
        paste(invalid_metrics, collapse = ", "),
        paste(allowed_metrics, collapse = ", ")
      ),
      call. = FALSE
    )
  }

  if (!is.numeric(sample_size) || length(sample_size) != 1 || is.na(sample_size) || sample_size < 2) {
    stop("`sample_size` must be a single numeric value >= 2.", call. = FALSE)
  }
  sample_size <- as.integer(sample_size)

  if (!is.numeric(confidence_level) || length(confidence_level) != 1 ||
      is.na(confidence_level) || confidence_level <= 0 || confidence_level >= 1) {
    stop("`confidence_level` must be between 0 and 1.", call. = FALSE)
  }

  if (!is.numeric(max_pages) || length(max_pages) != 1 || is.na(max_pages) || max_pages < 1) {
    stop("`max_pages` must be a single numeric value >= 1.", call. = FALSE)
  }
  max_pages <- as.integer(max_pages)

  if (!is.numeric(page_size) || length(page_size) != 1 || is.na(page_size) || page_size < 1 || page_size > 1000) {
    stop("`page_size` must be between 1 and 1000.", call. = FALSE)
  }
  page_size <- as.integer(page_size)

  if (!is.numeric(overlap_adjustment) || length(overlap_adjustment) != 1 ||
      is.na(overlap_adjustment) || overlap_adjustment <= 0) {
    stop("`overlap_adjustment` must be a single positive number.", call. = FALSE)
  }

  if (!quiet) {
    message("Building sampling frame from islands API...")
  }

  frame <- if (isTRUE(quiet)) {
    suppressMessages(get_all_islands(max_pages = max_pages, page_size = page_size))
  } else {
    get_all_islands(max_pages = max_pages, page_size = page_size)
  }
  frame <- dplyr::distinct(frame, island_code, .keep_all = TRUE)

  frame_size <- nrow(frame)
  if (frame_size == 0) {
    stop("No islands returned for the sampling frame.", call. = FALSE)
  }
  if (frame_size == (max_pages * page_size)) {
    warning(
      "Sampling frame hit `max_pages * page_size`; the frame may be truncated and estimates may be biased.",
      call. = FALSE
    )
  }

  if (sample_size > frame_size) {
    warning(
      sprintf("`sample_size` (%d) is larger than frame size (%d); using full frame.", sample_size, frame_size),
      call. = FALSE
    )
    sample_size <- frame_size
  }
  if (sample_size < 2) {
    stop("Sampling frame is too small to compute a confidence interval (need at least 2 islands).", call. = FALSE)
  }

  if (!is.null(seed)) {
    set.seed(seed)
  }

  sample_idx <- sample.int(frame_size, size = sample_size, replace = FALSE)
  sampled <- frame[sample_idx, , drop = FALSE]

  if (!quiet) {
    message(sprintf(
      "Fetching daily metrics for %d sampled islands across %d day(s)...",
      sample_size, n_days
    ))
  }

  sampled_rows <- list()
  island_status <- tibble::tibble(
    island_code = sampled$island_code,
    request_failed = FALSE
  )

  for (i in seq_len(nrow(sampled))) {
    code <- sampled$island_code[[i]]

    metric_tbl <- tryCatch(
      get_island_metrics(code = code, start_date = start_date, end_date = end_date, interval = "day"),
      error = function(e) NULL
    )

    if (is.null(metric_tbl) || nrow(metric_tbl) == 0) {
      island_status$request_failed[[i]] <- TRUE
      next
    }

    available_metrics <- intersect(metrics, names(metric_tbl))
    if (length(available_metrics) == 0) {
      island_status$request_failed[[i]] <- TRUE
      next
    }

    metric_rows <- metric_tbl[, c("timestamp", available_metrics), drop = FALSE]
    metric_rows$date <- as.Date(metric_rows$timestamp, tz = "UTC")
    metric_rows$island_code <- code
    metric_rows <- metric_rows[metric_rows$date >= start_date & metric_rows$date <= end_date, , drop = FALSE]

    if (nrow(metric_rows) == 0) {
      island_status$request_failed[[i]] <- TRUE
      next
    }

    metric_rows$timestamp <- NULL
    sampled_rows[[length(sampled_rows) + 1]] <- metric_rows

    if (!quiet && (i %% 25 == 0 || i == nrow(sampled))) {
      message(sprintf("Processed %d/%d islands", i, nrow(sampled)))
    }
  }

  sampled_metrics <- if (length(sampled_rows) > 0) {
    dplyr::bind_rows(sampled_rows)
  } else {
    tibble::tibble(island_code = character(0), date = as.Date(character(0)))
  }

  date_seq <- seq(start_date, end_date, by = "day")
  sample_grid <- tibble::as_tibble(expand.grid(
    island_code = sampled$island_code,
    date = date_seq,
    KEEP.OUT.ATTRS = FALSE,
    stringsAsFactors = FALSE
  ))
  sample_grid$date <- as.Date(sample_grid$date)

  sample_ts <- dplyr::left_join(sample_grid, sampled_metrics, by = c("island_code", "date"))
  sample_ts <- dplyr::left_join(sample_ts, island_status, by = "island_code")

  summary_rows <- list()
  for (metric in metrics) {
    if (!(metric %in% names(sample_ts))) {
      next
    }

    for (day in date_seq) {
      day_date <- as.Date(day, origin = "1970-01-01")
      day_values <- sample_ts[sample_ts$date == day_date, metric, drop = TRUE]
      if (isTRUE(na_as_zero)) {
        day_values[is.na(day_values)] <- 0
      }

      non_missing_n <- sum(!is.na(day_values))
      if (non_missing_n < 2) {
        summary_rows[[length(summary_rows) + 1]] <- tibble::tibble(
          date = day_date,
          metric = metric,
          frame_size = frame_size,
          sample_size = non_missing_n,
          confidence_level = confidence_level,
          adjustment = overlap_adjustment,
          estimated_total = NA_real_,
          lower_total = NA_real_,
          upper_total = NA_real_,
          estimated_adjusted_total = NA_real_,
          lower_adjusted_total = NA_real_,
          upper_adjusted_total = NA_real_,
          null_or_missing_metrics = sum(is.na(sample_ts[sample_ts$date == day_date, metric, drop = TRUE])),
          request_failures = sum(sample_ts$request_failed[sample_ts$date == day_date], na.rm = TRUE)
        )
        next
      }

      summary_row <- summarize_total_estimate(
        sample_values = day_values,
        frame_size = frame_size,
        confidence_level = confidence_level,
        adjustment = overlap_adjustment
      )

      summary_row$date <- day_date
      summary_row$metric <- metric
      summary_row$null_or_missing_metrics <- sum(is.na(sample_ts[sample_ts$date == day_date, metric, drop = TRUE]))
      summary_row$request_failures <- sum(sample_ts$request_failed[sample_ts$date == day_date], na.rm = TRUE)
      summary_row <- dplyr::relocate(summary_row, date, metric)

      summary_rows[[length(summary_rows) + 1]] <- summary_row
    }
  }

  summary_tbl <- if (length(summary_rows) > 0) {
    dplyr::bind_rows(summary_rows) |>
      dplyr::arrange(date, metric)
  } else {
    tibble::tibble(
      date = as.Date(character(0)),
      metric = character(0)
    )
  }

  return(list(
    summary = summary_tbl,
    sample = sample_ts
  ))
}

#' Summarize sampled total estimate from sample values
#' @noRd
summarize_total_estimate <- function(
  sample_values,
  frame_size,
  confidence_level = getOption("fortniteR.confidence_level", 0.95),
  adjustment = 1
) {
  observed <- sample_values[!is.na(sample_values)]
  n <- length(observed)

  if (n < 2) {
    stop("Need at least 2 non-missing sampled values to compute a confidence interval.", call. = FALSE)
  }
  if (!is.numeric(frame_size) || length(frame_size) != 1 || is.na(frame_size) || frame_size < n) {
    stop("`frame_size` must be a numeric scalar >= number of observed sample values.", call. = FALSE)
  }
  if (!is.numeric(confidence_level) || length(confidence_level) != 1 ||
      is.na(confidence_level) || confidence_level <= 0 || confidence_level >= 1) {
    stop("`confidence_level` must be between 0 and 1.", call. = FALSE)
  }
  if (!is.numeric(adjustment) || length(adjustment) != 1 ||
      is.na(adjustment) || adjustment <= 0) {
    stop("`adjustment` must be a single positive number.", call. = FALSE)
  }

  sample_mean <- mean(observed)
  sample_sd <- stats::sd(observed)

  fpc <- 1
  if (frame_size > 1 && n < frame_size) {
    fpc <- sqrt((frame_size - n) / (frame_size - 1))
  }

  se <- if (is.na(sample_sd)) 0 else (sample_sd / sqrt(n)) * fpc
  alpha <- 1 - confidence_level
  t_critical <- stats::qt(1 - alpha / 2, df = n - 1)
  margin <- t_critical * se

  lower_mean <- max(0, sample_mean - margin)
  upper_mean <- max(0, sample_mean + margin)

  estimated_total <- sample_mean * frame_size
  lower_total <- lower_mean * frame_size
  upper_total <- upper_mean * frame_size

  estimated_adjusted_total <- estimated_total / adjustment
  lower_adjusted_total <- lower_total / adjustment
  upper_adjusted_total <- upper_total / adjustment

  tibble::tibble(
    frame_size = frame_size,
    sample_size = n,
    confidence_level = confidence_level,
    adjustment = adjustment,
    estimated_total = estimated_total,
    lower_total = lower_total,
    upper_total = upper_total,
    estimated_adjusted_total = estimated_adjusted_total,
    lower_adjusted_total = lower_adjusted_total,
    upper_adjusted_total = upper_adjusted_total
  )
}

#' Summarize DAU estimate from sample values
#' @noRd
summarize_sample_estimate <- function(
  sample_values,
  frame_size,
  confidence_level = getOption("fortniteR.confidence_level", 0.95),
  overlap_adjustment = 1
) {
  out <- summarize_total_estimate(
    sample_values = sample_values,
    frame_size = frame_size,
    confidence_level = confidence_level,
    adjustment = overlap_adjustment
  )

  dplyr::transmute(
    out,
    frame_size = frame_size,
    sample_size = sample_size,
    confidence_level = confidence_level,
    overlap_adjustment = adjustment,
    estimated_island_dau = estimated_total,
    lower_island_dau = lower_total,
    upper_island_dau = upper_total,
    estimated_platform_dau = estimated_adjusted_total,
    lower_platform_dau = lower_adjusted_total,
    upper_platform_dau = upper_adjusted_total
  )
}
