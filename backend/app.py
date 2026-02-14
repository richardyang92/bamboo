from flask import Flask, request, jsonify, send_from_directory
from flask_sock import Sock
from flask_cors import CORS
import os
import threading
import json
import sys
from workflows.draw_pic import create_graph, GraphState
from datetime import datetime
from config import Config
from llm_providers.factory import LLMClientFactory
from llm_providers.ollama_provider import get_ollama_model_capabilities

# Fix UTF-8 encoding on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 初始化 Flask 应用
app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY
sock = Sock(app)

# CORS 配置
CORS(app, resources={
    r"/api/*": {
        "origins": Config.CORS_ORIGINS,
        "methods": ["GET", "POST", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# WebSocket 连接池 (按工作流类型分组)
websocket_clients = {
    'drawing': [],
    'document_with_images': [],
    'manim': []
}

# 全局变量存储工作流状态（支持多个工作流类型）
workflow_statuses = {
    'drawing': {
        'status': 'idle',
        'current_step': '',
        'steps': [],
        'result': None,
        'error': None
    },
    'document_with_images': {
        'status': 'idle',
        'current_step': '',
        'steps': [],
        'result': None,
        'error': None
    },
    'manim': {
        'status': 'idle',
        'current_step': '',
        'steps': [],
        'result': None,
        'error': None
    }
}

# 用于线程间通信的锁
status_lock = threading.Lock()

# 工作流停止标志（用于中断正在运行的工作流）
workflow_stop_flags = {
    'drawing': False,
    'document_with_images': False,
    'manim': False
}

def should_stop_workflow(workflow_type: str) -> bool:
    """检查工作流是否应该停止"""
    return workflow_stop_flags.get(workflow_type, False)

def reset_stop_flag(workflow_type: str):
    """重置工作流停止标志"""
    workflow_stop_flags[workflow_type] = False

# 为了向后兼容，保留旧的 workflow_status 引用
workflow_status = workflow_statuses['drawing']

def broadcast_to_workflow(workflow_type, message):
    """向指定工作流类型的所有客户端发送消息"""
    clients = websocket_clients.get(workflow_type, [])
    if not clients:
        print(f"[DEBUG] 无客户端连接，跳过发送: {workflow_type}")
        return
    
    print(f"[DEBUG] 向 {len(clients)} 个客户端发送消息: {workflow_type}")
    
    for ws in clients[:]:  # 使用切片避免迭代时修改列表
        try:
            data = json.dumps(message)
            print(f"[DEBUG] 发送消息内容长度: {len(data)} 字符")
            ws.send(data)
            print(f"[DEBUG] 消息发送成功")
        except Exception as e:
            print(f"[WARNING] 发送消息失败: {e}")
            import traceback
            traceback.print_exc()
            try:
                if ws in clients:
                    clients.remove(ws)
            except:
                pass

# 辅助函数：安全地更新和发送状态
def update_and_emit_status(workflow_type):
    """安全地更新并发送状态更新"""
    with status_lock:
        status = workflow_statuses.get(workflow_type, {}).copy()
    
    message = {
        'type': 'status_update',
        'workflow_type': workflow_type,
        **status
    }
    broadcast_to_workflow(workflow_type, message)
    print(f"[DEBUG] 状态更新已发送: {workflow_type} - {status.get('status', 'unknown')}")

# 辅助函数：发送流式响应内容
def emit_stream_content(workflow_type, node_name, content, content_type='content'):
    """发送AI流式响应内容到前端

    Args:
        workflow_type: 工作流类型
        node_name: 节点名称
        content: 内容文本
        content_type: 内容类型 ('content' 或 'reasoning')
    """
    message = {
        'type': 'stream_content',
        'workflow_type': workflow_type,
        'node': node_name,
        'content': content,
        'content_type': content_type  # 新增：区分普通内容和思考内容
    }
    broadcast_to_workflow(workflow_type, message)
    content_label = '思考内容' if content_type == 'reasoning' else '流式内容'
    print(f"[DEBUG] {content_label}已发送: {workflow_type}/{node_name}, 长度: {len(content)} 字符")

# 状态映射
DRAWING_STEP_NAMES = {
    'refine_prompt': '润色提示词',
    'generate_code': '生成绘图代码',
    'execute_code': '执行绘图代码',
    'analyze_execution_result': '分析执行结果',
    'fix_code_with_feedback': '修复代码',
    'save_image': '验证图片保存'
}

MANIM_STEP_NAMES = {
     'refine_prompt': '润色动画需求',
     'generate_code': '生成动画代码',
     'execute_code': '渲染动画视频',
     'save_video': '验证视频保存'
 }

# ==================== 前端静态文件服务（生产环境）====================
# 生产环境：服务前端静态文件
# 开发环境：前端由 Vite 开发服务器提供服务（http://localhost:5173）
FRONTEND_DIST = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frontend', 'dist')

@app.route('/api/health')
def health_check():
    """健康检查端点"""
    return jsonify({
        'status': 'healthy',
        'workflows': ['drawing', 'document_with_images', 'manim']
    })

# ========== 模型管理 API ==========

def get_ollama_models():
    """从 Ollama API 获取已安装的模型列表"""
    import requests
    try:
        # 调用 Ollama API 获取模型列表
        base_url = Config.OLLAMA_BASE_URL.replace('/v1', '')
        ollama_url = f'{base_url}/api/tags'
        print(f"[DEBUG] 正在从 Ollama API 获取模型列表: {ollama_url}")

        response = requests.get(ollama_url, timeout=2)
        print(f"[DEBUG] Ollama API 响应状态: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            models = [model['name'] for model in data.get('models', [])]
            print(f"[DEBUG] 从 Ollama 获取到 {len(models)} 个模型: {models}")
            return models
        else:
            print(f"[DEBUG] Ollama API 返回状态码: {response.status_code}")
            return None
    except Exception as e:
        print(f"[DEBUG] 获取 Ollama 模型列表失败: {e}")
        print(f"[DEBUG] 请确保 Ollama 服务正在运行: ollama serve")
        return None

def get_model_capabilities(provider: str, model_names: list) -> list:
    """为模型列表添加能力信息

    Args:
        provider: 提供商名称 ('deepseek' | 'ollama')
        model_names: 模型名称列表

    Returns:
        包含模型能力信息的列表，每个元素为 {'name': str, 'supports_thinking': bool}
    """
    models_with_info = []
    for model in model_names:
        if provider == 'deepseek':
            # DeepSeek: 只有 reasoner 系列支持思考
            supports_thinking = 'reasoner' in model.lower()
        elif provider == 'ollama':
            # Ollama: 使用 client.show() 动态获取模型能力
            # 检查 capabilities 中是否包含 "thinking"
            try:
                capabilities_info = get_ollama_model_capabilities(model)
                supports_thinking = capabilities_info.get('supports_thinking', False)
            except Exception as e:
                print(f"[DEBUG] 获取模型 {model} 能力失败: {e}，使用回退逻辑")
                # 回退到硬编码列表
                thinking_models = ['deepseek-r1', 'deepseek-v3', 'qwen3', 'phi-4']
                supports_thinking = any(tm in model.lower() for tm in thinking_models)
        else:
            supports_thinking = False

        models_with_info.append({
            'name': model,
            'supports_thinking': supports_thinking
        })
    return models_with_info

@app.route('/api/models', methods=['GET'])
def get_available_models():
    """获取可用的模型列表"""
    print("[DEBUG] ===== /api/models 被调用 =====")
    # DeepSeek 模型（固定列表）
    deepseek_models = ['deepseek-chat', 'deepseek-reasoner']

    # 尝试从 Ollama API 获取模型列表
    ollama_models = get_ollama_models()

    if ollama_models is None:
        # Ollama 服务不可用，使用默认列表
        print("[DEBUG] Ollama 服务不可用，使用默认模型列表")
        ollama_models = ['llama3.1', 'llama3', 'mistral', 'codellama', 'qwen2.5', 'deepseek-coder']
    else:
        print(f"[DEBUG] /api/models 返回 Ollama 实际模型列表: {ollama_models}")

    # 为模型添加能力信息
    deepseek_models_with_info = get_model_capabilities('deepseek', deepseek_models)
    ollama_models_with_info = get_model_capabilities('ollama', ollama_models)

    # 检查 Ollama 模型列表中是否有支持思考的模型
    ollama_supports_reasoning = any(m['supports_thinking'] for m in ollama_models_with_info)

    models = {
        'deepseek': {
            'provider': 'deepseek',
            'models': deepseek_models_with_info,
            'supports_reasoning': True,
            'current': Config.DEEPSEEK_MODEL
        },
        'ollama': {
            'provider': 'ollama',
            'models': ollama_models_with_info,
            'supports_reasoning': ollama_supports_reasoning,
            'current': ollama_models[0] if ollama_models else Config.OLLAMA_MODEL
        }
    }

    response = {
        'providers': models,
        'current_provider': Config.DEFAULT_LLM_PROVIDER,
        'current_config': Config.get_current_model_config()
    }
    print(f"[DEBUG] 返回的响应: {response}")
    return jsonify(response)

@app.route('/api/models/switch', methods=['POST'])
def switch_model():
    """切换当前使用的模型（运行时）"""
    data = request.json
    provider = data.get('provider')
    model = data.get('model')
    enable_thinking = data.get('enable_thinking', False)

    if not provider or not model:
        return jsonify({'error': '缺少必要参数: provider 和 model'}), 400

    if provider not in ['deepseek', 'ollama']:
        return jsonify({'error': '不支持的提供商'}), 400

    # 验证模型名称
    if provider == 'deepseek':
        if model not in ['deepseek-chat', 'deepseek-reasoner']:
            return jsonify({'error': '不支持的 DeepSeek 模型'}), 400
    elif provider == 'ollama':
        # 对于 Ollama，验证模型是否存在
        ollama_models = get_ollama_models()
        if ollama_models is None:
            # Ollama 服务不可用，使用默认列表验证
            default_models = ['llama3.1', 'llama3', 'mistral', 'codellama', 'qwen2.5', 'deepseek-coder']
            if model not in default_models:
                return jsonify({'error': f'不支持的 Ollama 模型: {model}. Ollama 服务可能未启动'}), 400
        elif model not in ollama_models:
            return jsonify({'error': f'模型 {model} 未在 Ollama 中找到'}), 400

    # 更新运行时配置（包括 enable_thinking）
    LLMClientFactory.set_runtime_config(provider, model, enable_thinking)

    return jsonify({
        'success': True,
        'current_config': LLMClientFactory.get_current_config()
    })

@app.route('/api/models/current', methods=['GET'])
def get_current_model():
    """获取当前使用的模型配置"""
    return jsonify(LLMClientFactory.get_current_config())

@app.route('/')
@app.route('/<path:path>')
def serve_frontend(path='index.html'):
    """服务前端静态文件（仅生产环境）"""
    # 如果前端构建目录存在，则服务静态文件
    if os.path.exists(FRONTEND_DIST):
        if path != 'index.html':
            file_path = os.path.join(FRONTEND_DIST, path)
            if os.path.isfile(file_path):
                return send_from_directory(FRONTEND_DIST, path)
        return send_from_directory(FRONTEND_DIST, 'index.html')
    else:
        # 开发环境：前端由 Vite 开发服务器提供服务
        return jsonify({
            'message': 'Frontend development server should be running at http://localhost:5173',
            'status': 'development_mode'
        })

@app.route('/api/workflow', methods=['POST'])
def run_workflow():
    """启动绘图工作流（向后兼容）"""
    return run_drawing_workflow()

@app.route('/api/drawing/workflow', methods=['POST'])
def run_drawing_workflow():
    """启动绘图工作流"""
    data = request.json
    user_prompt = data.get('prompt', '')
    model_provider = data.get('model_provider')
    model_name = data.get('model_name')
    enable_thinking = data.get('enable_thinking', False)

    if not user_prompt:
        return jsonify({'error': '请输入绘图需求'}), 400

    # 如果指定了模型配置，先设置运行时配置
    if model_provider and model_name:
        try:
            LLMClientFactory.set_runtime_config(model_provider, model_name, enable_thinking)
        except Exception as e:
            return jsonify({'error': f'模型配置失败: {str(e)}'}), 400

    # 立即更新状态为运行中，提供即时反馈
    workflow_statuses['drawing'] = {
        'status': 'running',
        'current_step': '',
        'steps': [],
        'result': None,
        'error': None
    }

    # 立即推送状态到客户端，确保无延迟
    update_and_emit_status('drawing')
    print(f"[DEBUG] 初始绘图状态已发送到客户端")

    # 在新线程中运行工作流
    thread = threading.Thread(target=run_drawing_workflow_thread, args=(user_prompt,))
    thread.daemon = True
    thread.start()

    return jsonify({'message': '绘图工作流已启动'})

@app.route('/api/status')
def get_status():
    """获取当前状态"""
    return jsonify(workflow_status)

@app.route('/api/images')
def list_images():
    """列出所有生成的图片"""
    plot_files = []
    if os.path.exists(os.path.join(Config.BASE_DIR, 'static', 'images')):
        for file in os.listdir(Config.IMAGES_DIR):
            if file.startswith('plot_') and file.endswith('.png'):
                filepath = os.path.join(Config.IMAGES_DIR, file)
                plot_files.append({
                    'name': file,
                    'path': f'/api/images/{file}',
                    'size': os.path.getsize(filepath),
                    'created': os.path.getmtime(filepath)
                })

    # 按创建时间排序
    plot_files.sort(key=lambda x: x['created'], reverse=True)
    return jsonify(plot_files)

@app.route('/api/images/<filename>')
def get_image(filename):
    """获取图片文件"""
    return send_from_directory(Config.IMAGES_DIR, filename)

@app.route('/api/images/<filename>', methods=['DELETE'])
def delete_image(filename):
    """删除图片文件"""
    try:
        filepath = os.path.join(Config.IMAGES_DIR, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            return jsonify({'message': '图片已删除'})
        else:
            return jsonify({'error': '文件不存在'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear', methods=['POST'])
def clear_history():
    """清除历史记录（向后兼容）"""
    return clear_drawing_history()

@app.route('/api/drawing/clear', methods=['POST'])
def clear_drawing_history():
    """清除绘图历史记录"""
    workflow_statuses['drawing']['steps'] = []
    workflow_statuses['drawing']['result'] = None
    workflow_statuses['drawing']['error'] = None
    update_and_emit_status('drawing')
    print("[DEBUG] 绘图历史已清除，状态已发送")
    return jsonify({'message': '绘图历史记录已清除'})

@app.route('/api/drawing/stop', methods=['POST'])
def stop_drawing_workflow():
    """停止绘图工作流"""
    if workflow_statuses['drawing']['status'] != 'running':
        return jsonify({'message': '工作流未在运行中'})

    workflow_stop_flags['drawing'] = True
    workflow_statuses['drawing']['status'] = 'stopped'
    workflow_statuses['drawing']['error'] = '用户取消操作'
    update_and_emit_status('drawing')
    print("[DEBUG] 绘图工作流已停止")
    return jsonify({'message': '绘图工作流已停止'})

# ==================== 文档工作流端点 ====================

@app.route('/api/document/workflow-with-images', methods=['POST'])
def run_document_with_images_workflow():
    """启动带图片的文档生成工作流"""
    data = request.json
    user_prompt = data.get('prompt', '')
    model_provider = data.get('model_provider')
    model_name = data.get('model_name')
    enable_thinking = data.get('enable_thinking', False)

    if not user_prompt:
        return jsonify({'error': '请输入文档主题'}), 400

    # 如果指定了模型配置，先设置运行时配置
    if model_provider and model_name:
        try:
            LLMClientFactory.set_runtime_config(model_provider, model_name, enable_thinking)
        except Exception as e:
            return jsonify({'error': f'模型配置失败: {str(e)}'}), 400

    # 立即更新状态为运行中
    workflow_statuses['document_with_images'] = {
        'status': 'running',
        'current_step': '',
        'steps': [],
        'result': None,
        'error': None
    }

    # 立即推送状态到客户端
    update_and_emit_status('document_with_images')
    print(f"[DEBUG] 初始文档状态已发送到客户端")

    # 在新线程中运行工作流
    thread = threading.Thread(target=run_document_with_images_thread, args=(user_prompt,))
    thread.daemon = True
    thread.start()

    return jsonify({'message': '带图片的文档生成工作流已启动'})

@app.route('/api/document/ai-modify', methods=['POST'])
def ai_modify_selection():
    """AI修改选中的文本内容"""
    try:
        data = request.json
        selected_text = data.get('selected_text', '')
        instructions = data.get('instructions', '')

        if not selected_text:
            return jsonify({'error': '请先选择要修改的内容'}), 400

        if not instructions:
            return jsonify({'error': '请提供修改指令'}), 400

        # 调用AI修改文本
        from openai import OpenAI
        import os

        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            return jsonify({'error': 'API密钥未配置'}), 500

        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

        prompt = f"""请根据以下指令修改这段文本，保持原有的Markdown格式和结构：

原文：
{selected_text}

修改指令：
{instructions}

要求：
1. 保持原有的Markdown格式（标题、列表、代码块等）
2. 保持原文的结构和逻辑
3. 严格按照修改指令进行修改
4. 只返回修改后的文本，不要添加任何解释或说明

修改后的文本："""

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": "你是一个专业的文本编辑助手，擅长根据用户指令修改文本内容。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=4000
        )

        modified_text = response.choices[0].message.content.strip()

        return jsonify({
            'modified_text': modified_text
        })

    except Exception as e:
        import traceback
        error_msg = f"修改失败: {str(e)}"
        traceback.print_exc()
        return jsonify({'error': error_msg}), 500

@app.route('/api/document/generate-image', methods=['POST'])
def ai_generate_image():
    """AI生成图片"""
    try:
        data = request.json
        description = data.get('description', '')

        if not description:
            return jsonify({'error': '请提供图片描述'}), 400

        # 导入绘图工作流
        from workflows.draw_pic import create_graph, GraphState

        print(f"\n[DEBUG] ===== AI生成图片工作流启动 =====")
        print(f"[DEBUG] 图片描述: '{description}'")

        # 创建工作流图
        workflow = create_graph()

        # 运行工作流
        initial_state = {
            "user_prompt": description,
            "generated_code": "",
            "image_path": "",
            "image_size": 0,
            "error": ""
        }

        print(f"[DEBUG] 开始调用绘图工作流...")
        result = workflow.invoke(initial_state)

        print(f"[DEBUG] ===== AI生成图片工作流执行完成 =====")
        print(f"[DEBUG] 最终结果: {result}")

        if result.get("error"):
            print(f"[DEBUG] 图片生成失败: {result['error']}")
            return jsonify({'error': result['error']}), 500

        # 提取文件名和URL
        filename = os.path.basename(result['image_path'])
        image_url = f'/api/images/{filename}'

        print(f"[DEBUG] 图片生成成功: {image_url}")

        return jsonify({
            'image_url': image_url,
            'image_path': result['image_path']
        })

    except Exception as e:
        import traceback
        error_msg = f"图片生成失败: {str(e)}"
        traceback.print_exc()
        return jsonify({'error': error_msg}), 500

@app.route('/api/documents')
def list_documents():
    """列出所有生成的文档"""
    doc_files = []
    if os.path.exists(Config.DOCS_DIR):
        for file in os.listdir(Config.DOCS_DIR):
            if file.startswith('doc_') and file.endswith('.md'):
                filepath = os.path.join(Config.DOCS_DIR, file)
                doc_files.append({
                    'type': 'document',
                    'name': file,
                    'url': f'/api/documents/{file}',
                    'size': os.path.getsize(filepath),
                    'created': os.path.getmtime(filepath)
                })

    # 按创建时间排序
    doc_files.sort(key=lambda x: x['created'], reverse=True)
    return jsonify(doc_files)

@app.route('/api/document/clear', methods=['POST'])
def clear_document_history():
    """清除文档历史记录"""
    workflow_statuses['document_with_images']['steps'] = []
    workflow_statuses['document_with_images']['result'] = None
    workflow_statuses['document_with_images']['error'] = None
    update_and_emit_status('document_with_images')
    print("[DEBUG] 文档历史已清除，状态已发送")
    return jsonify({'message': '文档历史记录已清除'})

@app.route('/api/document/stop', methods=['POST'])
def stop_document_workflow():
    """停止文档工作流"""
    if workflow_statuses['document_with_images']['status'] != 'running':
        return jsonify({'message': '工作流未在运行中'})

    workflow_stop_flags['document_with_images'] = True
    workflow_statuses['document_with_images']['status'] = 'stopped'
    workflow_statuses['document_with_images']['error'] = '用户取消操作'
    update_and_emit_status('document_with_images')
    print("[DEBUG] 文档工作流已停止")
    return jsonify({'message': '文档工作流已停止'})

@app.route('/api/documents/<filename>')
def get_document(filename):
    """获取文档内容"""
    return send_from_directory(Config.DOCS_DIR, filename)

@app.route('/api/documents/<filename>/content')
def get_document_content(filename):
    """获取文档的文本内容"""
    try:
        filepath = os.path.join(Config.DOCS_DIR, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            return jsonify({'content': content})
        else:
            return jsonify({'error': '文件不存在'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents/<filename>', methods=['DELETE'])
def delete_document(filename):
    """删除文档文件"""
    try:
        filepath = os.path.join(Config.DOCS_DIR, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            return jsonify({'message': '文档已删除'})
        else:
            return jsonify({'error': '文件不存在'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== Manim 动画工作流端点 ====================

@app.route('/api/manim/workflow', methods=['POST'])
def run_manim_workflow():
    """启动 Manim 动画工作流"""
    data = request.json
    user_prompt = data.get('prompt', '')
    quality = data.get('quality', 'medium')
    model_provider = data.get('model_provider')
    model_name = data.get('model_name')
    enable_thinking = data.get('enable_thinking', False)

    if not user_prompt:
        return jsonify({'error': '请输入动画需求'}), 400

    # 如果指定了模型配置，先设置运行时配置
    if model_provider and model_name:
        try:
            LLMClientFactory.set_runtime_config(model_provider, model_name, enable_thinking)
        except Exception as e:
            return jsonify({'error': f'模型配置失败: {str(e)}'}), 400

    # 立即更新状态为运行中
    workflow_statuses['manim'] = {
        'status': 'running',
        'current_step': '',
        'steps': [],
        'result': None,
        'error': None
    }

    # 立即推送状态到客户端
    update_and_emit_status('manim')
    print(f"[DEBUG] 初始 Manim 状态已发送到客户端")

    # 在新线程中运行工作流
    thread = threading.Thread(target=run_manim_workflow_thread, args=(user_prompt, quality,))
    thread.daemon = True
    thread.start()

    return jsonify({'message': 'Manim 动画工作流已启动'})

@app.route('/api/manim/videos')
def list_manim_videos():
    """列出所有生成的视频"""
    video_files = []
    if os.path.exists(Config.VIDEOS_DIR):
        for file in os.listdir(Config.VIDEOS_DIR):
            if file.startswith('manim_') and file.endswith('.mp4'):
                filepath = os.path.join(Config.VIDEOS_DIR, file)
                video_files.append({
                    'name': file,
                    'path': f'/api/manim/videos/{file}',
                    'size': os.path.getsize(filepath),
                    'created': os.path.getmtime(filepath)
                })

    video_files.sort(key=lambda x: x['created'], reverse=True)
    return jsonify(video_files)

@app.route('/api/manim/videos/<filename>')
def get_manim_video(filename):
    """获取视频文件"""
    return send_from_directory(Config.VIDEOS_DIR, filename)

@app.route('/api/manim/videos/<filename>', methods=['DELETE'])
def delete_manim_video(filename):
    """删除视频文件"""
    try:
        filepath = os.path.join(Config.VIDEOS_DIR, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            return jsonify({'message': '视频已删除'})
        else:
            return jsonify({'error': '文件不存在'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/manim/clear', methods=['POST'])
def clear_manim_history():
    """清除 Manim 历史记录"""
    workflow_statuses['manim']['steps'] = []
    workflow_statuses['manim']['result'] = None
    workflow_statuses['manim']['error'] = None
    update_and_emit_status('manim')
    print("[DEBUG] Manim 历史已清除，状态已发送")
    return jsonify({'message': 'Manim 历史记录已清除'})

@app.route('/api/manim/stop', methods=['POST'])
def stop_manim_workflow():
    """停止 Manim 工作流"""
    if workflow_statuses['manim']['status'] != 'running':
        return jsonify({'message': '工作流未在运行中'})

    workflow_stop_flags['manim'] = True
    workflow_statuses['manim']['status'] = 'stopped'
    workflow_statuses['manim']['error'] = '用户取消操作'
    update_and_emit_status('manim')
    print("[DEBUG] Manim 工作流已停止")
    return jsonify({'message': 'Manim 工作流已停止'})

 # ==================== 统一历史记录端点 ====================

@app.route('/api/history')
def list_history():
    """列出所有项目（图片 + 文档 + 视频）"""
    items = []

    # 添加图片
    if os.path.exists(os.path.join(Config.BASE_DIR, 'static', 'images')):
        for file in os.listdir(Config.IMAGES_DIR):
            if file.startswith('plot_') and file.endswith('.png'):
                filepath = os.path.join(Config.IMAGES_DIR, file)
                items.append({
                    'type': 'image',
                    'name': file,
                    'url': f'/api/images/{file}',
                    'size': os.path.getsize(filepath),
                    'created': os.path.getmtime(filepath)
                })

    # 添加文档
    if os.path.exists(Config.DOCS_DIR):
        for file in os.listdir(Config.DOCS_DIR):
            if file.startswith('doc_') and file.endswith('.md'):
                filepath = os.path.join(Config.DOCS_DIR, file)
                items.append({
                    'type': 'document',
                    'name': file,
                    'url': f'/api/documents/{file}',
                    'size': os.path.getsize(filepath),
                    'created': os.path.getmtime(filepath)
                })

    # 添加视频
    if os.path.exists(Config.VIDEOS_DIR):
        for file in os.listdir(Config.VIDEOS_DIR):
            if file.startswith('manim_') and file.endswith('.mp4'):
                filepath = os.path.join(Config.VIDEOS_DIR, file)
                items.append({
                    'type': 'video',
                    'name': file,
                    'url': f'/api/manim/videos/{file}',
                    'size': os.path.getsize(filepath),
                    'created': os.path.getmtime(filepath)
                })

    # 按创建时间排序
    items.sort(key=lambda x: x['created'], reverse=True)
    return jsonify(items)

# WebSocket 端点
@sock.route('/ws')
def websocket_connection(ws):
    """处理 WebSocket 连接"""
    print(f"[DEBUG] WebSocket 客户端连接")

    # 验证请求来源
    origin = ws.environ.get('HTTP_ORIGIN', '')
    if origin and origin not in Config.CORS_ORIGINS:
        print(f"[WARNING] WebSocket 连接被拒绝：无效的源 {origin}")
        ws.close()
        return

    try:
        # 首先接收客户端的 workflow_type 消息
        print(f"[DEBUG] 等待客户端 workflow_type 消息...")
        first_message = ws.receive()
        if first_message is None:
            print(f"[DEBUG] 客户端在发送 workflow_type 前断开连接")
            return

        data = json.loads(first_message)
        workflow_type = data.get('workflow_type', 'drawing')
        ws.workflow_type = workflow_type
        print(f"[DEBUG] 客户端工作流类型: {workflow_type}")

        # 验证 workflow_type
        if workflow_type not in ['drawing', 'document_with_images', 'manim']:
            print(f"[WARNING] 无效的工作流类型: {workflow_type}")
            ws.close()
            return

        # 将客户端添加到连接池
        if ws.workflow_type not in websocket_clients:
            websocket_clients[ws.workflow_type] = []
        websocket_clients[ws.workflow_type].append(ws)
        print(f"[DEBUG] 客户端已添加到 {ws.workflow_type} 连接池，当前连接数: {len(websocket_clients[ws.workflow_type])}")

        # 只发送当前工作流类型的初始状态（避免发送多个消息导致协议错误）
        with status_lock:
            status = workflow_statuses.get(ws.workflow_type, {}).copy()

        print(f"[DEBUG] 准备发送初始状态...")
        ws.send(json.dumps({
            'type': 'status_update',
            'workflow_type': ws.workflow_type,
            **status
        }))
        print(f"[DEBUG] {ws.workflow_type} 状态已发送")

        # 持续监听后续消息
        print(f"[DEBUG] 开始监听客户端消息...")
        while True:
            try:
                message = ws.receive()
                if message is None:
                    print(f"[DEBUG] 客户端断开连接（消息为 None）")
                    break

                data = json.loads(message)
                if 'workflow_type' in data:
                    # 更新客户端的工作流类型
                    old_type = ws.workflow_type
                    new_type = data['workflow_type']

                    # 验证新的 workflow_type
                    if new_type not in ['drawing', 'document_with_images', 'manim']:
                        print(f"[WARNING] 无效的工作流类型: {new_type}")
                        continue

                    # 只有当类型真正改变时才处理
                    if old_type != new_type:
                        ws.workflow_type = new_type

                        # 从旧的连接池中移除
                        if old_type in websocket_clients and ws in websocket_clients[old_type]:
                            websocket_clients[old_type].remove(ws)

                        # 添加到新的连接池
                        if ws.workflow_type not in websocket_clients:
                            websocket_clients[ws.workflow_type] = []
                        if ws not in websocket_clients[ws.workflow_type]:
                            websocket_clients[ws.workflow_type].append(ws)

                        print(f"[DEBUG] 客户端工作流类型变更: {old_type} -> {ws.workflow_type}")
                    else:
                        print(f"[DEBUG] 客户端工作流类型未改变: {old_type}")
            except ConnectionError as e:
                # 连接关闭时的正常情况
                print(f"[DEBUG] WebSocket 连接已关闭: {e}")
                break
            except Exception as e:
                # 其他异常情况
                error_msg = str(e)
                if '1005' in error_msg or 'Connection closed' in error_msg:
                    # 这是客户端断开连接的常见情况，不算错误
                    print(f"[DEBUG] 客户端断开连接: {e}")
                    break
                else:
                    print(f"[WARNING] 处理消息失败: {e}")
                    break

    except Exception as e:
        print(f"[DEBUG] WebSocket 错误: {e}")
    finally:
        # 从连接池中移除客户端
        if hasattr(ws, 'workflow_type') and ws.workflow_type in websocket_clients:
            if ws in websocket_clients[ws.workflow_type]:
                websocket_clients[ws.workflow_type].remove(ws)
        print(f"[DEBUG] WebSocket 客户端断开")

def run_drawing_workflow_thread(user_prompt):
    """在工作流线程中运行绘图工作流"""
    print(f"\n[DEBUG] ===== 绘图工作流线程启动 =====")
    print(f"[DEBUG] 用户提示词: '{user_prompt}'")

    # 重置停止标志
    reset_stop_flag('drawing')

    try:
        # 状态已在 /api/drawing/workflow 中重置，这里只需确认
        print(f"[DEBUG] 绘图工作流状态: {workflow_statuses['drawing']['status']}")

        # 创建工作流图
        def create_monitored_drawing_graph():
            """创建带监控的绘图工作流图"""
            from langgraph.graph import StateGraph, END

            # 原始节点函数
            from workflows.draw_pic import (
                refine_prompt, generate_code, execute_code,
                analyze_execution_result, fix_code_with_feedback, save_image
            )

            # 包装节点以添加进度报告
            def monitored_refine_prompt(state):
                # 检查停止标志
                if should_stop_workflow('drawing'):
                    print(f"[DEBUG] 工作流已被用户停止")
                    return {"error": "用户取消操作"}

                print(f"\n[DEBUG] >>> 节点 'refine_prompt' 开始执行")
                
                # 立即设置状态并发送更新
                workflow_statuses['drawing']['current_step'] = 'refine_prompt'
                workflow_statuses['drawing']['steps'].append({
                    'step': 'refine_prompt',
                    'name': DRAWING_STEP_NAMES['refine_prompt'],
                    'status': 'running',
                    'timestamp': datetime.now().isoformat()
                })
                update_and_emit_status('drawing')
                
                # 执行节点逻辑
                result = refine_prompt(state)
                
                # 节点完成时立即更新状态
                workflow_statuses['drawing']['steps'][-1]['status'] = 'completed'
                workflow_statuses['drawing']['steps'][-1]['completed_at'] = datetime.now().isoformat()
                update_and_emit_status('drawing')
                print(f"[DEBUG] <<< 节点 'refine_prompt' 执行完成")
                print(f"[DEBUG] 润色后的提示词: {result.get('refined_prompt', 'N/A')[:100]}...")
                return result

            def monitored_generate_code(state):
                # 检查停止标志
                if should_stop_workflow('drawing'):
                    print(f"[DEBUG] 工作流已被用户停止")
                    return {"error": "用户取消操作"}

                print(f"\n[DEBUG] >>> 节点 'generate_code' 开始执行")
                
                # 立即设置状态并发送更新
                workflow_statuses['drawing']['current_step'] = 'generate_code'
                workflow_statuses['drawing']['steps'].append({
                    'step': 'generate_code',
                    'name': DRAWING_STEP_NAMES['generate_code'],
                    'status': 'running',
                    'timestamp': datetime.now().isoformat()
                })
                update_and_emit_status('drawing')
                
                # 定义流式回调函数（支持内容类型）
                def stream_callback(content, content_type='content'):
                    emit_stream_content('drawing', 'generate_code', content, content_type)
                
                # 执行节点逻辑，传入流式回调
                result = generate_code(state, stream_callback=stream_callback)
                
                # 节点完成时立即更新状态
                if result.get('error'):
                    workflow_statuses['drawing']['steps'][-1]['status'] = 'error'
                    workflow_statuses['drawing']['steps'][-1]['error'] = result.get('error', '未知错误')
                else:
                    workflow_statuses['drawing']['steps'][-1]['status'] = 'completed'
                workflow_statuses['drawing']['steps'][-1]['completed_at'] = datetime.now().isoformat()
                update_and_emit_status('drawing')
                
                print(f"[DEBUG] <<< 节点 'generate_code' 执行完成")
                if result.get('error'):
                    print(f"[DEBUG] generate_code 返回错误: {result['error']}")
                else:
                    print(f"[DEBUG] 生成的代码长度: {len(result.get('generated_code', ''))} 字符")
                return result

            def monitored_execute_code(state):
                # 检查停止标志
                if should_stop_workflow('drawing'):
                    print(f"[DEBUG] 工作流已被用户停止")
                    return {"error": "用户取消操作"}

                print(f"\n[DEBUG] >>> 节点 'execute_code' 开始执行")
                
                # 立即设置状态并发送更新
                workflow_statuses['drawing']['current_step'] = 'execute_code'
                workflow_statuses['drawing']['steps'].append({
                    'step': 'execute_code',
                    'name': DRAWING_STEP_NAMES['execute_code'],
                    'status': 'running',
                    'timestamp': datetime.now().isoformat()
                })
                update_and_emit_status('drawing')
                
                # 执行节点逻辑
                result = execute_code(state)
                
                # 节点完成时立即更新状态
                if result.get('error'):
                    workflow_statuses['drawing']['steps'][-1]['status'] = 'error'
                    workflow_statuses['drawing']['steps'][-1]['error'] = result.get('error', '未知错误')
                else:
                    workflow_statuses['drawing']['steps'][-1]['status'] = 'completed'
                workflow_statuses['drawing']['steps'][-1]['completed_at'] = datetime.now().isoformat()
                update_and_emit_status('drawing')
                
                print(f"[DEBUG] <<< 节点 'execute_code' 执行完成")
                if result.get('error'):
                    print(f"[DEBUG] execute_code 返回错误: {result['error']}")
                else:
                    print(f"[DEBUG] 生成的图片路径: {result.get('image_path', 'N/A')}")
                return result

            def monitored_save_image(state):
                # 检查停止标志
                if should_stop_workflow('drawing'):
                    print(f"[DEBUG] 工作流已被用户停止")
                    return {"error": "用户取消操作"}

                print(f"\n[DEBUG] >>> 节点 'save_image' 开始执行")
                
                # 立即设置状态并发送更新
                workflow_statuses['drawing']['current_step'] = 'save_image'
                workflow_statuses['drawing']['steps'].append({
                    'step': 'save_image',
                    'name': DRAWING_STEP_NAMES['save_image'],
                    'status': 'running',
                    'timestamp': datetime.now().isoformat()
                })
                update_and_emit_status('drawing')
                
                # 执行节点逻辑
                result = save_image(state)
                
                # 节点完成时立即更新状态
                if result.get('error'):
                    workflow_statuses['drawing']['steps'][-1]['status'] = 'error'
                    workflow_statuses['drawing']['steps'][-1]['error'] = result.get('error', '未知错误')
                else:
                    workflow_statuses['drawing']['steps'][-1]['status'] = 'completed'
                workflow_statuses['drawing']['steps'][-1]['completed_at'] = datetime.now().isoformat()
                update_and_emit_status('drawing')
                
                print(f"[DEBUG] <<< 节点 'save_image' 执行完成")
                if result.get('error'):
                    print(f"[DEBUG] save_image 返回错误: {result['error']}")
                else:
                    print(f"[DEBUG] 图片大小: {result.get('image_size', 0)} 字节")
                return result

            def monitored_analyze_execution_result(state):
                # 检查停止标志
                if should_stop_workflow('drawing'):
                    print(f"[DEBUG] 工作流已被用户停止")
                    return {"error": "用户取消操作"}

                print(f"\n[DEBUG] >>> 节点 'analyze_execution_result' 开始执行")

                # 立即设置状态并发送更新
                workflow_statuses['drawing']['current_step'] = 'analyze_execution_result'
                workflow_statuses['drawing']['steps'].append({
                    'step': 'analyze_execution_result',
                    'name': DRAWING_STEP_NAMES['analyze_execution_result'],
                    'status': 'running',
                    'timestamp': datetime.now().isoformat()
                })
                update_and_emit_status('drawing')

                # 执行节点逻辑
                result = analyze_execution_result(state)

                # 节点完成时立即更新状态
                if result.get('error'):
                    workflow_statuses['drawing']['steps'][-1]['status'] = 'error'
                    workflow_statuses['drawing']['steps'][-1]['error'] = result.get('error', '未知错误')
                else:
                    workflow_statuses['drawing']['steps'][-1]['status'] = 'completed'
                workflow_statuses['drawing']['steps'][-1]['completed_at'] = datetime.now().isoformat()
                update_and_emit_status('drawing')

                print(f"[DEBUG] <<< 节点 'analyze_execution_result' 执行完成")
                retry_info = f" [重试 {result.get('retry_count', 0)}/{result.get('max_retries', 3)}]" if result.get('retry_count', 0) > 0 else ""
                if result.get('error'):
                    print(f"[DEBUG] analyze_execution_result 返回错误: {result['error']}")
                elif result.get('need_retry'):
                    print(f"[DEBUG] 需要重试{retry_info}，进入修复节点")
                else:
                    print(f"[DEBUG] 执行成功，准备保存图片")
                return result

            def monitored_fix_code_with_feedback(state):
                # 检查停止标志
                if should_stop_workflow('drawing'):
                    print(f"[DEBUG] 工作流已被用户停止")
                    return {"error": "用户取消操作"}

                print(f"\n[DEBUG] >>> 节点 'fix_code_with_feedback' 开始执行")

                # 立即设置状态并发送更新
                workflow_statuses['drawing']['current_step'] = 'fix_code_with_feedback'
                retry_count = state.get('retry_count', 1)
                max_retries = state.get('max_retries', 3)
                workflow_statuses['drawing']['steps'].append({
                    'step': 'fix_code_with_feedback',
                    'name': DRAWING_STEP_NAMES['fix_code_with_feedback'],
                    'status': 'running',
                    'timestamp': datetime.now().isoformat(),
                    'retry_info': {
                        'current': retry_count,
                        'max': max_retries
                    }
                })
                update_and_emit_status('drawing')

                # 定义流式回调函数
                def stream_callback(content, content_type='content'):
                    emit_stream_content('drawing', 'fix_code_with_feedback', content, content_type)

                # 执行节点逻辑，传入流式回调
                result = fix_code_with_feedback(state, stream_callback=stream_callback)

                # 节点完成时立即更新状态
                if result.get('error'):
                    workflow_statuses['drawing']['steps'][-1]['status'] = 'error'
                    workflow_statuses['drawing']['steps'][-1]['error'] = result.get('error', '未知错误')
                else:
                    workflow_statuses['drawing']['steps'][-1]['status'] = 'completed'
                workflow_statuses['drawing']['steps'][-1]['completed_at'] = datetime.now().isoformat()
                update_and_emit_status('drawing')

                print(f"[DEBUG] <<< 节点 'fix_code_with_feedback' 执行完成")
                if result.get('error'):
                    print(f"[DEBUG] fix_code_with_feedback 返回错误: {result['error']}")
                else:
                    print(f"[DEBUG] 修复后的代码长度: {len(result.get('generated_code', ''))} 字符")
                return result

            # 构建图（CodeAct模式：带反馈循环）
            workflow = StateGraph(GraphState)
            workflow.add_node("refine_prompt", monitored_refine_prompt)
            workflow.add_node("generate_code", monitored_generate_code)
            workflow.add_node("execute_code", monitored_execute_code)
            workflow.add_node("analyze_execution_result", monitored_analyze_execution_result)  # 新增
            workflow.add_node("fix_code_with_feedback", monitored_fix_code_with_feedback)    # 新增
            workflow.add_node("save_image", monitored_save_image)
            workflow.set_entry_point("refine_prompt")

            # 定义工作流边
            workflow.add_edge("refine_prompt", "generate_code")
            workflow.add_edge("generate_code", "execute_code")
            workflow.add_edge("execute_code", "analyze_execution_result")  # 修改：执行后先分析

            # 条件边：根据分析结果决定是保存还是重试
            def should_retry(state):
                """判断是否需要重试修复代码

                优先级顺序（重要！）：
                1. 先检查 need_retry - 如果需要重试，不管是否有错误都要进入修复流程
                2. 再检查 error - 如果有错误且不需要重试，结束工作流
                3. 否则保存图片
                """
                if state.get("need_retry", False):
                    # 需要修复代码，即使有旧错误也要进入修复流程
                    return "fix_code"
                if state.get("error"):
                    # 有错误信息且不再需要重试，结束工作流
                    return "end"
                return "save_image"

            workflow.add_conditional_edges(
                "analyze_execution_result",
                should_retry,
                {
                    "fix_code": "fix_code_with_feedback",  # 需要修复
                    "save_image": "save_image",            # 成功，保存图片
                    "end": END                              # 失败，结束
                }
            )

            # CodeAct反馈循环：修复后重新执行
            workflow.add_edge("fix_code_with_feedback", "execute_code")
            workflow.add_edge("save_image", END)

            return workflow.compile()

        graph = create_monitored_drawing_graph()
        print(f"[DEBUG] 绘图工作流图已创建并编译")

        # 运行工作流（使用流式执行）
        print(f"[DEBUG] 开始调用绘图工作流（流式模式）...")
        initial_state = {
            "user_prompt": user_prompt,
            "generated_code": "",
            "image_path": "",
            "image_size": 0,
            "error": "",
            # CodeAct 模式初始化字段
            "execution_output": "",
            "execution_success": False,
            "retry_count": 0,
            "max_retries": 3,
            "fix_feedback": "",
            "need_retry": False
        }
        print(f"[DEBUG] 初始状态: {initial_state}")

        # 使用流式执行
        result = {}
        try:
            for event in graph.stream(initial_state):
                # 检查停止标志
                if should_stop_workflow('drawing'):
                    print(f"[DEBUG] 检测到停止信号，中断工作流执行")
                    result["error"] = "用户取消操作"
                    break

                # event 是一个字典，包含节点名称和更新的状态
                for node_name, node_output in event.items():
                    print(f"[DEBUG] 节点 '{node_name}' 完成输出")
                    # 合并输出到结果中
                    result.update(node_output)

                    # 实时发送进度更新到前端
                    update_and_emit_status('drawing')

        except Exception as stream_error:
            print(f"[ERROR] 流式执行过程中出错: {str(stream_error)}")
            import traceback
            traceback.print_exc()
            result["error"] = str(stream_error)
            # 立即发送错误状态
            update_and_emit_status('drawing')

        print(f"\n[DEBUG] ===== 绘图工作流执行完成 =====")
        print(f"[DEBUG] 最终结果: {result}")

        # 更新最终状态
        if result.get("error"):
            print(f"[DEBUG] 绘图工作流执行失败，错误信息: {result['error']}")
            workflow_statuses['drawing']['status'] = 'error'
            workflow_statuses['drawing']['error'] = result['error']
        else:
            print(f"[DEBUG] 绘图工作流执行成功")
            workflow_statuses['drawing']['status'] = 'completed'
            # 从 image_path 中提取文件名（去掉 images/ 前缀）
            filename = os.path.basename(result['image_path'])
            workflow_statuses['drawing']['result'] = {
                'type': 'image',
                'image_path': result['image_path'],
                'image_url': f'/api/images/{filename}',
                'image_size': result['image_size'],
                'generated_code': result['generated_code']
            }
            print(f"[DEBUG] 结果图片路径: {result['image_path']}")
            print(f"[DEBUG] 结果图片 URL: /api/images/{filename}")

        workflow_statuses['drawing']['current_step'] = ''
        update_and_emit_status('drawing')
        print(f"[DEBUG] 绘图状态更新已发送到客户端")

    except Exception as e:
        import traceback
        print(f"\n[DEBUG] ===== 绘图工作流异常 =====")
        print(f"[DEBUG] 异常类型: {type(e).__name__}")
        print(f"[DEBUG] 异常信息: {str(e)}")
        print(f"[DEBUG] 完整堆栈跟踪:")
        traceback.print_exc()

        workflow_statuses['drawing']['status'] = 'error'
        workflow_statuses['drawing']['error'] = str(e)
        update_and_emit_status('drawing')
        print(f"[DEBUG] 绘图错误状态已发送到客户端")

# 向后兼容：保留旧的函数名
run_workflow_thread = run_drawing_workflow_thread

def run_document_with_images_thread(user_prompt):
    """在工作流线程中运行带图片的文档生成工作流"""
    print(f"\n[DEBUG] ===== 带图片的文档工作流线程启动 =====")
    print(f"[DEBUG] 用户提示词: '{user_prompt}'")

    # 重置停止标志
    reset_stop_flag('document_with_images')

    try:
        # 导入带图片的文档工作流
        from workflows.write_md_with_images import (
            create_graph as create_doc_with_images_graph,
            GraphState as DocWithImagesGraphState,
            set_image_progress_callback
        )

        # 添加步骤名称映射
        DOC_WITH_IMAGES_STEP_NAMES = {
            'refine_prompt': '润色写作需求',
            'generate_outline': '生成文档大纲',
            'generate_content': '生成文档内容',
            'identify_image_requests': '识别图片需求',
            'generate_images': '生成图表',
            'embed_images': '整合图片到文档',
            'save_document': '保存文档',
            'verify_document': '验证文档'
        }

        # 创建监控的工作流
        def create_monitored_doc_with_images_graph():
            """创建带监控的带图片文档工作流图"""
            from langgraph.graph import StateGraph, END

            # 导入原始节点函数
            from workflows.write_md_with_images import (
                refine_prompt, generate_outline, generate_content,
                identify_image_requests, generate_images, embed_images,
                save_document, verify_document
            )

            # 定义图片生成进度更新回调函数
            def image_progress_callback(current_index: int, total: int, description: str):
                """图片生成进度更新回调"""
                print(f"[DEBUG] 图片生成进度: {current_index}/{total} - {description}")

                # 更新当前步骤的进度信息
                with status_lock:
                    # 查找正在运行的 generate_images 步骤
                    for step in workflow_statuses['document_with_images']['steps']:
                        if step['step'] == 'generate_images' and step['status'] == 'running':
                            step['current_image_index'] = current_index
                            step['total_images'] = total
                            step['current_image_description'] = description
                            step['progress_text'] = f"正在生成第 {current_index}/{total} 张图片: {description}"
                            break

                # 立即发送进度更新
                update_and_emit_status('document_with_images')

            # 设置回调函数到工作流模块
            set_image_progress_callback(image_progress_callback)

            # 包装节点以添加进度报告
            def monitored_refine_prompt(state):
                # 检查停止标志
                if should_stop_workflow('document_with_images'):
                    print(f"[DEBUG] 工作流已被用户停止")
                    return {"error": "用户取消操作"}

                print(f"\n[DEBUG] >>> 带图片文档节点 'refine_prompt' 开始执行")
                
                # 立即设置状态并发送更新
                workflow_statuses['document_with_images']['current_step'] = 'refine_prompt'
                workflow_statuses['document_with_images']['steps'].append({
                    'step': 'refine_prompt',
                    'name': DOC_WITH_IMAGES_STEP_NAMES['refine_prompt'],
                    'status': 'running',
                    'timestamp': datetime.now().isoformat()
                })
                update_and_emit_status('document_with_images')
                
                # 执行节点逻辑
                result = refine_prompt(state)
                
                # 节点完成时立即更新状态
                if result.get('error'):
                    workflow_statuses['document_with_images']['steps'][-1]['status'] = 'error'
                    workflow_statuses['document_with_images']['steps'][-1]['error'] = result.get('error', '未知错误')
                else:
                    workflow_statuses['document_with_images']['steps'][-1]['status'] = 'completed'
                workflow_statuses['document_with_images']['steps'][-1]['completed_at'] = datetime.now().isoformat()
                update_and_emit_status('document_with_images')
                
                print(f"[DEBUG] <<< 带图片文档节点 'refine_prompt' 执行完成")
                return result

            def monitored_generate_outline(state):
                # 检查停止标志
                if should_stop_workflow('document_with_images'):
                    print(f"[DEBUG] 工作流已被用户停止")
                    return {"error": "用户取消操作"}

                print(f"\n[DEBUG] >>> 带图片文档节点 'generate_outline' 开始执行")
                
                # 立即设置状态并发送更新
                workflow_statuses['document_with_images']['current_step'] = 'generate_outline'
                workflow_statuses['document_with_images']['steps'].append({
                    'step': 'generate_outline',
                    'name': DOC_WITH_IMAGES_STEP_NAMES['generate_outline'],
                    'status': 'running',
                    'timestamp': datetime.now().isoformat()
                })
                update_and_emit_status('document_with_images')
                
                # 定义流式回调函数
                def stream_callback(content):
                    emit_stream_content('document_with_images', 'generate_outline', content)
                
                # 执行节点逻辑，传入流式回调
                result = generate_outline(state, stream_callback=stream_callback)
                
                # 节点完成时立即更新状态
                if result.get('error'):
                    workflow_statuses['document_with_images']['steps'][-1]['status'] = 'error'
                    workflow_statuses['document_with_images']['steps'][-1]['error'] = result.get('error', '未知错误')
                else:
                    workflow_statuses['document_with_images']['steps'][-1]['status'] = 'completed'
                workflow_statuses['document_with_images']['steps'][-1]['completed_at'] = datetime.now().isoformat()
                update_and_emit_status('document_with_images')
                
                print(f"[DEBUG] <<< 带图片文档节点 'generate_outline' 执行完成")
                return result

            def monitored_generate_content(state):
                # 检查停止标志
                if should_stop_workflow('document_with_images'):
                    print(f"[DEBUG] 工作流已被用户停止")
                    return {"error": "用户取消操作"}

                print(f"\n[DEBUG] >>> 带图片文档节点 'generate_content' 开始执行")
                
                # 立即设置状态并发送更新
                workflow_statuses['document_with_images']['current_step'] = 'generate_content'
                workflow_statuses['document_with_images']['steps'].append({
                    'step': 'generate_content',
                    'name': DOC_WITH_IMAGES_STEP_NAMES['generate_content'],
                    'status': 'running',
                    'timestamp': datetime.now().isoformat()
                })
                update_and_emit_status('document_with_images')
                
                # 定义流式回调函数
                def stream_callback(content):
                    emit_stream_content('document_with_images', 'generate_content', content)
                
                # 执行节点逻辑，传入流式回调
                result = generate_content(state, stream_callback=stream_callback)
                
                # 节点完成时立即更新状态
                if result.get('error'):
                    workflow_statuses['document_with_images']['steps'][-1]['status'] = 'error'
                    workflow_statuses['document_with_images']['steps'][-1]['error'] = result.get('error', '未知错误')
                else:
                    workflow_statuses['document_with_images']['steps'][-1]['status'] = 'completed'
                workflow_statuses['document_with_images']['steps'][-1]['completed_at'] = datetime.now().isoformat()
                update_and_emit_status('document_with_images')
                
                print(f"[DEBUG] <<< 带图片文档节点 'generate_content' 执行完成")
                return result

            def monitored_identify_image_requests(state):
                # 检查停止标志
                if should_stop_workflow('document_with_images'):
                    print(f"[DEBUG] 工作流已被用户停止")
                    return {"error": "用户取消操作"}

                print(f"\n[DEBUG] >>> 带图片文档节点 'identify_image_requests' 开始执行")
                
                # 立即设置状态并发送更新
                workflow_statuses['document_with_images']['current_step'] = 'identify_image_requests'
                workflow_statuses['document_with_images']['steps'].append({
                    'step': 'identify_image_requests',
                    'name': DOC_WITH_IMAGES_STEP_NAMES['identify_image_requests'],
                    'status': 'running',
                    'timestamp': datetime.now().isoformat()
                })
                update_and_emit_status('document_with_images')
                
                # 执行节点逻辑
                result = identify_image_requests(state)
                
                # 节点完成时立即更新状态
                if result.get('error'):
                    workflow_statuses['document_with_images']['steps'][-1]['status'] = 'error'
                    workflow_statuses['document_with_images']['steps'][-1]['error'] = result.get('error', '未知错误')
                else:
                    workflow_statuses['document_with_images']['steps'][-1]['status'] = 'completed'
                workflow_statuses['document_with_images']['steps'][-1]['completed_at'] = datetime.now().isoformat()
                update_and_emit_status('document_with_images')
                
                print(f"[DEBUG] <<< 带图片文档节点 'identify_image_requests' 执行完成")
                return result

            def monitored_generate_images(state):
                # 检查停止标志
                if should_stop_workflow('document_with_images'):
                    print(f"[DEBUG] 工作流已被用户停止")
                    return {"error": "用户取消操作"}

                print(f"\n[DEBUG] >>> 带图片文档节点 'generate_images' 开始执行")
                
                # 立即设置状态并发送更新
                workflow_statuses['document_with_images']['current_step'] = 'generate_images'
                workflow_statuses['document_with_images']['steps'].append({
                    'step': 'generate_images',
                    'name': DOC_WITH_IMAGES_STEP_NAMES['generate_images'],
                    'status': 'running',
                    'timestamp': datetime.now().isoformat()
                })
                update_and_emit_status('document_with_images')
                
                # 执行节点逻辑
                result = generate_images(state)
                
                # 节点完成时立即更新状态
                if result.get('error'):
                    workflow_statuses['document_with_images']['steps'][-1]['status'] = 'error'
                    workflow_statuses['document_with_images']['steps'][-1]['error'] = result.get('error', '未知错误')
                else:
                    workflow_statuses['document_with_images']['steps'][-1]['status'] = 'completed'
                workflow_statuses['document_with_images']['steps'][-1]['completed_at'] = datetime.now().isoformat()
                update_and_emit_status('document_with_images')
                
                print(f"[DEBUG] <<< 带图片文档节点 'generate_images' 执行完成")
                return result

            def monitored_embed_images(state):
                # 检查停止标志
                if should_stop_workflow('document_with_images'):
                    print(f"[DEBUG] 工作流已被用户停止")
                    return {"error": "用户取消操作"}

                print(f"\n[DEBUG] >>> 带图片文档节点 'embed_images' 开始执行")
                
                # 立即设置状态并发送更新
                workflow_statuses['document_with_images']['current_step'] = 'embed_images'
                workflow_statuses['document_with_images']['steps'].append({
                    'step': 'embed_images',
                    'name': DOC_WITH_IMAGES_STEP_NAMES['embed_images'],
                    'status': 'running',
                    'timestamp': datetime.now().isoformat()
                })
                update_and_emit_status('document_with_images')
                
                # 执行节点逻辑
                result = embed_images(state)
                
                # 节点完成时立即更新状态
                if result.get('error'):
                    workflow_statuses['document_with_images']['steps'][-1]['status'] = 'error'
                    workflow_statuses['document_with_images']['steps'][-1]['error'] = result.get('error', '未知错误')
                else:
                    workflow_statuses['document_with_images']['steps'][-1]['status'] = 'completed'
                workflow_statuses['document_with_images']['steps'][-1]['completed_at'] = datetime.now().isoformat()
                update_and_emit_status('document_with_images')
                
                print(f"[DEBUG] <<< 带图片文档节点 'embed_images' 执行完成")
                return result

            def monitored_save_document(state):
                # 检查停止标志
                if should_stop_workflow('document_with_images'):
                    print(f"[DEBUG] 工作流已被用户停止")
                    return {"error": "用户取消操作"}

                print(f"\n[DEBUG] >>> 带图片文档节点 'save_document' 开始执行")
                
                # 立即设置状态并发送更新
                workflow_statuses['document_with_images']['current_step'] = 'save_document'
                workflow_statuses['document_with_images']['steps'].append({
                    'step': 'save_document',
                    'name': DOC_WITH_IMAGES_STEP_NAMES['save_document'],
                    'status': 'running',
                    'timestamp': datetime.now().isoformat()
                })
                update_and_emit_status('document_with_images')
                
                # 执行节点逻辑
                result = save_document(state)
                
                # 节点完成时立即更新状态
                if result.get('error'):
                    workflow_statuses['document_with_images']['steps'][-1]['status'] = 'error'
                    workflow_statuses['document_with_images']['steps'][-1]['error'] = result.get('error', '未知错误')
                else:
                    workflow_statuses['document_with_images']['steps'][-1]['status'] = 'completed'
                workflow_statuses['document_with_images']['steps'][-1]['completed_at'] = datetime.now().isoformat()
                update_and_emit_status('document_with_images')
                
                print(f"[DEBUG] <<< 带图片文档节点 'save_document' 执行完成")
                return result

            def monitored_verify_document(state):
                # 检查停止标志
                if should_stop_workflow('document_with_images'):
                    print(f"[DEBUG] 工作流已被用户停止")
                    return {"error": "用户取消操作"}

                print(f"\n[DEBUG] >>> 带图片文档节点 'verify_document' 开始执行")
                
                # 立即设置状态并发送更新
                workflow_statuses['document_with_images']['current_step'] = 'verify_document'
                workflow_statuses['document_with_images']['steps'].append({
                    'step': 'verify_document',
                    'name': DOC_WITH_IMAGES_STEP_NAMES['verify_document'],
                    'status': 'running',
                    'timestamp': datetime.now().isoformat()
                })
                update_and_emit_status('document_with_images')
                
                # 执行节点逻辑
                result = verify_document(state)
                
                # 节点完成时立即更新状态
                if result.get('error'):
                    workflow_statuses['document_with_images']['steps'][-1]['status'] = 'error'
                    workflow_statuses['document_with_images']['steps'][-1]['error'] = result.get('error', '未知错误')
                else:
                    workflow_statuses['document_with_images']['steps'][-1]['status'] = 'completed'
                workflow_statuses['document_with_images']['steps'][-1]['completed_at'] = datetime.now().isoformat()
                update_and_emit_status('document_with_images')
                
                print(f"[DEBUG] <<< 带图片文档节点 'verify_document' 执行完成")
                return result

            # 构建图
            workflow = StateGraph(DocWithImagesGraphState)
            workflow.add_node("refine_prompt", monitored_refine_prompt)
            workflow.add_node("generate_outline", monitored_generate_outline)
            workflow.add_node("generate_content", monitored_generate_content)
            workflow.add_node("identify_image_requests", monitored_identify_image_requests)
            workflow.add_node("generate_images", monitored_generate_images)
            workflow.add_node("embed_images", monitored_embed_images)
            workflow.add_node("save_document", monitored_save_document)
            workflow.add_node("verify_document", monitored_verify_document)
            workflow.set_entry_point("refine_prompt")
            workflow.add_edge("refine_prompt", "generate_outline")
            workflow.add_edge("generate_outline", "generate_content")
            workflow.add_edge("generate_content", "identify_image_requests")

            # 条件边：判断是否需要生成图片
            def monitored_should_generate_images(state):
                """判断是否需要生成图片"""
                image_requests = state.get("image_requests", [])
                has_images = bool(image_requests)

                if has_images:
                    print(f"[INFO] 检测到 {len(image_requests)} 个图片需求，进入生图流程")
                    return "generate_images"
                else:
                    print(f"[INFO] 无图片需求，跳过生图流程，直接保存文档")
                    # 为跳过的步骤添加 skipped 状态记录
                    skipped_steps = [
                        ('generate_images', '生成图表'),
                        ('embed_images', '整合图片到文档')
                    ]
                    for step_id in skipped_steps:
                        workflow_statuses['document_with_images']['steps'].append({
                            'step': step_id,
                            'name': DOC_WITH_IMAGES_STEP_NAMES[step_id],
                            'status': 'skipped',
                            'timestamp': datetime.now().isoformat(),
                            'completed_at': datetime.now().isoformat()
                        })
                    update_and_emit_status('document_with_images')
                    return "save_document"

            # 使用条件边替代固定边
            workflow.add_conditional_edges(
                "identify_image_requests",
                monitored_should_generate_images,
                {
                    "generate_images": "generate_images",
                    "save_document": "save_document"
                }
            )

            workflow.add_edge("generate_images", "embed_images")
            workflow.add_edge("embed_images", "save_document")
            workflow.add_edge("save_document", "verify_document")
            workflow.add_edge("verify_document", END)

            return workflow.compile()

        graph = create_monitored_doc_with_images_graph()
        print(f"[DEBUG] 带图片的文档工作流图已创建并编译")

        print(f"[DEBUG] 开始调用带图片的文档工作流（流式模式）...")
        initial_state = {
            "user_prompt": user_prompt,
            "refined_prompt": "",
            "document_outline": "",
            "markdown_content": "",
            "image_requests": [],
            "generated_images": [],
            "final_content": "",
            "output_path": "",
            "file_size": 0,
            "error": ""
        }
        print(f"[DEBUG] 初始状态: {initial_state}")

        # 使用流式执行
        result = {}
        try:
            for event in graph.stream(initial_state):
                # 检查停止标志
                if should_stop_workflow('document_with_images'):
                    print(f"[DEBUG] 检测到停止信号，中断工作流执行")
                    result["error"] = "用户取消操作"
                    break

                # event 是一个字典，包含节点名称和更新的状态
                for node_name, node_output in event.items():
                    print(f"[DEBUG] 节点 '{node_name}' 完成输出")
                    # 合并输出到结果中
                    result.update(node_output)

                    # 实时发送进度更新到前端
                    update_and_emit_status('document_with_images')

        except Exception as stream_error:
            print(f"[ERROR] 流式执行过程中出错: {str(stream_error)}")
            import traceback
            traceback.print_exc()
            result["error"] = str(stream_error)
            # 立即发送错误状态
            update_and_emit_status('document_with_images')

        print(f"\n[DEBUG] ===== 带图片的文档工作流执行完成 =====")
        print(f"[DEBUG] 最终结果: {result}")

        if result.get("error"):
            print(f"[DEBUG] 带图片的文档工作流执行失败，错误信息: {result['error']}")
            workflow_statuses['document_with_images']['status'] = 'error'
            workflow_statuses['document_with_images']['error'] = result['error']
        else:
            print(f"[DEBUG] 带图片的文档工作流执行成功")
            workflow_statuses['document_with_images']['status'] = 'completed'
            filename = os.path.basename(result['output_path'])
            workflow_statuses['document_with_images']['result'] = {
                'type': 'document_with_images',
                'path': result['output_path'],
                'filename': filename,
                'url': f'/api/documents/{filename}',
                'size': result['file_size'],
                'content': result.get('final_content', ''),
                'outline': result.get('document_outline', ''),
                'images': result.get('generated_images', []),
                'image_count': len(result.get('generated_images', []))
            }
            print(f"[DEBUG] 结果文档路径: {result['output_path']}")
            print(f"[DEBUG] 结果文档 URL: /api/documents/{filename}")
            print(f"[DEBUG] 生成图片数: {len(result.get('generated_images', []))}")

        workflow_statuses['document_with_images']['current_step'] = ''
        update_and_emit_status('document_with_images')
        print(f"[DEBUG] 带图片的文档状态更新已发送到客户端")

    except Exception as e:
        import traceback
        print(f"\n[DEBUG] ===== 带图片的文档工作流异常 =====")
        print(f"[DEBUG] 异常类型: {type(e).__name__}")
        print(f"[DEBUG] 异常信息: {str(e)}")
        print(f"[DEBUG] 完整堆栈跟踪:")
        traceback.print_exc()

        workflow_statuses['document_with_images']['status'] = 'error'
        workflow_statuses['document_with_images']['error'] = str(e)
        update_and_emit_status('document_with_images')
        print(f"[DEBUG] 带图片的文档错误状态已发送到客户端")

def run_manim_workflow_thread(user_prompt, quality):
    """在工作流线程中运行 Manim 动画工作流"""
    print(f"\n[DEBUG] ===== Manim 动画工作流线程启动 =====")
    print(f"[DEBUG] 用户提示词: '{user_prompt}'")
    print(f"[DEBUG] 渲染质量: '{quality}'")

    # 重置停止标志
    reset_stop_flag('manim')

    try:
        # 导入 Manim 动画工作流
        from workflows.manim_gen import create_graph as create_manim_graph, ManimState

        # 创建监控的工作流
        def create_monitored_manim_graph():
            """创建带监控的 Manim 动画工作流图"""
            from langgraph.graph import StateGraph, END

            # 导入原始节点函数
            from workflows.manim_gen import (
                refine_prompt, generate_code, execute_code, save_video
            )

            # 包装节点以添加进度报告
            def monitored_refine_prompt(state):
                # 检查停止标志
                if should_stop_workflow('manim'):
                    print(f"[DEBUG] 工作流已被用户停止")
                    return {"error": "用户取消操作"}

                print(f"\n[DEBUG] >>> Manim 节点 'refine_prompt' 开始执行")

                workflow_statuses['manim']['current_step'] = 'refine_prompt'
                workflow_statuses['manim']['steps'].append({
                    'step': 'refine_prompt',
                    'name': MANIM_STEP_NAMES['refine_prompt'],
                    'status': 'running',
                    'timestamp': datetime.now().isoformat()
                })
                update_and_emit_status('manim')

                result = refine_prompt(state)

                if result.get('error'):
                    workflow_statuses['manim']['steps'][-1]['status'] = 'error'
                    workflow_statuses['manim']['steps'][-1]['error'] = result.get('error', '未知错误')
                else:
                    workflow_statuses['manim']['steps'][-1]['status'] = 'completed'
                    workflow_statuses['manim']['steps'][-1]['completed_at'] = datetime.now().isoformat()
                update_and_emit_status('manim')

                print(f"[DEBUG] <<< Manim 节点 'refine_prompt' 执行完成")
                return result

            def monitored_generate_code(state):
                # 检查停止标志
                if should_stop_workflow('manim'):
                    print(f"[DEBUG] 工作流已被用户停止")
                    return {"error": "用户取消操作"}

                print(f"\n[DEBUG] >>> Manim 节点 'generate_code' 开始执行")

                workflow_statuses['manim']['current_step'] = 'generate_code'
                workflow_statuses['manim']['steps'].append({
                    'step': 'generate_code',
                    'name': MANIM_STEP_NAMES['generate_code'],
                    'status': 'running',
                    'timestamp': datetime.now().isoformat()
                })
                update_and_emit_status('manim')

                def stream_callback(content):
                    emit_stream_content('manim', 'generate_code', content)

                result = generate_code(state, stream_callback=stream_callback)

                if result.get('error'):
                    workflow_statuses['manim']['steps'][-1]['status'] = 'error'
                    workflow_statuses['manim']['steps'][-1]['error'] = result.get('error', '未知错误')
                else:
                    workflow_statuses['manim']['steps'][-1]['status'] = 'completed'
                    workflow_statuses['manim']['steps'][-1]['completed_at'] = datetime.now().isoformat()
                update_and_emit_status('manim')

                print(f"[DEBUG] <<< Manim 节点 'generate_code' 执行完成")
                if result.get('error'):
                    print(f"[DEBUG] generate_code 返回错误: {result['error']}")
                else:
                    print(f"[DEBUG] 生成的代码长度: {len(result.get('generated_code', ''))} 字符")
                return result

            def monitored_execute_code(state):
                # 检查停止标志
                if should_stop_workflow('manim'):
                    print(f"[DEBUG] 工作流已被用户停止")
                    return {"error": "用户取消操作"}

                print(f"\n[DEBUG] >>> Manim 节点 'execute_code' 开始执行")

                workflow_statuses['manim']['current_step'] = 'execute_code'
                workflow_statuses['manim']['steps'].append({
                    'step': 'execute_code',
                    'name': MANIM_STEP_NAMES['execute_code'],
                    'status': 'running',
                    'timestamp': datetime.now().isoformat()
                })
                update_and_emit_status('manim')

                result = execute_code(state)

                if result.get('error'):
                    workflow_statuses['manim']['steps'][-1]['status'] = 'error'
                    workflow_statuses['manim']['steps'][-1]['error'] = result.get('error', '未知错误')
                else:
                    workflow_statuses['manim']['steps'][-1]['status'] = 'completed'
                    workflow_statuses['manim']['steps'][-1]['completed_at'] = datetime.now().isoformat()
                update_and_emit_status('manim')

                print(f"[DEBUG] <<< Manim 节点 'execute_code' 执行完成")
                if result.get('error'):
                    print(f"[DEBUG] execute_code 返回错误: {result['error']}")
                else:
                    print(f"[DEBUG] 生成的视频路径: {result.get('video_path', 'N/A')}")
                return result

            def monitored_save_video(state):
                # 检查停止标志
                if should_stop_workflow('manim'):
                    print(f"[DEBUG] 工作流已被用户停止")
                    return {"error": "用户取消操作"}

                print(f"\n[DEBUG] >>> Manim 节点 'save_video' 开始执行")

                workflow_statuses['manim']['current_step'] = 'save_video'
                workflow_statuses['manim']['steps'].append({
                    'step': 'save_video',
                    'name': MANIM_STEP_NAMES['save_video'],
                    'status': 'running',
                    'timestamp': datetime.now().isoformat()
                })
                update_and_emit_status('manim')

                result = save_video(state)

                if result.get('error'):
                    workflow_statuses['manim']['steps'][-1]['status'] = 'error'
                    workflow_statuses['manim']['steps'][-1]['error'] = result.get('error', '未知错误')
                else:
                    workflow_statuses['manim']['steps'][-1]['status'] = 'completed'
                    workflow_statuses['manim']['steps'][-1]['completed_at'] = datetime.now().isoformat()
                update_and_emit_status('manim')

                print(f"[DEBUG] <<< Manim 节点 'save_video' 执行完成")
                if result.get('error'):
                    print(f"[DEBUG] save_video 返回错误: {result['error']}")
                else:
                    print(f"[DEBUG] 视频大小: {result.get('video_size', 0)} 字节")
                return result

            # 构建图
            workflow = StateGraph(ManimState)
            workflow.add_node("refine_prompt", monitored_refine_prompt)
            workflow.add_node("generate_code", monitored_generate_code)
            workflow.add_node("execute_code", monitored_execute_code)
            workflow.add_node("save_video", monitored_save_video)
            workflow.set_entry_point("refine_prompt")
            workflow.add_edge("refine_prompt", "generate_code")
            workflow.add_edge("generate_code", "execute_code")
            workflow.add_edge("execute_code", "save_video")
            workflow.add_edge("save_video", END)

            return workflow.compile()

        graph = create_monitored_manim_graph()
        print(f"[DEBUG] Manim 工作流图已创建并编译")

        print(f"[DEBUG] 开始调用 Manim 工作流（流式模式）...")
        initial_state = {
            "user_prompt": user_prompt,
            "refined_prompt": "",
            "generated_code": "",
            "video_path": "",
            "video_size": 0,
            "render_quality": quality,
            "error": ""
        }
        print(f"[DEBUG] 初始状态: {initial_state}")

        # 使用流式执行
        result = {}
        try:
            for event in graph.stream(initial_state):
                # 检查停止标志
                if should_stop_workflow('manim'):
                    print(f"[DEBUG] 检测到停止信号，中断工作流执行")
                    result["error"] = "用户取消操作"
                    break

                for node_name, node_output in event.items():
                    print(f"[DEBUG] 节点 '{node_name}' 完成输出")
                    result.update(node_output)

                    update_and_emit_status('manim')

        except Exception as stream_error:
            print(f"[ERROR] 流式执行过程中出错: {str(stream_error)}")
            import traceback
            traceback.print_exc()
            result["error"] = str(stream_error)
            update_and_emit_status('manim')

        print(f"\n[DEBUG] ===== Manim 工作流执行完成 =====")
        print(f"[DEBUG] 最终结果: {result}")

        # 更新最终状态
        if result.get("error"):
            print(f"[DEBUG] Manim 工作流执行失败，错误信息: {result['error']}")
            workflow_statuses['manim']['status'] = 'error'
            workflow_statuses['manim']['error'] = result['error']
        else:
            print(f"[DEBUG] Manim 工作流执行成功")
            workflow_statuses['manim']['status'] = 'completed'
            filename = os.path.basename(result['video_path'])
            workflow_statuses['manim']['result'] = {
                'type': 'video',
                'video_path': result['video_path'],
                'video_url': f'/api/manim/videos/{filename}',
                'video_size': result['video_size'],
                'generated_code': result['generated_code']
            }
            print(f"[DEBUG] 结果视频路径: {result['video_path']}")
            print(f"[DEBUG] 结果视频 URL: /api/manim/videos/{filename}")

        workflow_statuses['manim']['current_step'] = ''
        update_and_emit_status('manim')
        print(f"[DEBUG] Manim 状态更新已发送到客户端")

    except Exception as e:
        import traceback
        print(f"\n[DEBUG] ===== Manim 动画工作流异常 =====")
        print(f"[DEBUG] 异常类型: {type(e).__name__}")
        print(f"[DEBUG] 异常信息: {str(e)}")
        print(f"[DEBUG] 完整堆栈跟踪:")
        traceback.print_exc()

        workflow_statuses['manim']['status'] = 'error'
        workflow_statuses['manim']['error'] = str(e)
        update_and_emit_status('manim')
        print(f"[DEBUG] Manim 错误状态已发送到客户端")

if __name__ == '__main__':
    from werkzeug.serving import run_simple
    print("Starting Web server...")
    print("Drawing mode: http://localhost:5001")
    print("Document mode: http://localhost:5001")
    # 开发环境使用自动重载，生产环境可设置为 False
    run_simple('0.0.0.0', 5001, app, use_reloader=False, use_debugger=False, use_evalex=False, threaded=True)
