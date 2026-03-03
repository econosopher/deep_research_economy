Release summary for 0.2.0
=========================

Changes
- Align endpoints and params to API spec (metrics/{interval}, from/to semantics, metrics filter)
- Validation for island code, interval, and 7-day date range
- Improved error messages; optional OAuth bearer token; base URL override
- S3 classes for returns; README and metadata updates

Test environments
- local macOS (arm64), R 4.2.2: R CMD check --as-cran
- Additional cross-platform checks will be run via rhub

R CMD check results
- 0 errors | 0 warnings | 1 note
- Note: “unable to verify current time” (benign, clock check)

Reverse dependencies
- None

Additional notes
- API docs included under inst/extdata

