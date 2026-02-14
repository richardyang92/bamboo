# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Bamboo is an AI-powered workflow system built with LangGraph that generates:
- **Data visualizations** (matplotlib charts)
- **Markdown documents** with integrated charts
- **Manim animations** (mathematical videos)

The project has been refactored into a modern **frontend-backend architecture**:
- **Backend**: Flask API with WebSocket support, LangGraph workflows
- **Frontend**: React 19 + TypeScript + Vite

All workflows support multiple LLM providers (DeepSeek and Ollama) with runtime model switching.

## Development Commands

### Initial Setup
```bash
# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend setup
cd frontend
npm install
```

Configure environment in `backend/.env`:
```
DEEPSEEK_API_KEY=your_key_here
DEFAULT_LLM_PROVIDER=deepseek
OLLAMA_BASE_URL=http://localhost:11434
```

**Supported LLM Providers:**
- **DeepSeek** (default): Requires `DEEPSEEK_API_KEY`, models: `deepseek-chat`, `deepseek-reasoner`
- **Ollama** (local): Requires running `ollama serve`, supports models like `llama3.1`, `deepseek-r1`

### Running the Application

**Development Mode (Full Stack):**
```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
python app.py       # Runs on http://localhost:5001

# Terminal 2: Frontend
cd frontend
npm run dev         # Runs on http://localhost:5173
```

**Production Build:**
```bash
cd frontend
npm run build       # Builds to frontend/dist/
# Backend will serve static files from frontend/dist/
```

### Frontend Commands
```bash
npm run dev         # Start Vite dev server (port 5173)
npm run build       # TypeScript check + build for production
npm run lint        # Run ESLint
npm run preview     # Preview production build
```

## Architecture

### Project Structure

```
bamboo/
├── backend/                # Flask backend
│   ├── app.py            # Flask server, WebSocket, REST API
│   ├── config.py         # Centralized configuration
│   ├── workflows/        # LangGraph workflow definitions
│   │   ├── draw_pic.py           # 4-step drawing workflow
│   │   ├── write_md_with_images.py # 8-step doc workflow
│   │   └── manim_gen.py          # 4-step animation workflow
│   ├── static/           # Generated files
│   │   ├── images/      # Generated plots
│   │   ├── docs/        # Generated markdown documents
│   │   └── videos/      # Generated Manim animations
│   └── requirements.txt
├── frontend/              # React + TypeScript frontend
│   ├── src/
│   │   ├── components/   # React components by workflow type
│   │   ├── pages/       # HomePage, HistoryPage
│   │   ├── services/    # API client, WebSocket client
│   │   ├── types/       # TypeScript type definitions
│   │   └── main.tsx     # React entry point
│   ├── vite.config.ts    # Vite dev server with proxy
│   └── package.json
```

### Technology Stack

**Backend:**
- Flask 3.0.0 (Web framework)
- flask-sock 0.7.0 (WebSocket support)
- flask-cors 4.0.0 (CORS handling)
- LangGraph 0.0.28 (Workflow engine)
- OpenAI SDK (DeepSeek API client)
- matplotlib >= 3.9.0, numpy >= 2.0.0
- manim >= 0.18.0

**Frontend:**
- React 19.2.0
- TypeScript 5.9.3
- Vite 7.3.1 (Build tool + dev server)
- Ant Design 6.3.0 (UI framework)
- Axios 1.13.5 (HTTP client)
- react-markdown 10.1.0, KaTeX 0.16.28 (Markdown + Math)
- react-router-dom 7.13.0 (Routing)
- @xyflow/react (Workflow graph visualization)
- react-syntax-highlighter (Code highlighting)

## LangGraph Workflow Architecture

Each workflow is a StateGraph with nodes that pass state dictionaries:

```python
# State pattern (TypedDict)
class GraphState(TypedDict):
    user_prompt: str
    refined_prompt: str
    generated_code/content: str
    image_path/video_path: str
    error: str
```

**Node pattern**: Each node receives `GraphState`, returns dict with updated fields.

**Error handling**: Check `state.get("error")` at start of nodes, propagate errors via `{"error": "message"}`.

### Workflow Files

| File | Purpose |
|------|---------|
| [backend/workflows/draw_pic.py](backend/workflows/draw_pic.py) | 4-step drawing workflow |
| [backend/workflows/write_md_with_images.py](backend/workflows/write_md_with_images.py) | 8-step document workflow |
| [backend/workflows/manim_gen.py](backend/workflows/manim_gen.py) | 4-step animation workflow |

### LLM Provider Architecture

The system uses a factory pattern for multi-provider LLM support in `backend/llm_providers/`:

| File | Purpose |
|------|---------|
| [backend/llm_providers/base.py](backend/llm_providers/base.py) | Abstract base class and `ModelConfig` dataclass |
| [backend/llm_providers/factory.py](backend/llm_providers/factory.py) | `LLMClientFactory` for creating clients, runtime config management |
| [backend/llm_providers/deepseek_provider.py](backend/llm_providers/deepseek_provider.py) | DeepSeek API implementation |
| [backend/llm_providers/ollama_provider.py](backend/llm_providers/ollama_provider.py) | Ollama local model implementation |

**Usage pattern:**
```python
from llm_providers.factory import LLMClientFactory

# Create client with default config
client = LLMClientFactory.create_client()

# Switch model at runtime
LLMClientFactory.set_runtime_config('ollama', 'llama3.1', enable_thinking=False)

# Get current config
config = LLMClientFactory.get_current_config()
# Returns: {'provider': 'ollama', 'model': 'llama3.1', 'supports_reasoning': False, 'enable_thinking': False}
```

**Reasoning model detection:** The factory auto-detects reasoning-capable models (DeepSeek-Reasoner, DeepSeek-R1 on Ollama) and enables thinking mode accordingly.

## Backend API Structure

### Configuration

Centralized configuration in [backend/config.py](backend/config.py):
- Environment variables via `python-dotenv`
- Static file paths: `static/images`, `static/docs`, `static/videos`
- CORS origins for development (ports 5173, 3000)

### REST API Endpoints

**Drawing:**
- `POST /api/drawing/workflow` - Start drawing workflow
- `GET /api/images` - List images
- `DELETE /api/images/<filename>` - Delete image
- `POST /api/drawing/clear` - Clear history
- `POST /api/drawing/stop` - Stop running workflow

**Documents:**
- `POST /api/document/workflow-with-images` - Start document workflow
- `POST /api/document/ai-modify` - AI modify selected text
- `POST /api/document/generate-image` - Generate image for document
- `GET /api/documents` - List documents
- `GET /api/documents/<filename>/content` - Get document content
- `DELETE /api/documents/<filename>` - Delete document
- `POST /api/document/stop` - Stop running workflow

**Manim:**
- `POST /api/manim/workflow` - Start Manim workflow (with quality param)
- `GET /api/manim/videos` - List videos
- `DELETE /api/manim/videos/<filename>` - Delete video
- `POST /api/manim/clear` - Clear history
- `POST /api/manim/stop` - Stop running workflow

**Model Management:**
- `GET /api/models` - List available models per provider
- `POST /api/models/switch` - Switch model at runtime
- `GET /api/models/current` - Get current model config

**Unified:**
- `GET /api/history` - List all items (images + docs + videos)
- `GET /api/health` - Health check

### WebSocket Architecture

**Endpoint:** `ws://localhost:5001/ws`

**Connection flow:**
1. Client connects to WebSocket
2. Client sends first message: `{"workflow_type": "drawing|document_with_images|manim"}`
3. Server adds client to connection pool for that workflow type
4. Server broadcasts status updates to clients of specific type

**Message types:**
- `status_update` - Workflow progress updates
- `stream_content` - AI streaming responses (with `content_type`: 'content' or 'reasoning')

**Status tracking:** Isolated per workflow type in `workflow_statuses` dict in [backend/app.py](backend/app.py:40-62).

### Workflow Stop Mechanism

Each workflow can be stopped mid-execution via stop flags in [backend/app.py](backend/app.py:70-82):

```python
workflow_stop_flags = {
    'drawing': False,
    'document_with_images': False,
    'manim': False
}

def should_stop_workflow(workflow_type: str) -> bool:
    return workflow_stop_flags.get(workflow_type, False)
```

**Implementation pattern:** Each monitored node checks `should_stop_workflow()` at the start and returns `{"error": "用户取消操作"}` if true. The graph stream loop also checks between node executions.

## Frontend Architecture

### Key Files

**Services:**
- [frontend/src/services/api.ts](frontend/src/services/api.ts) - Axios HTTP client with interceptors
- [frontend/src/services/websocket.ts](frontend/src/services/websocket.ts) - WebSocket singleton with reconnection

**Types:** [frontend/src/types/index.ts](frontend/src/types/index.ts) defines:
- `WorkflowType`, `WorkflowStatusType` (includes 'stopped'), `StepStatus` (includes 'skipped')
- `WorkflowStatus`, `WorkflowStep`, `WorkflowResult`
- `HistoryItem`, `WebSocketMessage`
- `ModelConfig`, `AvailableModels`, `LLMProvider` for model management
- `WorkflowNodeData`, `WorkflowEdgeData` for React Flow graphs

**Components:** Organized by workflow type:
- `components/drawing/` - Drawing workflow UI
- `components/document/` - Document workflow UI
- `components/manim/` - Manim workflow UI
- `components/common/` - Shared components

### Development Configuration

[Vite config](frontend/vite.config.ts) proxies API/WebSocket to backend:
```typescript
proxy: {
  '/api': { target: 'http://localhost:5001', changeOrigin: true },
  '/ws': { target: 'ws://localhost:5001', ws: true }
}
```

**Environment variables (for frontend):**
- `VITE_API_URL` - Backend API base URL (default: http://localhost:5001)
- `VITE_WS_URL` - WebSocket URL (default: ws://localhost:5001/ws)

## Code Patterns

### LLM Client Usage
```python
from llm_providers.factory import LLMClientFactory

# Get client with current config
client = LLMClientFactory.create_client()

# Streaming response with callback
response = client.chat_completion(
    messages=[...],
    model='deepseek-chat',
    stream=True,
    think=False  # Enable for reasoning models
)
for chunk in response:
    content = chunk.choices[0].delta.content
    reasoning = chunk.choices[0].delta.reasoning_content  # For reasoning models
    if stream_callback:
        stream_callback(content, reasoning)
```

### DeepSeek API Integration (Legacy)
```python
from openai import OpenAI
client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")

# Streaming response with callback
stream = client.chat.completions.create(
    model="deepseek-chat",
    messages=[...],
    stream=True
)
for chunk in stream:
    content = chunk.choices[0].delta.content
    if stream_callback:
        stream_callback(content)
```

### Subprocess Error Handling (Critical for Manim)
```python
process = subprocess.Popen(cmd, stdout=PIPE, stderr=PIPE, text=True)

# Capture stderr line by line
stderr_lines = []
for line in process.stderr:
    stderr_lines.append(line)

# Must call communicate() BEFORE checking returncode
stdout_data, stderr_data = process.communicate()
returncode = process.returncode

if returncode != 0:
    full_stderr = ''.join(stderr_lines) + (stderr_data or '')
```

### File Path Handling
```python
from config import Config
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_path = os.path.join(Config.IMAGES_DIR, f"plot_{timestamp}.png")
```

### Monitored Workflow Node Pattern

Nodes in [backend/app.py](backend/app.py) are wrapped for progress tracking and stop detection:

```python
def monitored_refine_prompt(state):
    # Check stop flag first
    if should_stop_workflow('drawing'):
        return {"error": "用户取消操作"}

    # Set status to running
    workflow_statuses['drawing']['steps'].append({
        'step': 'refine_prompt',
        'name': DRAWING_STEP_NAMES['refine_prompt'],
        'status': 'running',
        'timestamp': datetime.now().isoformat()
    })
    update_and_emit_status('drawing')  # Broadcast to clients

    result = refine_prompt(state)  # Execute original node

    # Mark as completed
    workflow_statuses['drawing']['steps'][-1]['status'] = 'completed'
    workflow_statuses['drawing']['steps'][-1]['completed_at'] = datetime.now().isoformat()
    update_and_emit_status('drawing')
    return result
```

## Important Constraints

### Matplotlib/Drawing Workflow
- Chinese font configuration required (see [backend/workflows/draw_pic.py:41-58](backend/workflows/draw_pic.py:41-58))
- Use `plt.tight_layout()` and `bbox_inches='tight'` to prevent clipping
- Avoid matplotlib format string color codes like 'purple-' (use `color='purple'` instead)
- Generate dense data points: `np.linspace(start, end, 1000)`
- Must set explicit axis limits with `ax.set_xlim()`, `ax.set_ylim()`

### Manim Workflow
- Clear cache before rendering: `shutil.rmtree(os.path.join(Config.VIDEOS_DIR, "media", "cache"))`
- Videos output to nested directories: `media/videos/<scene>/<quality>/<file>.mp4`
- Use recursive glob to find: `glob.glob(os.path.join(videos_dir, "media/videos/**/*.mp4"), recursive=True)`
- Class name extraction: `re.search(r'class\s+(\w+)\s*\(\s*Scene\s*\)', code)`
- Use `-o` flag for custom output filename

### Document Workflow
- KaTeX-compatible LaTeX only (avoid `\cdotp`, `\*`; use `\cdot`)
- Use UTC timestamps for filenames
- Clean document IDs: extract keywords, replace special chars with `_`

### WebSocket Development
- Always send `workflow_type` in first message after connection
- Handle workflow type switching via `switchWorkflow()` method
- Max reconnection attempts: 5
- Reconnect delay: 2000ms

## Production Deployment

1. Build frontend: `cd frontend && npm run build`
2. Ensure `frontend/dist/` exists
3. Backend will serve static files from dist directory
4. WebSocket still active for real-time updates
5. Set environment variables:
   - `FLASK_HOST=0.0.0.0`
   - `FLASK_PORT=5001`
   - `DEEPSEEK_API_KEY=your_key`
   - `FRONTEND_URL` (for CORS)

## Common Issues

### Ollama Connection Failed
- Ensure Ollama service is running: `ollama serve`
- Check `OLLAMA_BASE_URL` in config (default: `http://localhost:11434`)
- Verify model is downloaded: `ollama list`, pull if needed: `ollama pull llama3.1`

### WebSocket Not Receiving Updates
- Ensure workflow_type is set correctly on client connection
- Check `update_and_emit_status()` is called after state changes
- Verify client is subscribed to correct workflow type

### Manim Return Code 1
- Cause: Cache corruption or subprocess stderr handling issue
- Fix: Clear cache directory before rendering
- Debug: Check full stderr output from `process.communicate()`

### Empty/Blank Images
- Add data validation: check for NaN, Inf, all-zero values
- Explicitly set axis limits: `ax.set_xlim()`, `ax.set_ylim()`
- Ensure plot objects are added to axes before saving
- Check backend logs for matplotlib warnings

### Frontend Can't Connect to Backend
- Ensure Vite proxy is configured correctly in [vite.config.ts](frontend/vite.config.ts)
- Backend should be running on port 5001
- Check CORS origins in [backend/config.py](backend/config.py:26-31)
