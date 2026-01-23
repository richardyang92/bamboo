from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
import os
import threading
import time
from draw_pic import create_graph, GraphState
from datetime import datetime
import eventlet

# 初始化 Flask 应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*")

# 全局变量存储工作流状态（支持多个工作流类型）
workflow_statuses = {
    'drawing': {
        'status': 'idle',
        'current_step': '',
        'steps': [],
        'result': None,
        'error': None
    },
    'document': {
        'status': 'idle',
        'current_step': '',
        'steps': [],
        'result': None,
        'error': None
    }
}

# 为了向后兼容，保留旧的 workflow_status 引用
workflow_status = workflow_statuses['drawing']

# 状态映射
DRAWING_STEP_NAMES = {
    'refine_prompt': '润色提示词',
    'generate_code': '生成绘图代码',
    'execute_code': '执行绘图代码',
    'save_image': '验证图片保存'
}

DOCUMENT_STEP_NAMES = {
    'refine_prompt': '润色写作需求',
    'generate_outline': '生成文档大纲',
    'generate_content': '生成文档内容',
    'save_document': '保存文档',
    'verify_document': '验证文档'
}

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/history')
def history():
    """历史页面"""
    return render_template('history.html')

@app.route('/api/workflow', methods=['POST'])
def run_workflow():
    """启动绘图工作流（向后兼容）"""
    return run_drawing_workflow()

@app.route('/api/drawing/workflow', methods=['POST'])
def run_drawing_workflow():
    """启动绘图工作流"""
    data = request.json
    user_prompt = data.get('prompt', '')

    if not user_prompt:
        return jsonify({'error': '请输入绘图需求'}), 400

    # 立即更新状态为运行中，提供即时反馈
    workflow_statuses['drawing'] = {
        'status': 'running',
        'current_step': '',
        'steps': [],
        'result': None,
        'error': None
    }

    # 立即推送状态到客户端，确保无延迟
    socketio.emit('status_update', {'type': 'drawing', **workflow_statuses['drawing']})
    socketio.sleep(0)  # 强制立即发送

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
    if os.path.exists('images'):
        for file in os.listdir('images'):
            if file.startswith('plot_') and file.endswith('.png'):
                filepath = os.path.join('images', file)
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
    return send_from_directory('images', filename)

@app.route('/api/images/<filename>', methods=['DELETE'])
def delete_image(filename):
    """删除图片文件"""
    try:
        filepath = os.path.join('images', filename)
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
    socketio.emit('status_update', {'type': 'drawing', **workflow_statuses['drawing']})
    socketio.sleep(0)  # 立即发送消息
    return jsonify({'message': '绘图历史记录已清除'})

# ==================== 文档工作流端点 ====================

@app.route('/api/document/workflow', methods=['POST'])
def run_document_workflow():
    """启动文档生成工作流"""
    data = request.json
    user_prompt = data.get('prompt', '')
    options = data.get('options', {})

    if not user_prompt:
        return jsonify({'error': '请输入文档主题'}), 400

    # 立即更新状态为运行中，提供即时反馈
    workflow_statuses['document'] = {
        'status': 'running',
        'current_step': '',
        'steps': [],
        'result': None,
        'error': None
    }

    # 立即推送状态到客户端，确保无延迟
    socketio.emit('status_update', {'type': 'document', **workflow_statuses['document']})
    socketio.sleep(0)  # 强制立即发送

    # 在新线程中运行工作流
    thread = threading.Thread(target=run_document_workflow_thread, args=(user_prompt, options))
    thread.daemon = True
    thread.start()

    return jsonify({'message': '文档生成工作流已启动'})

@app.route('/api/documents')
def list_documents():
    """列出所有生成的文档"""
    doc_files = []
    if os.path.exists('docs'):
        for file in os.listdir('docs'):
            if file.startswith('doc_') and file.endswith('.md'):
                filepath = os.path.join('docs', file)
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

@app.route('/api/documents/<filename>')
def get_document(filename):
    """获取文档内容"""
    return send_from_directory('docs', filename)

@app.route('/api/documents/<filename>/content')
def get_document_content(filename):
    """获取文档的文本内容"""
    try:
        filepath = os.path.join('docs', filename)
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
        filepath = os.path.join('docs', filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            return jsonify({'message': '文档已删除'})
        else:
            return jsonify({'error': '文件不存在'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== 统一历史记录端点 ====================

@app.route('/api/history')
def list_history():
    """列出所有项目（图片 + 文档）"""
    items = []

    # 添加图片
    if os.path.exists('images'):
        for file in os.listdir('images'):
            if file.startswith('plot_') and file.endswith('.png'):
                filepath = os.path.join('images', file)
                items.append({
                    'type': 'image',
                    'name': file,
                    'url': f'/api/images/{file}',
                    'size': os.path.getsize(filepath),
                    'created': os.path.getmtime(filepath)
                })

    # 添加文档
    if os.path.exists('docs'):
        for file in os.listdir('docs'):
            if file.startswith('doc_') and file.endswith('.md'):
                filepath = os.path.join('docs', file)
                items.append({
                    'type': 'document',
                    'name': file,
                    'url': f'/api/documents/{file}',
                    'size': os.path.getsize(filepath),
                    'created': os.path.getmtime(filepath)
                })

    # 按创建时间排序
    items.sort(key=lambda x: x['created'], reverse=True)
    return jsonify(items)

def run_drawing_workflow_thread(user_prompt):
    """在工作流线程中运行绘图工作流"""
    print(f"\n[DEBUG] ===== 绘图工作流线程启动 =====")
    print(f"[DEBUG] 用户提示词: '{user_prompt}'")

    try:
        # 状态已在 /api/drawing/workflow 中重置，这里只需确认
        print(f"[DEBUG] 绘图工作流状态: {workflow_statuses['drawing']['status']}")

        # 创建工作流图
        def create_monitored_drawing_graph():
            """创建带监控的绘图工作流图"""
            from langgraph.graph import StateGraph, END

            # 原始节点函数
            from draw_pic import refine_prompt, generate_code, execute_code, save_image

            # 包装节点以添加进度报告
            def monitored_refine_prompt(state):
                print(f"\n[DEBUG] >>> 节点 'refine_prompt' 开始执行")
                workflow_statuses['drawing']['current_step'] = 'refine_prompt'
                workflow_statuses['drawing']['steps'].append({
                    'step': 'refine_prompt',
                    'name': DRAWING_STEP_NAMES['refine_prompt'],
                    'status': 'running',
                    'timestamp': datetime.now().isoformat()
                })
                socketio.emit('status_update', {'type': 'drawing', **workflow_statuses['drawing']})
                socketio.sleep(0)  # 立即发送消息
                result = refine_prompt(state)
                workflow_statuses['drawing']['steps'][-1]['status'] = 'completed'
                socketio.emit('status_update', {'type': 'drawing', **workflow_statuses['drawing']})
                socketio.sleep(0)  # 立即发送消息
                print(f"[DEBUG] <<< 节点 'refine_prompt' 执行完成")
                print(f"[DEBUG] 润色后的提示词: {result.get('refined_prompt', 'N/A')[:100]}...")
                return result

            def monitored_generate_code(state):
                print(f"\n[DEBUG] >>> 节点 'generate_code' 开始执行")
                workflow_statuses['drawing']['current_step'] = 'generate_code'
                workflow_statuses['drawing']['steps'].append({
                    'step': 'generate_code',
                    'name': DRAWING_STEP_NAMES['generate_code'],
                    'status': 'running',
                    'timestamp': datetime.now().isoformat()
                })
                socketio.emit('status_update', {'type': 'drawing', **workflow_statuses['drawing']})
                socketio.sleep(0)  # 立即发送消息
                result = generate_code(state)
                workflow_statuses['drawing']['steps'][-1]['status'] = 'completed'
                socketio.emit('status_update', {'type': 'drawing', **workflow_statuses['drawing']})
                socketio.sleep(0)  # 立即发送消息
                print(f"[DEBUG] <<< 节点 'generate_code' 执行完成")
                if result.get('error'):
                    print(f"[DEBUG] generate_code 返回错误: {result['error']}")
                else:
                    print(f"[DEBUG] 生成的代码长度: {len(result.get('generated_code', ''))} 字符")
                return result

            def monitored_execute_code(state):
                print(f"\n[DEBUG] >>> 节点 'execute_code' 开始执行")
                workflow_statuses['drawing']['current_step'] = 'execute_code'
                workflow_statuses['drawing']['steps'].append({
                    'step': 'execute_code',
                    'name': DRAWING_STEP_NAMES['execute_code'],
                    'status': 'running',
                    'timestamp': datetime.now().isoformat()
                })
                socketio.emit('status_update', {'type': 'drawing', **workflow_statuses['drawing']})
                socketio.sleep(0)  # 立即发送消息
                result = execute_code(state)
                workflow_statuses['drawing']['steps'][-1]['status'] = 'completed'
                socketio.emit('status_update', {'type': 'drawing', **workflow_statuses['drawing']})
                socketio.sleep(0)  # 立即发送消息
                print(f"[DEBUG] <<< 节点 'execute_code' 执行完成")
                if result.get('error'):
                    print(f"[DEBUG] execute_code 返回错误: {result['error']}")
                else:
                    print(f"[DEBUG] 生成的图片路径: {result.get('image_path', 'N/A')}")
                return result

            def monitored_save_image(state):
                print(f"\n[DEBUG] >>> 节点 'save_image' 开始执行")
                workflow_statuses['drawing']['current_step'] = 'save_image'
                workflow_statuses['drawing']['steps'].append({
                    'step': 'save_image',
                    'name': DRAWING_STEP_NAMES['save_image'],
                    'status': 'running',
                    'timestamp': datetime.now().isoformat()
                })
                socketio.emit('status_update', {'type': 'drawing', **workflow_statuses['drawing']})
                socketio.sleep(0)  # 立即发送消息
                result = save_image(state)
                workflow_statuses['drawing']['steps'][-1]['status'] = 'completed'
                socketio.emit('status_update', {'type': 'drawing', **workflow_statuses['drawing']})
                socketio.sleep(0)  # 立即发送消息
                print(f"[DEBUG] <<< 节点 'save_image' 执行完成")
                if result.get('error'):
                    print(f"[DEBUG] save_image 返回错误: {result['error']}")
                else:
                    print(f"[DEBUG] 图片大小: {result.get('image_size', 0)} 字节")
                return result

            # 构建图
            workflow = StateGraph(GraphState)
            workflow.add_node("refine_prompt", monitored_refine_prompt)
            workflow.add_node("generate_code", monitored_generate_code)
            workflow.add_node("execute_code", monitored_execute_code)
            workflow.add_node("save_image", monitored_save_image)
            workflow.set_entry_point("refine_prompt")
            workflow.add_edge("refine_prompt", "generate_code")
            workflow.add_edge("generate_code", "execute_code")
            workflow.add_edge("execute_code", "save_image")
            workflow.add_edge("save_image", END)

            return workflow.compile()

        graph = create_monitored_drawing_graph()
        print(f"[DEBUG] 绘图工作流图已创建并编译")

        # 运行工作流
        print(f"[DEBUG] 开始调用绘图工作流...")
        initial_state = {
            "user_prompt": user_prompt,
            "generated_code": "",
            "image_path": "",
            "image_size": 0,
            "error": ""
        }
        print(f"[DEBUG] 初始状态: {initial_state}")

        result = graph.invoke(initial_state)

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
        socketio.emit('status_update', {'type': 'drawing', **workflow_statuses['drawing']})
        socketio.sleep(0)  # 立即发送消息
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
        socketio.emit('status_update', {'type': 'drawing', **workflow_statuses['drawing']})
        socketio.sleep(0)  # 立即发送消息
        print(f"[DEBUG] 绘图错误状态已发送到客户端")

def run_document_workflow_thread(user_prompt, options):
    """在工作流线程中运行文档生成工作流"""
    print(f"\n[DEBUG] ===== 文档工作流线程启动 =====")
    print(f"[DEBUG] 用户提示词: '{user_prompt}'")
    print(f"[DEBUG] 文档选项: {options}")

    try:
        # 导入文档工作流
        from write_md import create_graph as create_document_graph, GraphState as DocumentGraphState

        # 创建监控的文档工作流
        def create_monitored_document_graph():
            """创建带监控的文档工作流图"""
            from langgraph.graph import StateGraph, END

            # 导入原始节点函数
            from write_md import refine_prompt, generate_outline, generate_content, save_document, verify_document

            # 包装节点以添加进度报告
            def monitored_refine_prompt(state):
                print(f"\n[DEBUG] >>> 文档节点 'refine_prompt' 开始执行")
                workflow_statuses['document']['current_step'] = 'refine_prompt'
                workflow_statuses['document']['steps'].append({
                    'step': 'refine_prompt',
                    'name': DOCUMENT_STEP_NAMES['refine_prompt'],
                    'status': 'running',
                    'timestamp': datetime.now().isoformat()
                })
                socketio.emit('status_update', {'type': 'document', **workflow_statuses['document']})
                socketio.sleep(0)
                result = refine_prompt(state)
                workflow_statuses['document']['steps'][-1]['status'] = 'completed'
                socketio.emit('status_update', {'type': 'document', **workflow_statuses['document']})
                socketio.sleep(0)
                print(f"[DEBUG] <<< 文档节点 'refine_prompt' 执行完成")
                return result

            def monitored_generate_outline(state):
                print(f"\n[DEBUG] >>> 文档节点 'generate_outline' 开始执行")
                workflow_statuses['document']['current_step'] = 'generate_outline'
                workflow_statuses['document']['steps'].append({
                    'step': 'generate_outline',
                    'name': DOCUMENT_STEP_NAMES['generate_outline'],
                    'status': 'running',
                    'timestamp': datetime.now().isoformat()
                })
                socketio.emit('status_update', {'type': 'document', **workflow_statuses['document']})
                socketio.sleep(0)
                result = generate_outline(state)
                if result.get('error'):
                    workflow_statuses['document']['steps'][-1]['status'] = 'error'
                else:
                    workflow_statuses['document']['steps'][-1]['status'] = 'completed'
                socketio.emit('status_update', {'type': 'document', **workflow_statuses['document']})
                socketio.sleep(0)
                print(f"[DEBUG] <<< 文档节点 'generate_outline' 执行完成")
                return result

            def monitored_generate_content(state):
                print(f"\n[DEBUG] >>> 文档节点 'generate_content' 开始执行")
                workflow_statuses['document']['current_step'] = 'generate_content'
                workflow_statuses['document']['steps'].append({
                    'step': 'generate_content',
                    'name': DOCUMENT_STEP_NAMES['generate_content'],
                    'status': 'running',
                    'timestamp': datetime.now().isoformat()
                })
                socketio.emit('status_update', {'type': 'document', **workflow_statuses['document']})
                socketio.sleep(0)
                result = generate_content(state)
                if result.get('error'):
                    workflow_statuses['document']['steps'][-1]['status'] = 'error'
                else:
                    workflow_statuses['document']['steps'][-1]['status'] = 'completed'
                socketio.emit('status_update', {'type': 'document', **workflow_statuses['document']})
                socketio.sleep(0)
                print(f"[DEBUG] <<< 文档节点 'generate_content' 执行完成")
                return result

            def monitored_save_document(state):
                print(f"\n[DEBUG] >>> 文档节点 'save_document' 开始执行")
                workflow_statuses['document']['current_step'] = 'save_document'
                workflow_statuses['document']['steps'].append({
                    'step': 'save_document',
                    'name': DOCUMENT_STEP_NAMES['save_document'],
                    'status': 'running',
                    'timestamp': datetime.now().isoformat()
                })
                socketio.emit('status_update', {'type': 'document', **workflow_statuses['document']})
                socketio.sleep(0)
                result = save_document(state)
                if result.get('error'):
                    workflow_statuses['document']['steps'][-1]['status'] = 'error'
                else:
                    workflow_statuses['document']['steps'][-1]['status'] = 'completed'
                socketio.emit('status_update', {'type': 'document', **workflow_statuses['document']})
                socketio.sleep(0)
                print(f"[DEBUG] <<< 文档节点 'save_document' 执行完成")
                return result

            def monitored_verify_document(state):
                print(f"\n[DEBUG] >>> 文档节点 'verify_document' 开始执行")
                workflow_statuses['document']['current_step'] = 'verify_document'
                workflow_statuses['document']['steps'].append({
                    'step': 'verify_document',
                    'name': DOCUMENT_STEP_NAMES['verify_document'],
                    'status': 'running',
                    'timestamp': datetime.now().isoformat()
                })
                socketio.emit('status_update', {'type': 'document', **workflow_statuses['document']})
                socketio.sleep(0)
                result = verify_document(state)
                if result.get('error'):
                    workflow_statuses['document']['steps'][-1]['status'] = 'error'
                else:
                    workflow_statuses['document']['steps'][-1]['status'] = 'completed'
                socketio.emit('status_update', {'type': 'document', **workflow_statuses['document']})
                socketio.sleep(0)
                print(f"[DEBUG] <<< 文档节点 'verify_document' 执行完成")
                return result

            # 构建图
            workflow = StateGraph(DocumentGraphState)
            workflow.add_node("refine_prompt", monitored_refine_prompt)
            workflow.add_node("generate_outline", monitored_generate_outline)
            workflow.add_node("generate_content", monitored_generate_content)
            workflow.add_node("save_document", monitored_save_document)
            workflow.add_node("verify_document", monitored_verify_document)
            workflow.set_entry_point("refine_prompt")
            workflow.add_edge("refine_prompt", "generate_outline")
            workflow.add_edge("generate_outline", "generate_content")
            workflow.add_edge("generate_content", "save_document")
            workflow.add_edge("save_document", "verify_document")
            workflow.add_edge("verify_document", END)

            return workflow.compile()

        graph = create_monitored_document_graph()
        print(f"[DEBUG] 文档工作流图已创建并编译")

        # 运行工作流
        print(f"[DEBUG] 开始调用文档工作流...")
        initial_state = {
            "user_prompt": user_prompt,
            "refined_prompt": "",
            "document_outline": "",
            "markdown_content": "",
            "output_path": "",
            "file_size": 0,
            "error": ""
        }
        print(f"[DEBUG] 初始状态: {initial_state}")

        result = graph.invoke(initial_state)

        print(f"\n[DEBUG] ===== 文档工作流执行完成 =====")
        print(f"[DEBUG] 最终结果: {result}")

        # 更新最终状态
        if result.get("error"):
            print(f"[DEBUG] 文档工作流执行失败，错误信息: {result['error']}")
            workflow_statuses['document']['status'] = 'error'
            workflow_statuses['document']['error'] = result['error']
        else:
            print(f"[DEBUG] 文档工作流执行成功")
            workflow_statuses['document']['status'] = 'completed'
            filename = os.path.basename(result['output_path'])
            workflow_statuses['document']['result'] = {
                'type': 'document',
                'path': result['output_path'],
                'filename': filename,
                'url': f'/api/documents/{filename}',
                'size': result['file_size'],
                'content': result.get('markdown_content', ''),
                'outline': result.get('document_outline', '')
            }
            print(f"[DEBUG] 结果文档路径: {result['output_path']}")
            print(f"[DEBUG] 结果文档 URL: /api/documents/{filename}")

        workflow_statuses['document']['current_step'] = ''
        socketio.emit('status_update', {'type': 'document', **workflow_statuses['document']})
        socketio.sleep(0)  # 立即发送消息
        print(f"[DEBUG] 文档状态更新已发送到客户端")

    except Exception as e:
        import traceback
        print(f"\n[DEBUG] ===== 文档工作流异常 =====")
        print(f"[DEBUG] 异常类型: {type(e).__name__}")
        print(f"[DEBUG] 异常信息: {str(e)}")
        print(f"[DEBUG] 完整堆栈跟踪:")
        traceback.print_exc()

        workflow_statuses['document']['status'] = 'error'
        workflow_statuses['document']['error'] = str(e)
        socketio.emit('status_update', {'type': 'document', **workflow_statuses['document']})
        socketio.sleep(0)  # 立即发送消息
        print(f"[DEBUG] 文档错误状态已发送到客户端")

# 向后兼容：保留旧的函数名
run_workflow_thread = run_drawing_workflow_thread

@socketio.on('connect')
def handle_connect():
    """处理客户端连接 - 发送所有工作流状态"""
    emit('status_update', {'type': 'drawing', **workflow_statuses['drawing']})
    emit('status_update', {'type': 'document', **workflow_statuses['document']})

@socketio.on('disconnect')
def handle_disconnect():
    """处理客户端断开"""
    pass

if __name__ == '__main__':
    print("🚀 启动 Web 服务器...")
    print("📝 绘图模式: http://localhost:5001")
    print("📄 文档模式: http://localhost:5001")
    socketio.run(app, debug=True, host='0.0.0.0', port=5001)
