# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Bamboo is an AI-powered workflow system built with LangGraph that generates:
- **Data visualizations** (matplotlib charts)
- **Markdown documents** with integrated charts
- **Manim animations** (mathematical videos)

All workflows use DeepSeek AI model for code/content generation.

## Development Commands

### Setup
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Configure `.env` file with:
```
DEEPSEEK_API_KEY=your_key_here
```

### Running the Application
```bash
./start.sh           # Quick start (checks env and deps)
python app.py        # Direct start
```

Server runs on `http://localhost:5001`

### CLI Workflow Testing
```bash
python draw_pic.py "绘图需求"           # Drawing workflow
python write_md.py "文档主题"            # Document generation
python write_md_with_images.py "主题"   # Document with embedded charts
python manim_gen.py "动画描述" [quality] # Manim animation (quality: low/medium/high/4k)
```

### Manim Testing
```bash
# Manim renders to nested directories: media/videos/<scene_name>/<quality>/<filename>.mp4
# Videos are moved to videos/ directory after completion
manim -ql scene_file.py SceneClassName     # Render low quality
manim -qm scene_file.py SceneClassName     # Render medium quality
```

## Architecture

### LangGraph Workflows

Each workflow is a StateGraph with nodes that pass state dictionaries:

```
GraphState (TypedDict)
    ├── user_prompt: str
    ├── refined_prompt: str
    ├── generated_code/content: str
    ├── image_path/video_path: str
    └── error: str
```

**Node pattern**: Each node receives `GraphState`, returns dict with updated fields.

**Error handling**: Check `state.get("error")` at start of nodes, propagate errors via `{"error": "message"}`.

### Core Files

| File | Purpose |
|------|---------|
| `draw_pic.py` | 4-step drawing workflow: refine → generate → execute → save |
| `write_md_with_images.py` | 8-step doc+images workflow: refine → outline → content → identify images → generate → embed → save → verify |
| `manim_gen.py` | 4-step animation workflow: refine → generate → render → save |
| `app.py` | Flask server with WebSocket support for real-time updates |

### WebSocket Architecture

Three workflow types with isolated state:
- `drawing` - Drawing workflow
- `document_with_images` - Document generation with embedded charts
- `manim` - Manim animation workflow

Clients connect with workflow type selection:
```javascript
const socket = new WebSocket('ws://localhost:5001/ws');
socket.send(JSON.stringify({workflow_type: 'drawing'}));
```

Status updates broadcast to clients of specific workflow type:
```python
workflow_statuses = {
    'drawing': {'status': 'running', 'current_step': '', 'steps': [], ...},
    'document_with_images': {...},
    'manim': {...}
}
```

### API Endpoints Structure

**Drawing**: `/api/drawing/workflow`, `/api/drawing/clear`
**Documents**: `/api/document/workflow-with-images`, `/api/document/ai-modify`, `/api/document/generate-image`
**Manim**: `/api/manim/workflow`, `/api/manim/videos`, `/api/manim/clear`
**Files**: `/api/images`, `/api/documents`, `/api/history`

### Threaded Workflow Execution

Long-running workflows execute in daemon threads with monitored wrappers:

```python
def run_workflow_thread(user_prompt):
    def monitored_node(state):
        workflow_statuses['type']['steps'].append({'step': 'name', 'status': 'running'})
        update_and_emit_status('type')
        result = original_node(state)
        workflow_statuses['type']['steps'][-1]['status'] = 'completed'
        update_and_emit_status('type')
        return result
```

## Code Patterns

### DeepSeek API Integration
```python
from openai import OpenAI
client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")

# Streaming response
stream = client.chat.completions.create(
    model="deepseek-chat",
    messages=[...],
    stream=True
)
for chunk in stream:
    content = chunk.choices[0].delta.content
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
script_dir = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.join(script_dir, "output")
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
```

### Recursive File Search
```python
# Manim outputs to nested: media/videos/<scene>/<quality>/<file>.mp4
import glob
videos = glob.glob(os.path.join(videos_dir, "media/videos/**/*.mp4"), recursive=True)
```

## Important Constraints

### Manim Workflow
- Clear cache before rendering: `shutil.rmtree(os.path.join(videos_dir, "media", "cache"))`
- Videos output to nested directories, use recursive glob to find
- Class name extraction: `re.search(r'class\s+(\w+)\s*\(\s*Scene\s*\)', code)`
- Use `-o` flag for custom output filename

### Drawing Workflow
- Matplotlib Chinese font configuration required (see `draw_pic.py` font setup)
- Use `plt.tight_layout()` and `bbox_inches='tight'` to prevent clipping
- Avoid matplotlib format string color codes like 'purple-' (use `color='purple'` instead)
- Generate dense data points: `np.linspace(start, end, 1000)`

### Document Workflow
- KaTeX-compatible LaTeX only (avoid `\cdotp`, `\*`; use `\cdot`)
- Use UTC timestamps for filenames
- Clean document IDs: extract keywords, replace special chars with `_`

## Common Issues

### Manim Return Code 1
- Cause: Cache corruption or subprocess stderr handling issue
- Fix: Clear cache directory before rendering
- Debug: Check full stderr output from `process.communicate()`

### WebSocket Not Receiving Updates
- Ensure workflow_type is set correctly on client connection
- Check `update_and_emit_status()` is called after state changes
- Verify client is subscribed to correct workflow type

### Empty/Blank Images
- Add data validation: check for NaN, Inf, all-zero values
- Explicitly set axis limits: `ax.set_xlim()`, `ax.set_ylim()`
- Ensure plot objects are added to axes before saving
