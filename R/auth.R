#' Create request for Fortnite Ecosystem API
#'
#' @param endpoint API endpoint (appended to base URL)
#'
#' @return An httr2 request object
#' @export
#'
#' @examples
#' # Example showing request structure
#' endpoint <- "islands"
#' # This would construct an httr2 request object
#' 
#' \dontrun{
#' req <- fortnite_request("islands")
#' }
fortnite_request <- function(endpoint = "") {
  # Create base request
  req <- httr2::request("https://api.fortnite.com/ecosystem/v1")
  
  # Add endpoint if provided
  if (endpoint != "") {
    req <- req |> httr2::req_url_path_append(endpoint)
  }
  
  # Add standard headers and options
  req <- req |>
    httr2::req_headers(
      "Accept" = "application/json",
      "User-Agent" = "fortniteR/0.1.0"
    ) |>
    httr2::req_retry(max_tries = 3) |>
    httr2::req_timeout(30) |>
    httr2::req_error(body = function(resp) {
      body <- httr2::resp_body_json(resp, check_type = FALSE)
      if (!is.null(body$error)) {
        paste0(body$error$code, ": ", body$error$message)
      } else if (!is.null(body$message)) {
        body$message
      } else {
        paste0("API error: ", httr2::resp_status(resp))
      }
    })
  
  return(req)
}