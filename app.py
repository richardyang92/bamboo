from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_sock import Sock
import os
import threading
import json
from draw_pic import create_graph, GraphState
from datetime import datetime

# 初始化 Flask 应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
sock = Sock(app)

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
def emit_stream_content(workflow_type, node_name, content):
    """发送AI流式响应内容到前端"""
    message = {
        'type': 'stream_content',
        'workflow_type': workflow_type,
        'node': node_name,
        'content': content
    }
    broadcast_to_workflow(workflow_type, message)
    print(f"[DEBUG] 流式内容已发送: {workflow_type}/{node_name}, 长度: {len(content)} 字符")

# 状态映射
DRAWING_STEP_NAMES = {
    'refine_prompt': '润色提示词',
    'generate_code': '生成绘图代码',
    'execute_code': '执行绘图代码',
    'save_image': '验证图片保存'
}

MANIM_STEP_NAMES = {
     'refine_prompt': '润色动画需求',
     'generate_code': '生成动画代码',
     'execute_code': '渲染动画视频',
     'save_video': '验证视频保存'
 }

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/test')
def test():
    """测试页面"""
    return render_template('test.html')

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
    print("[DEBUG] 绘图历史已清除，状态已发送")
    return jsonify({'message': '绘图历史记录已清除'})

# ==================== 文档工作流端点 ====================

@app.route('/api/document/workflow-with-images', methods=['POST'])
def run_document_with_images_workflow():
    """启动带图片的文档生成工作流"""
    data = request.json
    user_prompt = data.get('prompt', '')

    if not user_prompt:
        return jsonify({'error': '请输入文档主题'}), 400

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
        from draw_pic import create_graph, GraphState

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

# ==================== Manim 动画工作流端点 ====================

@app.route('/api/manim/workflow', methods=['POST'])
def run_manim_workflow():
    """启动 Manim 动画工作流"""
    data = request.json
    user_prompt = data.get('prompt', '')
    quality = data.get('quality', 'medium')

    if not user_prompt:
        return jsonify({'error': '请输入动画需求'}), 400

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
    if os.path.exists('videos'):
        for file in os.listdir('videos'):
            if file.startswith('manim_') and file.endswith('.mp4'):
                filepath = os.path.join('videos', file)
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
    return send_from_directory('videos', filename)

@app.route('/api/manim/videos/<filename>', methods=['DELETE'])
def delete_manim_video(filename):
    """删除视频文件"""
    try:
        filepath = os.path.join('videos', filename)
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

 # ==================== 统一历史记录端点 ====================

@app.route('/api/history')
def list_history():
    """列出所有项目（图片 + 文档 + 视频）"""
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

    # 添加视频
    if os.path.exists('videos'):
        for file in os.listdir('videos'):
            if file.startswith('manim_') and file.endswith('.mp4'):
                filepath = os.path.join('videos', file)
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
    
    # 默认连接到 drawing
    ws.workflow_type = 'drawing'
    
    try:
        # 将客户端添加到连接池
        if ws.workflow_type not in websocket_clients:
            websocket_clients[ws.workflow_type] = []
        websocket_clients[ws.workflow_type].append(ws)
        print(f"[DEBUG] 客户端已添加到 {ws.workflow_type} 连接池，当前连接数: {len(websocket_clients[ws.workflow_type])}")
        
        # 发送初始状态（先获取数据，释放锁后再发送）
        with status_lock:
            drawing_status = workflow_statuses['drawing'].copy()
            doc_status = workflow_statuses.get('document_with_images', {}).copy() if 'document_with_images' in workflow_statuses else None
            manim_status = workflow_statuses.get('manim', {}).copy() if 'manim' in workflow_statuses else None

        print(f"[DEBUG] 准备发送初始状态...")
        ws.send(json.dumps({
            'type': 'status_update',
            'workflow_type': 'drawing',
            **drawing_status
        }))
        print(f"[DEBUG] 绘图状态已发送")

        if doc_status:
            ws.send(json.dumps({
                'type': 'status_update',
                'workflow_type': 'document_with_images',
                **doc_status
            }))
            print(f"[DEBUG] 文档状态已发送")

        if manim_status:
            ws.send(json.dumps({
                'type': 'status_update',
                'workflow_type': 'manim',
                **manim_status
            }))
            print(f"[DEBUG] Manim 状态已发送")
        
        # 接收消息（使用 while 循环而不是 for 迭代）
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
                
                # 定义流式回调函数
                def stream_callback(content):
                    emit_stream_content('drawing', 'generate_code', content)
                
                # 执行节点逻辑，传入流式回调
                result = generate_code(state, stream_callback=stream_callback)
                
                # 节点完成时立即更新状态
                if result.get('error'):
                    workflow_statuses['drawing']['steps'][-1]['status'] = 'error'
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

        # 运行工作流（使用流式执行）
        print(f"[DEBUG] 开始调用绘图工作流（流式模式）...")
        initial_state = {
            "user_prompt": user_prompt,
            "generated_code": "",
            "image_path": "",
            "image_size": 0,
            "error": ""
        }
        print(f"[DEBUG] 初始状态: {initial_state}")

        # 使用流式执行
        result = {}
        try:
            for event in graph.stream(initial_state):
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
                else:
                    workflow_statuses['document_with_images']['steps'][-1]['status'] = 'completed'
                workflow_statuses['document_with_images']['steps'][-1]['completed_at'] = datetime.now().isoformat()
                update_and_emit_status('document_with_images')
                
                print(f"[DEBUG] <<< 带图片文档节点 'refine_prompt' 执行完成")
                return result

            def monitored_generate_outline(state):
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
                else:
                    workflow_statuses['document_with_images']['steps'][-1]['status'] = 'completed'
                workflow_statuses['document_with_images']['steps'][-1]['completed_at'] = datetime.now().isoformat()
                update_and_emit_status('document_with_images')
                
                print(f"[DEBUG] <<< 带图片文档节点 'generate_outline' 执行完成")
                return result

            def monitored_generate_content(state):
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
                else:
                    workflow_statuses['document_with_images']['steps'][-1]['status'] = 'completed'
                workflow_statuses['document_with_images']['steps'][-1]['completed_at'] = datetime.now().isoformat()
                update_and_emit_status('document_with_images')
                
                print(f"[DEBUG] <<< 带图片文档节点 'generate_content' 执行完成")
                return result

            def monitored_identify_image_requests(state):
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
                else:
                    workflow_statuses['document_with_images']['steps'][-1]['status'] = 'completed'
                workflow_statuses['document_with_images']['steps'][-1]['completed_at'] = datetime.now().isoformat()
                update_and_emit_status('document_with_images')
                
                print(f"[DEBUG] <<< 带图片文档节点 'identify_image_requests' 执行完成")
                return result

            def monitored_generate_images(state):
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
                else:
                    workflow_statuses['document_with_images']['steps'][-1]['status'] = 'completed'
                workflow_statuses['document_with_images']['steps'][-1]['completed_at'] = datetime.now().isoformat()
                update_and_emit_status('document_with_images')
                
                print(f"[DEBUG] <<< 带图片文档节点 'generate_images' 执行完成")
                return result

            def monitored_embed_images(state):
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
                else:
                    workflow_statuses['document_with_images']['steps'][-1]['status'] = 'completed'
                workflow_statuses['document_with_images']['steps'][-1]['completed_at'] = datetime.now().isoformat()
                update_and_emit_status('document_with_images')
                
                print(f"[DEBUG] <<< 带图片文档节点 'embed_images' 执行完成")
                return result

            def monitored_save_document(state):
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
                else:
                    workflow_statuses['document_with_images']['steps'][-1]['status'] = 'completed'
                workflow_statuses['document_with_images']['steps'][-1]['completed_at'] = datetime.now().isoformat()
                update_and_emit_status('document_with_images')
                
                print(f"[DEBUG] <<< 带图片文档节点 'save_document' 执行完成")
                return result

            def monitored_verify_document(state):
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
            workflow.add_edge("identify_image_requests", "generate_images")
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

    try:
        # 导入 Manim 动画工作流
        from manim_gen import create_graph as create_manim_graph, ManimState

        # 创建监控的工作流
        def create_monitored_manim_graph():
            """创建带监控的 Manim 动画工作流图"""
            from langgraph.graph import StateGraph, END

            # 导入原始节点函数
            from manim_gen import (
                refine_prompt, generate_code, execute_code, save_video
            )

            # 包装节点以添加进度报告
            def monitored_refine_prompt(state):
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
                else:
                    workflow_statuses['manim']['steps'][-1]['status'] = 'completed'
                    workflow_statuses['manim']['steps'][-1]['completed_at'] = datetime.now().isoformat()
                update_and_emit_status('manim')

                print(f"[DEBUG] <<< Manim 节点 'refine_prompt' 执行完成")
                return result

            def monitored_generate_code(state):
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
    print("🚀 启动 Web 服务器...")
    print("📝 绘图模式: http://localhost:5001")
    print("📄 文档模式: http://localhost:5001")
    # 开发环境使用自动重载，生产环境可设置为 False
    run_simple('0.0.0.0', 5001, app, use_reloader=False, use_debugger=False, use_evalex=False, threaded=True)
