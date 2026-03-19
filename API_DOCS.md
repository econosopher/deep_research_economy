# Economy Research API Documentation

REST API for generating game economy JSON structures using LLM providers.

## Base URL
```
http://localhost:5001
```

## Endpoints

### Health Check
```
GET /health
```
Returns server status and version information.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-26T10:00:00.000Z",
  "version": "1.0.0"
}
```

### Generate Research Cache
```
POST /api/research/cache
```
Creates a research cache structure for prompt building.

**Request Body:**
```json
{
  "gameName": "string",
  "depth": 1-3,
  "promptVersion": "2.0 (optional)",
  "researchBrief": "string (optional)",
  "conversionPrompt": "string (optional)",
  "responseJsonSchema": { "type": "object" }
}
```

**Response:**
```json
{
  "success": true,
  "cache": {
    "game": "string",
    "depth": 1-3,
    "timestamp": "ISO 8601",
    "prompt_version": "2.0",
    "instructions": "string",
    "research_brief": "string",
    "conversion_prompt": "string",
    "json_schema": { "type": "object" },
    "session_id": "string",
    "categories": ["string"]
  },
  "session_id": "string"
}
```

### Generate Economy JSON
```
POST /api/research/generate
```
Generates complete economy JSON using selected LLM provider.

**Request Body:**
```json
{
  "gameName": "string",
  "depth": 1-3,
  "provider": "gemini" | "claude",
  "apiKey": "string (optional)",
  "sessionId": "string (optional)",
  "promptVersion": "2.0 (optional)",
  "researchBrief": "string (optional)",
  "conversionPrompt": "string (optional)",
  "responseMimeType": "application/json (optional)",
  "responseJsonSchema": { "type": "object" }
}
```

**Response:**
```json
{
  "success": true,
  "json": {
    "inputs": [...],
    "nodes": [...],
    "edges": [...],
    "_metadata": {
      "provider": "gemini",
      "model": "gemini-2.5-flash",
      "prompt_version": "2.0"
    }
  },
  "session_id": "string"
}
```

### Validate API Key
```
POST /api/research/validate-key
```
Checks whether a Gemini API key is accepted by the configured runtime.

**Request Body:**
```json
{
  "apiKey": "string"
}
```

**Response:**
```json
{
  "valid": true,
  "http_ok": true,
  "message": "API key is valid",
  "error": null
}
```

### Get Session
```
GET /api/research/session/{session_id}
```
Retrieves stored session information.

**Response:**
```json
{
  "game": "string",
  "depth": 1-3,
  "created": "ISO 8601",
  "cache": {...},
  "economy_json": {...},
  "completed": "ISO 8601"
}
```

### Validate JSON
```
POST /api/research/validate
```
Validates economy JSON structure.

**Request Body:**
```json
{
  "json": {...} | "string"
}
```

**Response:**
```json
{
  "valid": true|false,
  "message": "string"
}
```

### List Templates
```
GET /api/templates
```
Lists available example templates.

**Response:**
```json
{
  "templates": [
    {
      "name": "string",
      "filename": "string.json"
    }
  ]
}
```

### Get Template
```
GET /api/templates/{template_name}
```
Retrieves specific template JSON.

**Response:**
```json
{
  "name": "string",
  "json": {...}
}
```

## Setup

1. Install dependencies:
```bash
cd deep_research_economy
pip install -r requirements.txt
```

2. Set API keys (optional):
```bash
export GEMINI_API_KEY="your-key"
export GEMINI_DEEP_RESEARCH_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
```

3. Start server:
```bash
python api_server.py
```

## Environment Variables

- `PORT` - Server port (default: 5000, commonly run as 5001 for the Figma plugin)
- `FLASK_ENV` - Set to "development" for debug mode
- `GEMINI_DEEP_RESEARCH_API_KEY` - Preferred Gemini API key
- `GEMINI_API_KEY` - Gemini API key
- `GOOGLE_API_KEY` - Fallback Gemini API key
- `ANTHROPIC_API_KEY` - Claude API key

Gemini key lookup precedence is:
1. `GEMINI_DEEP_RESEARCH_API_KEY`
2. `GEMINI_API_KEY`
3. `GOOGLE_API_KEY`
4. Shared env files such as `/Users/phillip/Documents/secrets/global.env`, `/Users/phillip/Documents/vibe_coding_projects/.env`, and `~/.api_keys`

## Error Responses

All endpoints return errors in format:
```json
{
  "error": "Error message"
}
```

HTTP status codes:
- 200 - Success
- 400 - Bad request
- 404 - Not found
- 500 - Server error

Credential problems are returned as `400` responses so the caller can distinguish configuration failures from server failures.
