<p align="center">
  <img src="package_logo.png" width="200" alt="fortniteR logo">
</p>

# fortniteR

R client for the Fortnite Ecosystem API, providing access to island metadata and engagement metrics.

## Installation

```r
# Install from GitHub
devtools::install_github("econosopher/fortniteR")

# Or using pacman
if (!require(pacman)) install.packages("pacman")
pacman::p_load_gh("econosopher/fortniteR")
```

## Usage

**IMPORTANT**: This package uses real API data only. NO MOCK DATA is used.

The Fortnite Ecosystem API is PUBLIC and does NOT require authentication. The API documentation incorrectly mentions OAuth2, but all endpoints work without any authentication.

### Fetching Island Data

```r
library(fortniteR)

# Get list of islands
islands <- get_islands(limit = 50)

# Get all islands with pagination (up to 1000)
all_islands <- get_all_islands()

# Get specific island metadata
island_info <- get_island_metadata("XXXX-XXXX-XXXX")

# Get island metrics (plays, retention, etc.)
metrics <- get_island_metrics(
  code = "XXXX-XXXX-XXXX",
  start_date = Sys.Date() - 7,
  end_date = Sys.Date(),
  interval = "day"  # Options: "minute", "hour", "day"
)
```

### Creating Visualizations

The package includes a script to create beautiful GT tables from the API data:

```bash
# Run this script to generate the top 10 islands table
Rscript scripts/01_top_10_islands_table.R
```

### Example Output

Here's an example of a GT table generated using real data from the Fortnite Ecosystem API:

<p align="left">
  <img src="/output/top_10_islands_table.png">
</p>


*This table shows the top performing Fortnite Creative Islands ranked by unique players, displaying comprehensive engagement metrics (unique players, total plays, average play time, peak CCU) and retention data (D1 and D7 retention rates).*


## Features

- Fetch island listings with pagination
- Get detailed island metadata
- Retrieve engagement metrics (players, plays, retention, etc.)
- Support for different time intervals (day, hour, minute)
- Create beautiful GT tables with metrics
- No authentication required

## API Endpoints

- `/islands` - Returns basic island metadata (code, name, creator, platform, tags)
- `/islands/{code}` - Returns detailed metadata for a specific island
- `/islands/{code}/metrics` - Returns engagement metrics (plays, retention, etc.)

## API Limitations

- Historical metrics data limited to 7 days
- Only public/discoverable islands available
- Minimum 5 unique players required for metrics data
- Some Epic games don't support favorites/recommendations
