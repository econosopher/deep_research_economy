# Flask API Architecture & Linking

## Overview

The Flask REST API serves as a bridge between the Figma plugin (TypeScript/JavaScript) and the deep research economy system (Python). This architecture enables cross-language communication and leverages Python's LLM libraries while maintaining a clean separation of concerns.

## Architecture Diagram

```
┌─────────────────────┐         HTTP/REST          ┌──────────────────────┐
│   Figma Plugin      │ ◄─────────────────────────► │   Flask API Server   │
│   (TypeScript)      │                             │   (Python)           │
│                     │                             │                      │
│ - research-bridge.ts│                             │ - api_server.py      │
│ - UI components     │                             │ - economy_builder.py │
│ - JSON validation   │                             │ - LLM providers      │
└─────────────────────┘                             └──────────────────────┘
```

## How the Linking Works

### 1. Client Side (Figma Plugin)
The plugin communicates with the Flask server through the `research-bridge.ts` module:

```typescript
// research-bridge.ts
export async function generateResearchCache(request: ResearchRequest) {
  const response = await fetch('http://localhost:5001/api/research/cache', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request)
  });
  // Handle response...
}
```

### 2. Server Side (Flask API)
Flask receives and processes requests, delegating to appropriate Python modules:

```python
@app.route('/api/research/generate', methods=['POST'])
def generate_economy():
    data = request.json
    
    # Extract parameters
    game_name = data.get('gameName')
    depth = data.get('depth')
    provider_name = data.get('provider')
    
    # Initialize economy builder with LLM provider
    builder = EconomyJSONBuilder(
        provider_name=provider_name,
        api_key=api_key
    )
    
    # Generate economy JSON using Python LLM libraries
    economy_json = builder.provider.generate_economy_json(
        markdown_content, 
        game_name
    )
    
    return jsonify({'success': True, 'json': economy_json})
```

### 3. Cross-Origin Resource Sharing (CORS)
CORS is configured to allow the Figma plugin to communicate with the Flask server:

```python
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=['*'])  # Allow all origins for development
```

This enables:
- Cross-origin requests from the Figma plugin
- Different ports (plugin on Figma's internal port, API on 5001)
- Local development without security restrictions

### 4. Request/Response Flow

1. **User Action**: User clicks "Generate" in Figma plugin
2. **Client Request**: TypeScript sends HTTP POST to Flask
3. **Server Processing**: Flask routes to appropriate handler
4. **Python Logic**: Economy builder uses LLM providers
5. **JSON Response**: Flask returns JSON result
6. **Client Update**: Plugin updates UI with result

## Key Components

### Flask Routes

| Route | Method | Purpose |
|-------|--------|---------|
| `/health` | GET | Health check & status |
| `/api/research/cache` | POST | Generate research cache |
| `/api/research/generate` | POST | Generate economy JSON |
| `/api/research/validate` | POST | Validate JSON structure |
| `/api/research/session/{id}` | GET | Retrieve session data |
| `/api/templates` | GET | List available templates |

### Data Flow

1. **Input Processing**
   - Figma plugin collects user input (game name, depth)
   - TypeScript validates and formats data
   - HTTP POST sends JSON payload

2. **Server Processing**
   - Flask deserializes JSON request
   - Python processes with appropriate logic
   - LLM providers generate content when needed

3. **Response Handling**
   - Flask serializes Python objects to JSON
   - HTTP response includes status codes
   - TypeScript handles success/error cases

### Session Management

The Flask server maintains session state in memory:

```python
research_sessions = {}  # In-memory storage

@app.route('/api/research/cache', methods=['POST'])
def generate_cache():
    # Generate session ID
    session_id = f"{game_name}_{timestamp}"
    
    # Store in session
    research_sessions[session_id] = {
        'game': game_name,
        'cache': cache,
        'created': datetime.now()
    }
    
    return jsonify({'session_id': session_id})
```

**Note**: For production, use Redis or a database for session storage.

## Error Handling

### Client Side
```typescript
try {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }
} catch (error) {
  // Fallback to local generation
  return generateLocalFallback();
}
```

### Server Side
```python
try:
    # Process request
    result = process_request(data)
    return jsonify({'success': True, 'result': result})
except Exception as e:
    logger.error(f"Error: {str(e)}")
    return jsonify({'error': str(e)}), 500
```

## Development Setup

### 1. Install Dependencies
```bash
cd deep_research_economy
pip3 install -r requirements.txt
```

### 2. Start Flask Server
```bash
PORT=5001 python3 api_server.py
```

### 3. Configure Plugin
The plugin automatically connects to `localhost:5001`. Update `research-bridge.ts` if using a different port.

### 4. Environment Variables
```bash
export GEMINI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
export PORT=5001
export FLASK_ENV=development  # Enable debug mode
```

## Testing

### Unit Tests
```bash
# Test Flask endpoints
python3 test_api.py

# Test TypeScript bridge
npm test -- research-bridge
```

### Integration Tests
```bash
# Start server
python3 api_server.py &

# Run integration tests
node test-api-integration.js
```

## Security Considerations

### Development
- CORS allows all origins (`*`) for ease of development
- Server binds to `0.0.0.0` for local network access
- No authentication required

### Production Recommendations
1. **CORS**: Restrict to specific origins
   ```python
   CORS(app, origins=['https://figma.com'])
   ```

2. **Authentication**: Add API key validation
   ```python
   def require_api_key(f):
       @wraps(f)
       def decorated_function(*args, **kwargs):
           api_key = request.headers.get('X-API-Key')
           if not validate_api_key(api_key):
               return jsonify({'error': 'Invalid API key'}), 401
           return f(*args, **kwargs)
       return decorated_function
   ```

3. **Rate Limiting**: Prevent abuse
   ```python
   from flask_limiter import Limiter
   limiter = Limiter(app, key_func=get_remote_address)
   
   @limiter.limit("10 per minute")
   @app.route('/api/research/generate')
   ```

4. **HTTPS**: Use SSL/TLS for encrypted communication
5. **Input Validation**: Sanitize all user inputs
6. **Session Storage**: Use Redis or database instead of memory

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   - macOS AirPlay uses port 5000
   - Solution: Use port 5001 or disable AirPlay

2. **CORS Errors**
   - Check Flask CORS configuration
   - Ensure server is running
   - Verify URL in research-bridge.ts

3. **Module Not Found**
   - Install dependencies: `pip3 install -r requirements.txt`
   - Check Python version (requires 3.7+)

4. **Connection Refused**
   - Start Flask server first
   - Check firewall settings
   - Verify port number matches

## Performance Optimization

### Caching
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_economy(game_name, depth):
    # Cache frequently requested games
    return generate_economy(game_name, depth)
```

### Async Processing
For long-running LLM requests:
```python
from celery import Celery

@app.route('/api/research/generate/async', methods=['POST'])
def generate_async():
    task = generate_economy_task.delay(data)
    return jsonify({'task_id': task.id})
```

### Connection Pooling
Reuse HTTP connections on client side:
```typescript
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), 30000);

const response = await fetch(url, {
  signal: controller.signal
});
```