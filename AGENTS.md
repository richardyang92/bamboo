# AGENTS.md

This file provides guidance for agentic coding assistants working in this repository.

## Build Commands

### Installation
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Running the Application
```bash
# Quick start (recommended)
./start.sh

# Or manually
python app.py
```

### Running Drawing Workflow (CLI)
```bash
python draw_pic.py "绘图需求描述"
```

### Running Document Workflow (CLI)
```bash
python write_md.py "文档主题"
```

### Running Document Workflow with Images (CLI)
```bash
python write_md_with_images.py "文档主题"
```

### Testing
No automated tests currently exist in this repository. When adding tests:
- Use pytest: `pytest tests/`
- Run single test: `pytest tests/test_module.py::test_function`

## Code Style Guidelines

### Python Code Style

#### Imports
1. Standard library imports first
2. Third-party imports second
3. Local imports third
4. Each import on separate line
5. Avoid `from module import *`

Example:
```python
import os
import sys
from typing import TypedDict
from langgraph.graph import StateGraph, END
from openai import OpenAI
from dotenv import load_dotenv
```

#### Type Hints
- Always use type hints for function parameters and return values
- Use `TypedDict` for complex state structures
- Import from `typing` module

Example:
```python
class GraphState(TypedDict):
    user_prompt: str
    refined_prompt: str
    generated_code: str
    error: str

def refine_prompt(state: GraphState) -> GraphState:
    """Refine user prompt for better code generation."""
    pass
```

#### Naming Conventions
- Variables and functions: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private methods: `_leading_underscore`

#### Error Handling
- Wrap all external API calls in try/except blocks
- Provide specific error messages with context
- Return error state in workflow nodes: `{"error": "message"}`
- Use traceback for debugging but not in production output

Example:
```python
try:
    result = client.chat.completions.create(...)
    return {"content": result}
except Exception as e:
    import traceback
    error_msg = f"Generation failed: {str(e)}"
    traceback.print_exc()
    return {"error": error_msg}
```

#### Docstrings
- Use triple-quoted strings for function documentation
- Brief description of purpose
- Document parameters and return values for complex functions

#### Debugging Output
- Use `print()` with prefixes: `[DEBUG]`, `[INFO]`, `[WARNING]`
- Prefix with emoji for better visibility: ✅ ❌ 📝
- Include context and variable values in debug messages

Example:
```python
print(f"[DEBUG] API Key status: {'set' if api_key else 'not set'}")
print(f"✅ Image saved successfully")
```

### LangGraph Workflow Patterns

#### Node Functions
- Each node receives `GraphState` as parameter
- Return dictionary with updated state fields
- Never mutate state directly; return updated fields
- Check for existing errors before processing

Example:
```python
def process_node(state: GraphState) -> GraphState:
    if state.get("error"):
        return state  # Skip processing if error exists

    try:
        # Process logic
        return {"result": processed_data}
    except Exception as e:
        return {"error": str(e)}
```

#### Workflow Definition
```python
from langgraph.graph import StateGraph, END

workflow = StateGraph(GraphState)
workflow.add_node("node_name", node_function)
workflow.set_entry_point("node_name")
workflow.add_edge("node1", "node2")
workflow.add_edge("node2", END)
return workflow.compile()
```

### API Integration

#### OpenAI/DeepSeek Client
```python
from openai import OpenAI
import os

api_key = os.getenv("DEEPSEEK_API_KEY")
client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[...],
    temperature=0.3,
    max_tokens=6000
)
```

#### Token Usage Monitoring
- Check `response.usage.total_tokens` after API calls
- Warn if approaching token limits
- Adjust `max_tokens` based on output size needs

### File Operations

#### Path Handling
- Use `os.path` for cross-platform compatibility
- Use absolute paths when working with files
- Create directories if they don't exist

Example:
```python
import os
from datetime import datetime

script_dir = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.join(script_dir, "output")

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_path = os.path.join(output_dir, f"file_{timestamp}.ext")
```

#### File Naming
- Use descriptive prefixes: `plot_`, `doc_`, `log_`
- Include timestamps for uniqueness
- Remove special characters from user input

### Flask/Web Development

#### SocketIO Updates
- Use `socketio.emit()` for real-time status updates
- Call `socketio.sleep(0)` after emit to force immediate send
- Include type field in updates for multi-workflow support

```python
socketio.emit('status_update', {'type': 'drawing', **workflow_status})
socketio.sleep(0)  # Force immediate send
```

#### API Endpoints
- Use RESTful naming conventions
- Return JSON responses
- Include appropriate HTTP status codes
- Handle errors gracefully

### Code Organization

#### File Structure
- `app.py` - Flask application and API routes
- `draw_pic.py` - Drawing workflow nodes
- `write_md.py` - Document generation workflow nodes
- `templates/` - HTML templates
- `images/` - Generated plots
- `docs/` - Generated documents

#### Modular Design
- Each workflow in separate file
- Reusable utility functions
- Configuration in `.env` file
- Environment variables with `dotenv`

## Environment Variables

Required environment variables in `.env`:
```
DEEPSEEK_API_KEY=your_api_key_here
```

## Important Notes

### Code Safety
- Generated code executes in sandboxed environment
- Always validate user input
- Never commit `.env` file or API keys

### Chinese Language Support
- Configure matplotlib fonts: `['Arial Unicode MS', 'SimHei', ...]`
- Set `rcParams['axes.unicode_minus'] = False`
- Use UTF-8 encoding for file operations

### KaTeX Compatibility (for documents)
- Use KaTeX-compatible LaTeX commands
- Avoid: `\\cdotp`, `\\*`
- Prefer: `\\cdot`, standard LaTeX symbols

### Performance
- Use threading for long-running workflows
- Avoid blocking the main Flask thread
- Optimize API token usage with appropriate max_tokens

## Development Workflow

1. Make changes to Python files
2. Test locally with `python app.py` or CLI commands
3. Verify API integration with valid DEEPSEEK_API_KEY
4. Check console output for [DEBUG] messages
5. Test real-time updates in browser console
6. Generate sample outputs in `images/` or `docs/`

## Common Patterns to Follow

### Workflow Step Progress
```python
workflow_status['steps'].append({
    'step': 'step_name',
    'name': 'Human Readable Name',
    'status': 'running',
    'timestamp': datetime.now().isoformat()
})
socketio.emit('status_update', {'type': 'workflow', **workflow_status})
# ... process ...
workflow_status['steps'][-1]['status'] = 'completed'
socketio.emit('status_update', {'type': 'workflow', **workflow_status})
```

### Monitored Node Wrapper
```python
def monitored_node(state):
    print(f"[DEBUG] >>> Node 'node_name' starting")
    # Update status to running
    result = original_node(state)
    # Update status to completed
    print(f"[DEBUG] <<< Node 'node_name' complete")
    return result
```
