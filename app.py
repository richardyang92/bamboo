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
    }
}

# 用于线程间通信的锁
status_lock = threading.Lock()

# 为了向后兼容，保留旧的 workflow_status 引用
workflow_status = workflow_statuses['drawing']

# 辅助函数：安全地更新和发送状态
def update_and_emit_status(workflow_type):
    """安全地更新并发射状态更新（避免 greenlet 切换错误）"""
    with status_lock:
        status = workflow_statuses.get(workflow_type, {}).copy()
    
    try:
        socketio.emit('status_update', {'type': workflow_type, **status})
    except Exception as e:
        print(f"[WARNING] 状态更新发送失败: {e}")

# 状态映射
DRAWING_STEP_NAMES = {
    'refine_prompt': '润色提示词',
    'generate_code': '生成绘图代码',
    'execute_code': '执行绘图代码',
    'save_image': '验证图片保存'
}

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/history')
def history():
    """历史页面"""
    return render_template('history.html')

@app.route('/document')
def document():
    """文档生成页面"""
    return render_template('document.html')

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
    update_and_emit_status('drawing')

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
    update_and_emit_status('drawing')
    return jsonify({'message': '绘图历史记录已清除'})

# ==================== 文档工作流端点 ====================

@app.route('/api/document/workflow-with-images', methods=['POST'])
def run_document_with_images_workflow():
    """启动带图片的文档生成工作流"""
    data = request.json
    user_prompt = data.get('prompt', '')

    if not user_prompt:
        return jsonify({'error': '请输入文档主题'}), 400

    # 初始化新的工作流状态（用于带图片的文档生成）
    if 'document_with_images' not in workflow_statuses:
        workflow_statuses['document_with_images'] = {
            'status': 'idle',
            'current_step': '',
            'steps': [],
            'result': None,
            'error': None
        }

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

    # 在新线程中运行工作流
    thread = threading.Thread(target=run_document_with_images_thread, args=(user_prompt,))
    thread.daemon = True
    thread.start()

    return jsonify({'message': '带图片的文档生成工作流已启动'})

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
                update_and_emit_status('drawing')
                result = refine_prompt(state)
                workflow_statuses['drawing']['steps'][-1]['status'] = 'completed'
                update_and_emit_status('drawing')
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
                update_and_emit_status('drawing')
                result = generate_code(state)
                workflow_statuses['drawing']['steps'][-1]['status'] = 'completed'
                update_and_emit_status('drawing')
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
                update_and_emit_status('drawing')
                result = execute_code(state)
                workflow_statuses['drawing']['steps'][-1]['status'] = 'completed'
                update_and_emit_status('drawing')
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
                update_and_emit_status('drawing')
                result = save_image(state)
                workflow_statuses['drawing']['steps'][-1]['status'] = 'completed'
                update_and_emit_status('drawing')
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

    try:
        # 导入带图片的文档工作流
        from write_md_with_images import create_graph as create_doc_with_images_graph, GraphState as DocWithImagesGraphState

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
            from write_md_with_images import (
                refine_prompt, generate_outline, generate_content,
                identify_image_requests, generate_images, embed_images,
                save_document, verify_document
            )

            # 包装节点以添加进度报告
            def monitored_refine_prompt(state):
                print(f"\n[DEBUG] >>> 带图片文档节点 'refine_prompt' 开始执行")
                workflow_statuses['document_with_images']['current_step'] = 'refine_prompt'
                workflow_statuses['document_with_images']['steps'].append({
                    'step': 'refine_prompt',
                    'name': DOC_WITH_IMAGES_STEP_NAMES['refine_prompt'],
                    'status': 'running',
                    'timestamp': datetime.now().isoformat()
                })
                update_and_emit_status('document_with_images')
                result = refine_prompt(state)
                workflow_statuses['document_with_images']['steps'][-1]['status'] = 'completed'
                update_and_emit_status('document_with_images')
                print(f"[DEBUG] <<< 带图片文档节点 'refine_prompt' 执行完成")
                return result

            def monitored_generate_outline(state):
                print(f"\n[DEBUG] >>> 带图片文档节点 'generate_outline' 开始执行")
                workflow_statuses['document_with_images']['current_step'] = 'generate_outline'
                workflow_statuses['document_with_images']['steps'].append({
                    'step': 'generate_outline',
                    'name': DOC_WITH_IMAGES_STEP_NAMES['generate_outline'],
                    'status': 'running',
                    'timestamp': datetime.now().isoformat()
                })
                update_and_emit_status('document_with_images')
                result = generate_outline(state)
                if result.get('error'):
                    workflow_statuses['document_with_images']['steps'][-1]['status'] = 'error'
                else:
                    workflow_statuses['document_with_images']['steps'][-1]['status'] = 'completed'
                update_and_emit_status('document_with_images')
                print(f"[DEBUG] <<< 带图片文档节点 'generate_outline' 执行完成")
                return result

            def monitored_generate_content(state):
                print(f"\n[DEBUG] >>> 带图片文档节点 'generate_content' 开始执行")
                workflow_statuses['document_with_images']['current_step'] = 'generate_content'
                workflow_statuses['document_with_images']['steps'].append({
                    'step': 'generate_content',
                    'name': DOC_WITH_IMAGES_STEP_NAMES['generate_content'],
                    'status': 'running',
                    'timestamp': datetime.now().isoformat()
                })
                update_and_emit_status('document_with_images')
                result = generate_content(state)
                if result.get('error'):
                    workflow_statuses['document_with_images']['steps'][-1]['status'] = 'error'
                else:
                    workflow_statuses['document_with_images']['steps'][-1]['status'] = 'completed'
                update_and_emit_status('document_with_images')
                print(f"[DEBUG] <<< 带图片文档节点 'generate_content' 执行完成")
                return result

            def monitored_identify_image_requests(state):
                print(f"\n[DEBUG] >>> 带图片文档节点 'identify_image_requests' 开始执行")
                workflow_statuses['document_with_images']['current_step'] = 'identify_image_requests'
                workflow_statuses['document_with_images']['steps'].append({
                    'step': 'identify_image_requests',
                    'name': DOC_WITH_IMAGES_STEP_NAMES['identify_image_requests'],
                    'status': 'running',
                    'timestamp': datetime.now().isoformat()
                })
                update_and_emit_status('document_with_images')
                result = identify_image_requests(state)
                if result.get('error'):
                    workflow_statuses['document_with_images']['steps'][-1]['status'] = 'error'
                else:
                    workflow_statuses['document_with_images']['steps'][-1]['status'] = 'completed'
                update_and_emit_status('document_with_images')
                print(f"[DEBUG] <<< 带图片文档节点 'identify_image_requests' 执行完成")
                return result

            def monitored_generate_images(state):
                print(f"\n[DEBUG] >>> 带图片文档节点 'generate_images' 开始执行")
                workflow_statuses['document_with_images']['current_step'] = 'generate_images'
                workflow_statuses['document_with_images']['steps'].append({
                    'step': 'generate_images',
                    'name': DOC_WITH_IMAGES_STEP_NAMES['generate_images'],
                    'status': 'running',
                    'timestamp': datetime.now().isoformat()
                })
                update_and_emit_status('document_with_images')
                result = generate_images(state)
                if result.get('error'):
                    workflow_statuses['document_with_images']['steps'][-1]['status'] = 'error'
                else:
                    workflow_statuses['document_with_images']['steps'][-1]['status'] = 'completed'
                update_and_emit_status('document_with_images')
                print(f"[DEBUG] <<< 带图片文档节点 'generate_images' 执行完成")
                return result

            def monitored_embed_images(state):
                print(f"\n[DEBUG] >>> 带图片文档节点 'embed_images' 开始执行")
                workflow_statuses['document_with_images']['current_step'] = 'embed_images'
                workflow_statuses['document_with_images']['steps'].append({
                    'step': 'embed_images',
                    'name': DOC_WITH_IMAGES_STEP_NAMES['embed_images'],
                    'status': 'running',
                    'timestamp': datetime.now().isoformat()
                })
                update_and_emit_status('document_with_images')
                result = embed_images(state)
                if result.get('error'):
                    workflow_statuses['document_with_images']['steps'][-1]['status'] = 'error'
                else:
                    workflow_statuses['document_with_images']['steps'][-1]['status'] = 'completed'
                update_and_emit_status('document_with_images')
                print(f"[DEBUG] <<< 带图片文档节点 'embed_images' 执行完成")
                return result

            def monitored_save_document(state):
                print(f"\n[DEBUG] >>> 带图片文档节点 'save_document' 开始执行")
                workflow_statuses['document_with_images']['current_step'] = 'save_document'
                workflow_statuses['document_with_images']['steps'].append({
                    'step': 'save_document',
                    'name': DOC_WITH_IMAGES_STEP_NAMES['save_document'],
                    'status': 'running',
                    'timestamp': datetime.now().isoformat()
                })
                update_and_emit_status('document_with_images')
                result = save_document(state)
                if result.get('error'):
                    workflow_statuses['document_with_images']['steps'][-1]['status'] = 'error'
                else:
                    workflow_statuses['document_with_images']['steps'][-1]['status'] = 'completed'
                update_and_emit_status('document_with_images')
                print(f"[DEBUG] <<< 带图片文档节点 'save_document' 执行完成")
                return result

            def monitored_verify_document(state):
                print(f"\n[DEBUG] >>> 带图片文档节点 'verify_document' 开始执行")
                workflow_statuses['document_with_images']['current_step'] = 'verify_document'
                workflow_statuses['document_with_images']['steps'].append({
                    'step': 'verify_document',
                    'name': DOC_WITH_IMAGES_STEP_NAMES['verify_document'],
                    'status': 'running',
                    'timestamp': datetime.now().isoformat()
                })
                update_and_emit_status('document_with_images')
                result = verify_document(state)
                if result.get('error'):
                    workflow_statuses['document_with_images']['steps'][-1]['status'] = 'error'
                else:
                    workflow_statuses['document_with_images']['steps'][-1]['status'] = 'completed'
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
            workflow.add_edge("identify_image_requests", "generate_images")
            workflow.add_edge("generate_images", "embed_images")
            workflow.add_edge("embed_images", "save_document")
            workflow.add_edge("save_document", "verify_document")
            workflow.add_edge("verify_document", END)

            return workflow.compile()

        graph = create_monitored_doc_with_images_graph()
        print(f"[DEBUG] 带图片的文档工作流图已创建并编译")

        print(f"[DEBUG] 开始调用带图片的文档工作流...")
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

        result = graph.invoke(initial_state)

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

@socketio.on('connect')
def handle_connect():
    """处理客户端连接 - 发送所有工作流状态"""
    emit('status_update', {'type': 'drawing', **workflow_statuses['drawing']})
    if 'document_with_images' in workflow_statuses:
        emit('status_update', {'type': 'document_with_images', **workflow_statuses['document_with_images']})

@socketio.on('disconnect')
def handle_disconnect():
    """处理客户端断开"""
    pass

if __name__ == '__main__':
    print("🚀 启动 Web 服务器...")
    print("📝 绘图模式: http://localhost:5001")
    print("📄 文档模式: http://localhost:5001")
    socketio.run(app, debug=True, host='0.0.0.0', port=5001)
