test_that("summarize_sample_estimate computes expected point estimate", {
  vals <- c(10, 20, 30, 40, 50)

  out <- FortniteR:::summarize_sample_estimate(
    sample_values = vals,
    frame_size = 100,
    confidence_level = 0.95,
    overlap_adjustment = 2
  )

  expect_s3_class(out, "tbl_df")
  expect_equal(out$sample_size, 5)
  expect_equal(out$estimated_island_dau, mean(vals) * 100)
  expect_equal(out$estimated_platform_dau, (mean(vals) * 100) / 2)
  expect_gte(out$upper_platform_dau, out$lower_platform_dau)
})

test_that("summarize_sample_estimate validates inputs", {
  expect_error(
    FortniteR:::summarize_sample_estimate(c(1, 2), frame_size = 2, confidence_level = 1),
    "confidence_level"
  )

  expect_error(
    FortniteR:::summarize_sample_estimate(c(1, 2), frame_size = 2, overlap_adjustment = 0),
    "adjustment"
  )

  expect_error(
    FortniteR:::summarize_sample_estimate(c(1), frame_size = 1),
    "at least 2"
  )
})

test_that("estimate_fortnite_dau rejects future dates before API calls", {
  expect_error(
    estimate_fortnite_dau(date = Sys.Date() + 1, quiet = TRUE),
    "future"
  )
})

test_that("summarize_total_estimate computes expected point estimate", {
  vals <- c(5, 15, 25, 35)

  out <- FortniteR:::summarize_total_estimate(
    sample_values = vals,
    frame_size = 10,
    confidence_level = 0.9,
    adjustment = 2
  )

  expect_s3_class(out, "tbl_df")
  expect_equal(out$sample_size, 4)
  expect_equal(out$estimated_total, mean(vals) * 10)
  expect_equal(out$estimated_adjusted_total, (mean(vals) * 10) / 2)
})

test_that("confidence defaults can be controlled via option", {
  old <- options(FortniteR.confidence_level = 0.9)
  on.exit(options(old), add = TRUE)

  out <- FortniteR:::summarize_total_estimate(
    sample_values = c(1, 2, 3),
    frame_size = 3
  )
  expect_equal(out$confidence_level, 0.9)
})

test_that("estimate_fortnite_timeseries validates range and metrics before API calls", {
  expect_error(
    estimate_fortnite_timeseries(
      start_date = Sys.Date() - 10,
      end_date = Sys.Date() - 1,
      metrics = "unique_players",
      quiet = TRUE
    ),
    "at most 7 days"
  )

  expect_error(
    estimate_fortnite_timeseries(
      start_date = Sys.Date() - 2,
      end_date = Sys.Date() - 1,
      metrics = "not_a_metric",
      quiet = TRUE
    ),
    "Unsupported metric"
  )
})
