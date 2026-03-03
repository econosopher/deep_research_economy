FortniteR 0.2.0
----------------

- Align endpoints and query params with API spec:
  - Use `/islands/{code}/metrics/{interval}` with `from` (inclusive) and `to` (exclusive)
  - Support `metrics` filtering
  - Update islands listing to use `size`, `after`, `before`
- Add validation for island code, interval, and date ranges (<= 7 days)
- Improve error handling and messages; optional OAuth bearer token and base URL override
- Introduce S3 classes for returned data (`fortnite_islands`, `fortnite_metrics`)
- README updates and metadata (URL, BugReports)

