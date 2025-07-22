# Fortnite Ecosystem API v1.0.0

## Overview

<b>A public API to retrieve a list of Fortnite islands and their corresponding engagement metrics.</b>
<br>
<br>
<br>
Usage Notes / Limitations:
* Historical data is limited to 7 days
* Only data for public and discoverable Fortnite islands are available.
* Islands need at least 5 unique players for the specified time interval for data to appear—otherwise, you'll get a null value.
* Favorites and recommendations are not supported for some Epic-made games, so these fields will return 0.

## Authentication

### Auth
**Type**: oauth2
**OAuth2 Flows**:

**Clientcredentials Flow**:
- Token URL: `https://api.epicgames.dev/epic/oauth/v1/token`


## Servers

### Server 1
**URL**: `https://api.fortnite.com/ecosystem/v1`

### Server 2
**URL**: `/ecosystem/v1`


## Endpoints

### Islands
#### `GET /islands`

Retrieves a sorted list of islands. The islands returned are sorted by initial release date in with newest releases first.


**Parameters**:
- `Unknown` (Unknown, Unknown)
- `Unknown` (Unknown, Unknown)
- `Unknown` (Unknown, Unknown)

**Responses**:
- `200`
  - Content-Type: `application/json`
    - Schema: `IslandResponse`
---
#### `GET /islands/{code}`

Retrieves metadata for an island code.


**Parameters**:
- `Unknown` (Unknown, Unknown)

**Responses**:
- `404`: The island with the specified code was not found.
  - Content-Type: `application/json`
    - Schema: `ErrorResponse`
- `200`
  - Content-Type: `application/json`
    - Schema: `IslandMetadataSummary`
---
#### `GET /islands/{code}/metrics`

Retrieves usage metrics for an island code with a bucket interval size of days.


**Parameters**:
- `Unknown` (Unknown, Unknown)
- `Unknown` (Unknown, Unknown)
- `Unknown` (Unknown, Unknown)

**Responses**:
- `400`: The input parameters were invalid.
  - Content-Type: `application/json`
    - Schema: `ErrorResponse`
- `404`: The island with the specified code was not found.
  - Content-Type: `application/json`
    - Schema: `ErrorResponse`
- `429`: Rate limit exceeded. Please try again later.
  - Content-Type: `text/plain`
    - Schema: `string`
- `200`
  - Content-Type: `application/json`
    - Schema: `IslandMetricsResponse`
---
#### `GET /islands/{code}/metrics/{interval}`

Retrieves usage metrics for an island code with buckets at the specified interval.
* Retention is only available for day intervals and will be excluded from hour and minute intervals.
* Average minutes per player is only available for day and hour intervals and will be excluded from minute intervals.


**Parameters**:
- `Unknown` (Unknown, Unknown)
- `Unknown` (Unknown, Unknown)
- `Unknown` (Unknown, Unknown)
- `Unknown` (Unknown, Unknown)
- `Unknown` (Unknown, Unknown)

**Responses**:
- `400`: The input parameters were invalid.
  - Content-Type: `application/json`
    - Schema: `ErrorResponse`
- `404`: The island with the specified code was not found.
  - Content-Type: `application/json`
    - Schema: `ErrorResponse`
- `429`: Rate limit exceeded. Please try again later.
  - Content-Type: `text/plain`
    - Schema: `string`
- `200`
  - Content-Type: `application/json`
    - Schema: `FilterableIslandMetricsResponse`
---
#### `GET /islands/{code}/metrics/{interval}/peak-ccu`

Retrieves the number of peak concurrent players playing the island.


**Parameters**:
- `Unknown` (Unknown, Unknown)
- `Unknown` (Unknown, Unknown)
- `Unknown` (Unknown, Unknown)
- `Unknown` (Unknown, Unknown)

**Responses**:
- `400`: The input parameters were invalid.
  - Content-Type: `application/json`
    - Schema: `ErrorResponse`
- `404`: The island with the specified code was not found.
  - Content-Type: `application/json`
    - Schema: `ErrorResponse`
- `429`: Rate limit exceeded. Please try again later.
  - Content-Type: `text/plain`
    - Schema: `string`
- `200`
  - Content-Type: `application/json`
    - Schema: `MetricResponse`
---
#### `GET /islands/{code}/metrics/{interval}/favorites`

Retrieves the number of times the island was added to a player's favorites during the interval.


**Parameters**:
- `Unknown` (Unknown, Unknown)
- `Unknown` (Unknown, Unknown)
- `Unknown` (Unknown, Unknown)
- `Unknown` (Unknown, Unknown)

**Responses**:
- `400`: The input parameters were invalid.
  - Content-Type: `application/json`
    - Schema: `ErrorResponse`
- `404`: The island with the specified code was not found.
  - Content-Type: `application/json`
    - Schema: `ErrorResponse`
- `429`: Rate limit exceeded. Please try again later.
  - Content-Type: `text/plain`
    - Schema: `string`
- `200`
  - Content-Type: `application/json`
    - Schema: `MetricResponse`
---
#### `GET /islands/{code}/metrics/{interval}/minutes-played`

Retrieves the total amount of time in minutes that players spent playing the island.


**Parameters**:
- `Unknown` (Unknown, Unknown)
- `Unknown` (Unknown, Unknown)
- `Unknown` (Unknown, Unknown)
- `Unknown` (Unknown, Unknown)

**Responses**:
- `400`: The input parameters were invalid.
  - Content-Type: `application/json`
    - Schema: `ErrorResponse`
- `404`: The island with the specified code was not found.
  - Content-Type: `application/json`
    - Schema: `ErrorResponse`
- `429`: Rate limit exceeded. Please try again later.
  - Content-Type: `text/plain`
    - Schema: `string`
- `200`
  - Content-Type: `application/json`
    - Schema: `MetricResponse`
---
#### `GET /islands/{code}/metrics/{interval}/average-minutes-per-player`

Retrieves the average amount of time in minutes that players spent playing the island.
Average minutes per player is only available for day intervals. Requests for Average minutes per player for hour or minute interval will result in a 404 not found response.


**Parameters**:
- `Unknown` (Unknown, Unknown)
- `Unknown` (Unknown, Unknown)
- `Unknown` (Unknown, Unknown)
- `Unknown` (Unknown, Unknown)

**Responses**:
- `400`: The input parameters were invalid.
  - Content-Type: `application/json`
    - Schema: `ErrorResponse`
- `404`: The island with the specified code was not found.
  - Content-Type: `application/json`
    - Schema: `ErrorResponse`
- `429`: Rate limit exceeded. Please try again later.
  - Content-Type: `text/plain`
    - Schema: `string`
- `200`
  - Content-Type: `application/json`
    - Schema: `MetricResponse`
---
#### `GET /islands/{code}/metrics/{interval}/recommendations`

Retrieves the number of times the island was recommended by a player.


**Parameters**:
- `Unknown` (Unknown, Unknown)
- `Unknown` (Unknown, Unknown)
- `Unknown` (Unknown, Unknown)
- `Unknown` (Unknown, Unknown)

**Responses**:
- `400`: The input parameters were invalid.
  - Content-Type: `application/json`
    - Schema: `ErrorResponse`
- `404`: The island with the specified code was not found.
  - Content-Type: `application/json`
    - Schema: `ErrorResponse`
- `429`: Rate limit exceeded. Please try again later.
  - Content-Type: `text/plain`
    - Schema: `string`
- `200`
  - Content-Type: `application/json`
    - Schema: `MetricResponse`
---
#### `GET /islands/{code}/metrics/{interval}/unique-players`

Retrieves the number of unique players playing the island in the time period.


**Parameters**:
- `Unknown` (Unknown, Unknown)
- `Unknown` (Unknown, Unknown)
- `Unknown` (Unknown, Unknown)
- `Unknown` (Unknown, Unknown)

**Responses**:
- `400`: The input parameters were invalid.
  - Content-Type: `application/json`
    - Schema: `ErrorResponse`
- `404`: The island with the specified code was not found.
  - Content-Type: `application/json`
    - Schema: `ErrorResponse`
- `429`: Rate limit exceeded. Please try again later.
  - Content-Type: `text/plain`
    - Schema: `string`
- `200`
  - Content-Type: `application/json`
    - Schema: `MetricResponse`
---
#### `GET /islands/{code}/metrics/{interval}/plays`

Retrieves the number of times players started to play an island in time period. If a player started an island session multiple times during the time period, each play is counted.


**Parameters**:
- `Unknown` (Unknown, Unknown)
- `Unknown` (Unknown, Unknown)
- `Unknown` (Unknown, Unknown)
- `Unknown` (Unknown, Unknown)

**Responses**:
- `400`: The input parameters were invalid.
  - Content-Type: `application/json`
    - Schema: `ErrorResponse`
- `404`: The island with the specified code was not found.
  - Content-Type: `application/json`
    - Schema: `ErrorResponse`
- `429`: Rate limit exceeded. Please try again later.
  - Content-Type: `text/plain`
    - Schema: `string`
- `200`
  - Content-Type: `application/json`
    - Schema: `MetricResponse`
---
#### `GET /islands/{code}/metrics/{interval}/retention`

Retrieves the number of users the island retained over the last 7 days and 1 day.
* Retention is only available for day intervals. Requests for retention for an hour or minute interval will result in a 404 not found response.


**Parameters**:
- `Unknown` (Unknown, Unknown)
- `Unknown` (Unknown, Unknown)
- `Unknown` (Unknown, Unknown)
- `Unknown` (Unknown, Unknown)

**Responses**:
- `400`: The input parameters were invalid.
  - Content-Type: `application/json`
    - Schema: `ErrorResponse`
- `404`: The island with the specified code was not found.
  - Content-Type: `application/json`
    - Schema: `ErrorResponse`
- `429`: Rate limit exceeded. Please try again later.
  - Content-Type: `text/plain`
    - Schema: `string`
- `200`
  - Content-Type: `application/json`
    - Schema: `RetentionResponse`
---


## Schemas

### ErrorResponse
**Type**: `object`

**Properties**:
- `errorCode` (string, **required**): A programmatic error code.
- `errorMessage` (string, **required**): A human readable version of the error reason.
- `uuid` (string, **required**): The unique identifier for the error event.

### IslandResponse
**Type**: `object`

**Properties**:
- `links` (PaginationLinks, **required**)
- `meta` (PaginationMetadata, **required**)
- `data` (array, **required**)

### PaginatedIslandMetadataSummary
**Type**: `object`

### IslandPaginationMetadata
**Type**: `object`

**Properties**:
- `meta` (object, **required**)

### IslandMetadataSummary
**Type**: `object`

**Properties**:
- `code` (string, **required**): The island's code.
- `creatorCode` (string): The island creator's code.
- `displayName` (string): A friendly name that is used to refer to Epic first party playlist codes. 
The display name can be used in place of the island playlist code any place in the API that takes an island code parameter.

- `title` (string, **required**): The island's title.
- `category` (string): Island category which for islands utilizing a brand will be the brand code.
- `createdIn` (string): How the island was authored.
- `tags` (array, **required**): A list of tags a creator has attributed to their island (ex: 1v1).

### IslandMetricsResponse
**Type**: `object`

**Properties**:
- `averageMinutesPerPlayer` (Metrics, **required**): The average amount of time in minutes players spent playing the island.
- `peakCCU` (Metrics, **required**): The peak number of concurrent players playing the island.
- `favorites` (Metrics, **required**): The number of times the island was added to a player's favorites.
- `minutesPlayed` (Metrics, **required**): The total amount of time in minutes players spent playing the island.
- `recommendations` (Metrics, **required**): The number of times the island was recommended by a player.
- `retention` (array): The user retention data for the island during the time period.
- `plays` (Metrics, **required**): The number of unique plays the island had during the time period. A player playing multiple times during the
time period would count as a unique play each time.

- `uniquePlayers` (Metrics, **required**): The number of unique players playing the island.

### FilterableIslandMetricsResponse
**Type**: `object`

**Properties**:
- `averageMinutesPerPlayer` (Metrics): The average amount of time in minutes players spent playing the island.
- `peakCCU` (Metrics): The peak number of concurrent players playing the island.
- `favorites` (Metrics): The number of times the island was added to a player's favorites.
- `minutesPlayed` (Metrics): The total amount of time in minutes players spent playing the island.
- `recommendations` (Metrics): The number of times the island was recommended by a player.
- `retention` (array): The user retention data for the island during the time period.
- `plays` (Metrics): The number of unique plays the island had during the time period. A player playing multiple times during the
time period would count as a unique play each time.

- `uniquePlayers` (Metrics): The number of unique players playing the island.

### MetricResponse
The metric values at each time interval for the period.


**Type**: `object`

**Properties**:
- `intervals` (array)

### Metrics
The metric values at each time interval for the period.


**Type**: `array`

### MetricValue
A metric value and the interval date/time.

**Type**: `object`

**Properties**:
- `value` (['number', 'null']): The value of the metric, a null value means no data is present for that interval.
- `timestamp` (string): The date/time of the interval.

### PaginationLinks
**Type**: `object`

**Properties**:
- `prev` (['string', 'null']): Path to the previous page of results if a previous page is available. Will be null when no previous pages are available.
- `next` (['string', 'null']): Path to the next page of results if another page is available. Will be null when no more pages available.

### PaginationMetadata
**Type**: `object`

**Properties**:
- `count` (number, **required**): The number of results being returned.
- `page` (object, **required**)

### RetentionResponse
The retention values at each time interval for the period.


**Type**: `object`

**Properties**:
- `intervals` (array)

### Retention
**Type**: `object`

**Properties**:
- `d1` (['number', 'null']): The number of players retained in from the previous day.
- `d7` (['number', 'null']): The number of players retained from the previous 7 days.
- `timestamp` (string): The date/time of the interval.



---

*Generated on 2025-07-21 20:35:34*