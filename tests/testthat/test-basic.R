test_that("fortnite_request creates proper request object", {
  # Test that fortnite_request returns an httr2_request object
  req <- fortnite_request("islands")
  expect_s3_class(req, "httr2_request")
  
  # Test that base URL is correct
  expect_true(grepl("api.fortnite.com", req$url))
})

test_that("mock data structures are valid", {
  # Test mock response structure for get_islands
  mock_response <- list(
    islands = list(
      list(code = "1234-5678-9012", title = "Mock Island"),
      list(code = "2345-6789-0123", title = "Test Island")
    )
  )
  expect_type(mock_response, "list")
  expect_true("islands" %in% names(mock_response))
  
  # Test mock metadata structure
  mock_metadata <- list(
    code = "1234-5678-9012",
    title = "Mock Island",
    description = "A test island",
    tags = c("adventure", "multiplayer")
  )
  expect_type(mock_metadata, "list")
  expect_true(all(c("code", "title", "description", "tags") %in% names(mock_metadata)))
  
  # Test mock metrics structure
  mock_metrics <- tibble::tibble(
    date = as.Date(c("2024-01-01", "2024-01-02")),
    dau = c(1000, 1200),
    play_duration = c(45.5, 48.2)
  )
  expect_s3_class(mock_metrics, "tbl_df")
  expect_true(all(c("date", "dau", "play_duration") %in% names(mock_metrics)))
})