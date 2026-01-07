from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
import os
import threading
import time
from main import create_graph, GraphState
from datetime import datetime
import eventlet

# 初始化 Flask 应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*")

# 全局变量存储工作流状态
workflow_status = {
    'status': 'idle',
    'current_step': '',
    'steps': [],
    'result': None,
    'error': None
}

# 状态映射
STEP_NAMES = {
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

@app.route('/api/workflow', methods=['POST'])
def run_workflow():
    """启动工作流"""
    data = request.json
    user_prompt = data.get('prompt', '')

    if not user_prompt:
        return jsonify({'error': '请输入绘图需求'}), 400

    # 立即更新状态为运行中，提供即时反馈
    global workflow_status
    workflow_status = {
        'status': 'running',
        'current_step': '',
        'steps': [],
        'result': None,
        'error': None
    }

    # 立即推送状态到客户端，确保无延迟
    socketio.emit('status_update', workflow_status)
    socketio.sleep(0)  # 强制立即发送

    # 在新线程中运行工作流
    thread = threading.Thread(target=run_workflow_thread, args=(user_prompt,))
    thread.daemon = True
    thread.start()

    return jsonify({'message': '工作流已启动'})

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
    """清除历史记录"""
    workflow_status['steps'] = []
    workflow_status['result'] = None
    workflow_status['error'] = None
    socketio.emit('status_update', workflow_status)
    socketio.sleep(0)  # 立即发送消息
    return jsonify({'message': '历史记录已清除'})

def run_workflow_thread(user_prompt):
    """在工作流线程中运行"""
    global workflow_status

    print(f"\n[DEBUG] ===== 工作流线程启动 =====")
    print(f"[DEBUG] 用户提示词: '{user_prompt}'")

    try:
        # 状态已在 /api/workflow 中重置，这里只需确认
        print(f"[DEBUG] 工作流状态: {workflow_status['status']}")

        # 创建工作流图
        def create_monitored_graph():
            """创建带监控的工作流图"""
            from langgraph.graph import StateGraph, END

            # 原始节点函数
            from main import refine_prompt, generate_code, execute_code, save_image

            # 包装节点以添加进度报告
            def monitored_refine_prompt(state):
                print(f"\n[DEBUG] >>> 节点 'refine_prompt' 开始执行")
                workflow_status['current_step'] = 'refine_prompt'
                workflow_status['steps'].append({
                    'step': 'refine_prompt',
                    'name': STEP_NAMES['refine_prompt'],
                    'status': 'running',
                    'timestamp': datetime.now().isoformat()
                })
                socketio.emit('status_update', workflow_status)
                socketio.sleep(0)  # 立即发送消息
                result = refine_prompt(state)
                workflow_status['steps'][-1]['status'] = 'completed'
                socketio.emit('status_update', workflow_status)
                socketio.sleep(0)  # 立即发送消息
                print(f"[DEBUG] <<< 节点 'refine_prompt' 执行完成")
                print(f"[DEBUG] 润色后的提示词: {result.get('refined_prompt', 'N/A')[:100]}...")
                return result

            def monitored_generate_code(state):
                print(f"\n[DEBUG] >>> 节点 'generate_code' 开始执行")
                workflow_status['current_step'] = 'generate_code'
                workflow_status['steps'].append({
                    'step': 'generate_code',
                    'name': STEP_NAMES['generate_code'],
                    'status': 'running',
                    'timestamp': datetime.now().isoformat()
                })
                socketio.emit('status_update', workflow_status)
                socketio.sleep(0)  # 立即发送消息
                result = generate_code(state)
                workflow_status['steps'][-1]['status'] = 'completed'
                socketio.emit('status_update', workflow_status)
                socketio.sleep(0)  # 立即发送消息
                print(f"[DEBUG] <<< 节点 'generate_code' 执行完成")
                if result.get('error'):
                    print(f"[DEBUG] generate_code 返回错误: {result['error']}")
                else:
                    print(f"[DEBUG] 生成的代码长度: {len(result.get('generated_code', ''))} 字符")
                return result

            def monitored_execute_code(state):
                print(f"\n[DEBUG] >>> 节点 'execute_code' 开始执行")
                workflow_status['current_step'] = 'execute_code'
                workflow_status['steps'].append({
                    'step': 'execute_code',
                    'name': STEP_NAMES['execute_code'],
                    'status': 'running',
                    'timestamp': datetime.now().isoformat()
                })
                socketio.emit('status_update', workflow_status)
                socketio.sleep(0)  # 立即发送消息
                result = execute_code(state)
                workflow_status['steps'][-1]['status'] = 'completed'
                socketio.emit('status_update', workflow_status)
                socketio.sleep(0)  # 立即发送消息
                print(f"[DEBUG] <<< 节点 'execute_code' 执行完成")
                if result.get('error'):
                    print(f"[DEBUG] execute_code 返回错误: {result['error']}")
                else:
                    print(f"[DEBUG] 生成的图片路径: {result.get('image_path', 'N/A')}")
                return result

            def monitored_save_image(state):
                print(f"\n[DEBUG] >>> 节点 'save_image' 开始执行")
                workflow_status['current_step'] = 'save_image'
                workflow_status['steps'].append({
                    'step': 'save_image',
                    'name': STEP_NAMES['save_image'],
                    'status': 'running',
                    'timestamp': datetime.now().isoformat()
                })
                socketio.emit('status_update', workflow_status)
                socketio.sleep(0)  # 立即发送消息
                result = save_image(state)
                workflow_status['steps'][-1]['status'] = 'completed'
                socketio.emit('status_update', workflow_status)
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

        graph = create_monitored_graph()
        print(f"[DEBUG] 工作流图已创建并编译")

        # 运行工作流
        print(f"[DEBUG] 开始调用工作流...")
        initial_state = {
            "user_prompt": user_prompt,
            "generated_code": "",
            "image_path": "",
            "image_size": 0,
            "error": ""
        }
        print(f"[DEBUG] 初始状态: {initial_state}")

        result = graph.invoke(initial_state)

        print(f"\n[DEBUG] ===== 工作流执行完成 =====")
        print(f"[DEBUG] 最终结果: {result}")

        # 更新最终状态
        if result.get("error"):
            print(f"[DEBUG] 工作流执行失败，错误信息: {result['error']}")
            workflow_status['status'] = 'error'
            workflow_status['error'] = result['error']
        else:
            print(f"[DEBUG] 工作流执行成功")
            workflow_status['status'] = 'completed'
            # 从 image_path 中提取文件名（去掉 images/ 前缀）
            filename = os.path.basename(result['image_path'])
            workflow_status['result'] = {
                'image_path': result['image_path'],
                'image_url': f'/api/images/{filename}',
                'image_size': result['image_size'],
                'generated_code': result['generated_code']
            }
            print(f"[DEBUG] 结果图片路径: {result['image_path']}")
            print(f"[DEBUG] 结果图片 URL: /api/images/{filename}")

        workflow_status['current_step'] = ''
        socketio.emit('status_update', workflow_status)
        socketio.sleep(0)  # 立即发送消息
        print(f"[DEBUG] 状态更新已发送到客户端")

    except Exception as e:
        import traceback
        print(f"\n[DEBUG] ===== 工作流异常 =====")
        print(f"[DEBUG] 异常类型: {type(e).__name__}")
        print(f"[DEBUG] 异常信息: {str(e)}")
        print(f"[DEBUG] 完整堆栈跟踪:")
        traceback.print_exc()

        workflow_status['status'] = 'error'
        workflow_status['error'] = str(e)
        socketio.emit('status_update', workflow_status)
        socketio.sleep(0)  # 立即发送消息
        print(f"[DEBUG] 错误状态已发送到客户端")

@socketio.on('connect')
def handle_connect():
    """处理客户端连接"""
    emit('status_update', workflow_status)

@socketio.on('disconnect')
def handle_disconnect():
    """处理客户端断开"""
    pass

if __name__ == '__main__':
    print("🚀 启动 Web 服务器...")
    print("📝 访问地址: http://localhost:5001")
    socketio.run(app, debug=True, host='0.0.0.0', port=5001)
