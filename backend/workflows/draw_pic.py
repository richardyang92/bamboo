import os
import matplotlib.pyplot as plt
import sys
from typing import TypedDict
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv
from config import Config
from llm_providers.factory import LLMClientFactory

# 加载.env文件中的环境变量
load_dotenv()

# 定义状态结构
class GraphState(TypedDict):
    user_prompt: str
    refined_prompt: str  # AI润色后的绘图提示词
    generated_code: str
    image_path: str
    image_size: int
    error: str
    custom_filename: str  # 自定义文件名(可选),用于外部指定图片文件名
    # CodeAct 模式新增字段
    execution_output: str  # 执行输出（stdout/stderr）
    execution_success: bool  # 执行是否成功
    retry_count: int  # 当前重试次数
    max_retries: int  # 最大重试次数（默认3）
    fix_feedback: str  # AI对修复的分析反馈
    need_retry: bool  # 是否需要重试（内部条件标志）

# 润色绘图需求的节点
def refine_prompt(state: GraphState) -> GraphState:
    """使用AI润色用户的绘图需求，使其更适合生成高质量的绘图代码

    通过调用DeepSeek API智能理解和增强用户的绘图需求
    """
    print("1. 正在AI润色绘图需求...")
    user_prompt = state["user_prompt"]
    print(f"   [DEBUG] 原始需求: '{user_prompt}'")

    try:
        # 初始化LLM客户端
        client = LLMClientFactory.create_client()

        # 检查是否配置了API密钥
        if not client.config.api_key or client.config.api_key == 'ollama':
            if client.config.provider == 'deepseek':
                print(f"   [WARNING] ⚠️ 未设置 DEEPSEEK_API_KEY，直接使用原始需求")
                return {"refined_prompt": user_prompt}

        print(f"   [DEBUG] 正在调用 {client.config.provider} API 润色需求...")

        # 构建润色系统提示词（专注于需求细化）
        refine_system_prompt = """你是一个专业的数据可视化和绘图需求分析专家。

你的任务是理解用户的绘图需求，并将其转换为清晰、完整、专业的绘图指令。

## 工作原则

1. **理解意图**：准确理解用户想要表达的内容和目标
2. **识别类型**：判断是数据可视化图、物理示意图、几何图等哪种类型
3. **补全细节**：补充用户未明确说明但必要的绘图细节
4. **专业表达**：使用专业的绘图术语和规范的描述语言
5. **结构清晰**：将需求组织成条理清晰的指令

## 需求细化要点

### 数据可视化类
- 明确数据来源（公式、数据点等）
- 指定图表类型（折线图、散点图、柱状图等）
- 说明坐标轴含义和范围
- 标注关键特征（极值、趋势、拐点等）

### 物理示意图类
- 描述物体及其位置关系
- 明确标注内容（力、角度、尺寸等）
- 说明视图角度（侧视、俯视等）
- 指出关键约束条件

### 几何图形类
- 描述几何元素及其关系
- 明确角度、长度等参数
- 说明标注要求

## 输出格式

请直接输出润色后的绘图需求描述，使用清晰、专业的语言，包含所有必要的绘图细节。
不要包含技术实现细节（如代码语法、库使用等），这些由后续流程处理。"""

        # 调用 LLM API 进行润色
        response = client.chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": refine_system_prompt
                },
                {
                    "role": "user",
                    "content": f"""请将以下绘图需求润色为专业、完整的绘图指令：

{user_prompt}

要求：
1. 保持用户的原始意图和核心需求
2. 补充必要的绘图细节（如图表类型、坐标轴、标注等）
3. 使用专业术语和规范的描述语言
4. 将需求组织成结构清晰、易于理解的指令

直接输出润色后的绘图需求描述，不要包含任何解释。"""
                }
            ],
            model=client.config.model_name,
            temperature=0.3,
            max_tokens=2000,
            stream=False,
            think=client.config.enable_thinking  # 新增：启用 thinking 模式
        )

        # 获取润色后的提示词（支持思考模式）
        message = response.choices[0].message
        refined = message.content.strip()

        # 打印思考过程（如果有）- 适配不同提供商的字段名
        reasoning_field = client.get_reasoning_field_name()
        if hasattr(message, reasoning_field) and getattr(message, reasoning_field):
            reasoning_content = getattr(message, reasoning_field)
            print(f"   [DEBUG] 🧠 润色思考过程: {reasoning_content[:150]}...")

        print(f"   [DEBUG] AI需求润色完成")
        print(f"   [DEBUG] 润色后需求: '{refined[:200]}...'")
        print(f"   [DEBUG] ✅ 润色后需求长度: {len(refined)} 字符")

        return {"refined_prompt": refined}

    except Exception as e:
        import traceback
        error_msg = f"AI润色失败: {str(e)}"
        print(f"   [WARNING] ⚠️ {error_msg}")
        print(f"   [DEBUG] 直接使用原始需求")
        traceback.print_exc()

        # 如果AI润色失败，直接使用原始提示词
        return {"refined_prompt": user_prompt}

# 生成绘图代码的节点
def generate_code(state: GraphState, stream_callback=None) -> GraphState:
    """根据润色后的提示词使用DeepSeek模型生成绘图代码
    
    Args:
        state: 工作流状态
        stream_callback: 可选的回调函数，用于发送流式响应内容
    """
    print("2. 正在生成绘图代码...")
    user_prompt = state["refined_prompt"]
    print(f"   [DEBUG] 润色后的提示词: '{user_prompt[:100]}...'")

    try:
        # 初始化LLM客户端
        client = LLMClientFactory.create_client()

        # 检查API密钥
        if not client.config.api_key or client.config.api_key == 'ollama':
            if client.config.provider == 'deepseek':
                return {"error": "未设置 DEEPSEEK_API_KEY，请在 .env 文件中配置"}

        print(f"   [DEBUG] 正在调用 {client.config.provider} 模型 ({client.config.model_name})...")

        # 使用流式API调用
        stream = client.chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": get_drawing_system_prompt()
                },
                {
                    "role": "user",
                    "content": f"""请根据以下需求生成Python绘图代码：

{user_prompt}

【⚠️ 重要提醒】生成代码时请务必：
1. 确保所有括号 () 都正确配对
2. 确保所有引号 都正确配对
3. 特别检查每个函数调用（尤其是 ax.annotate, plt.plot）最后都有 )
4. 生成后立即检查一遍代码语法是否正确

请直接输出可执行的Python代码，不要包含任何解释。"""
                }
            ],
            model=client.config.model_name,
            temperature=0.3,
            max_tokens=8192,
            stream=True,
            think=client.config.enable_thinking  # 新增：启用 thinking 模式
        )

        # 收集流式响应（支持思考模式）
        generated_code = ""
        reasoning_content = ""  # 存储思考过程
        total_tokens = 0
        completion_tokens = 0

        print(f"   [DEBUG] 开始接收流式响应...")

        # 获取当前提供商使用的思考字段名
        reasoning_field = client.get_reasoning_field_name()

        if stream is None:
            return {"error": "LLM API 返回空响应，请检查模型配置和网络连接"}

        for chunk in stream:
            delta = chunk.choices[0].delta

            # 处理推理内容（思考过程）- 适配不同提供商的字段名
            if hasattr(delta, reasoning_field) and getattr(delta, reasoning_field) is not None:
                reasoning_delta = getattr(delta, reasoning_field)
                reasoning_content += reasoning_delta
                # 通过回调发送思考内容（如果有）
                if stream_callback:
                    stream_callback(reasoning_delta, content_type='reasoning')
                # 打印调试信息
                print(f"   [THINKING] {reasoning_delta[:100]}..." if len(reasoning_delta) > 100 else f"   [THINKING] {reasoning_delta}")

            # 处理最终内容（生成的代码）
            if delta.content is not None:
                content = delta.content
                generated_code += content
                # 如果有流式回调，实时发送内容
                if stream_callback:
                    stream_callback(content, content_type='content')
                
        generated_code = generated_code.strip()

        # 打印思考摘要（如果有）
        if reasoning_content:
            print(f"   [DEBUG] 🧠 思考过程长度: {len(reasoning_content)} 字符")
            print(f"   [DEBUG] 🧠 思考摘要: {reasoning_content[:200].strip()}..." if len(reasoning_content) > 200 else f"   [DEBUG] 🧠 思考内容: {reasoning_content}")

        print(f"   [DEBUG] ✅ AI 返回的代码长度: {len(generated_code)} 字符")
        print(f"   [DEBUG] 流式响应接收完成")

        # 检查token使用情况（思考模式包含推理token）
        if hasattr(stream, 'usage') and stream.usage:
            total_tokens = stream.usage.total_tokens
            completion_tokens = stream.usage.completion_tokens
            # 思考模式可能有 reasoning_tokens 和 completion_tokens
            reasoning_tokens = getattr(stream.usage, 'reasoning_tokens', 0)
            print(f"   [DEBUG] Token使用情况 - 总计: {total_tokens}, 代码: {completion_tokens}, 推理: {reasoning_tokens}")

            # 检查是否接近限制
            if completion_tokens >= 5800:  # 6000的97%
                print(f"   [WARNING] ⚠️ 代码接近token限制，可能被截断！")

        # 去除可能的markdown格式
        if generated_code.startswith('```python'):
            generated_code = generated_code[10:-3].strip()
            print(f"   [DEBUG] 移除了 ```python 标记")
        elif generated_code.startswith('```'):
            generated_code = generated_code[3:-3].strip()
            print(f"   [DEBUG] 移除了 ``` 标记")

        print(f"   [DEBUG] 最终代码长度: {len(generated_code)} 字符")
        print(f"   [DEBUG] 代码片段 (前200字符):\n{generated_code[:200]}")

        return {"generated_code": generated_code}
    except Exception as e:
        import traceback
        error_msg = f"生成代码失败: {str(e)}"

        # 检查是否是 API 错误
        error_str = str(e)
        if "401" in error_str or "403" in error_str or "Unauthorized" in error_str:
            error_msg = "DeepSeek API Key 无效或无权限。请检查 .env 文件中的 DEEPSEEK_API_KEY"
        elif "429" in error_str or "rate" in error_str.lower():
            error_msg = "DeepSeek API 调用频率限制，请稍后重试"
        elif "balance" in error_str.lower() or "insufficient" in error_str.lower():
            error_msg = "DeepSeek API 余额不足，请充值后重试"

        print(f"❌ {error_msg}")
        print(f"   [DEBUG] 完整堆栈跟踪:")
        traceback.print_exc()
        return {"error": error_msg}

# 执行绘图代码的节点
def execute_code(state: GraphState) -> GraphState:
    """执行生成的绘图代码（CodeAct模式：捕获输出供AI分析）"""
    retry_info = f" [重试 {state.get('retry_count', 0)}/{state.get('max_retries', 3)}]" if state.get('retry_count', 0) > 0 else ""
    print(f"3.{retry_info} 正在执行绘图代码...")

    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        matplotlib.rcParams['text.usetex'] = False

        from matplotlib import font_manager

        preferred_fonts = [
            'STHeiti', 'Heiti TC', 'Heiti SC', 'Hiragino Sans GB',
            'PingFang SC', 'PingFang HK', 'Arial Unicode MS',
            'STSong', 'Songti SC', 'Kaiti SC', 'STFangsong',
            'SimHei', 'SimSun', 'WenQuanYi Micro Hei'
        ]

        available_fonts = set(f.name for f in font_manager.fontManager.ttflist)
        selected_fonts = [f for f in preferred_fonts if f in available_fonts]

        if selected_fonts:
            matplotlib.rcParams['font.sans-serif'] = selected_fonts
            print(f"   [DEBUG] ✓ 已配置中文字体: {selected_fonts[:3]}")
        else:
            fallback_keywords = ['Hei', 'Song', 'Kai', 'Fang', 'Unicode']
            for keyword in fallback_keywords:
                matching = [f.name for f in font_manager.fontManager.ttflist if keyword in f.name]
                if matching:
                    matplotlib.rcParams['font.sans-serif'] = matching[:5]
                    print(f"   [DEBUG] ✓ 使用备选中文字体 (关键词: {keyword}): {matching[:3]}")
                    break

        matplotlib.rcParams['axes.unicode_minus'] = False

        local_vars = {
            'plt': plt,
            'os': os,
            'matplotlib': __import__('matplotlib'),
            'np': __import__('numpy'),
            'datetime': __import__('datetime'),
            'time': __import__('time')
        }

        # 用于捕获执行输出
        import io
        from contextlib import redirect_stdout, redirect_stderr

        captured_stdout = io.StringIO()
        captured_stderr = io.StringIO()

        import re
        import glob
        import time
        from datetime import datetime

        images_dir = Config.IMAGES_DIR

        if not os.path.exists(images_dir):
            os.makedirs(images_dir)
            print(f"   [DEBUG] 创建 images 目录: {images_dir}")

        print(f"   [DEBUG] Images 目录: {images_dir}")

        user_prompt = state["user_prompt"]
        print(f"   [DEBUG] 用户提示词: '{user_prompt}'")

        keywords = re.sub(r'[^\w\u4e00-\u9fa5]+', '_', user_prompt)
        keywords = keywords[:10].strip('_')
        print(f"   [DEBUG] 提取的关键词: '{keywords}'")

        if state.get("custom_filename"):
            target_filename = os.path.join(images_dir, state["custom_filename"])
            print(f"   [DEBUG] 使用自定义文件名: {state['custom_filename']}")
        else:
            if not keywords:
                keywords = "graph"
                print(f"   [DEBUG] 关键词为空，使用默认值: 'graph'")

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            target_filename = os.path.join(images_dir, f"plot_{keywords}_{timestamp}.png")
            print(f"   [DEBUG] 生成默认文件名: {os.path.basename(target_filename)}")

        print(f"   [DEBUG] 生成的代码 (前100字符): {state['generated_code'][:100]}...")

        local_vars["target_filename"] = target_filename

        import numpy as np_module
        from mpl_toolkits.mplot3d import Axes3D
        from mpl_toolkits.mplot3d import art3d
        from matplotlib.patches import (
            Ellipse, Rectangle, Circle, Arrow, FancyArrowPatch,
            Polygon, Arc, Wedge, FancyBboxPatch, PathPatch
        )

        global_vars = {
            'np': np_module,
            'numpy': np_module,
            'plt': plt,
            'matplotlib': __import__('matplotlib'),
            'os': os,
            'Axes3D': Axes3D,
            'art3d': art3d,
            'patches': __import__('matplotlib.patches'),
            'Ellipse': Ellipse,
            'Rectangle': Rectangle,
            'Circle': Circle,
            'Arrow': Arrow,
            'FancyArrowPatch': FancyArrowPatch,
            'Polygon': Polygon,
            'Arc': Arc,
            'Wedge': Wedge,
            'FancyBboxPatch': FancyBboxPatch,
            'PathPatch': PathPatch
        }

        files_before = set(glob.glob(os.path.join(images_dir, "plot_*.png")))
        print(f"   [DEBUG] 执行前存在的 plot 文件: {files_before}")

        print(f"   [DEBUG] 开始语法检查...")
        try:
            compile(state["generated_code"], '<string>', 'exec')
            print(f"   [DEBUG] ✓ 语法检查通过")
        except SyntaxError as se:
            error_msg = f"生成的代码存在语法错误（第{se.lineno}行）: {se.msg}"
            print(f"   [DEBUG] ✗ {error_msg}")
            print(f"   [DEBUG] 问题代码片段:\n{se.text}")
            return {
                "error": error_msg,
                "execution_output": f"SYNTAX ERROR:\n{error_msg}\nCode:\n{se.text}",
                "execution_success": False
            }

        code_to_execute = state["generated_code"]
        savefig_pattern = r"plt\.savefig\(['\"]([^'\"]+\.png)['\"]\)"
        savefig_matches = re.findall(savefig_pattern, code_to_execute)

        if savefig_matches:
            print(f"   [DEBUG] 检测到 {len(savefig_matches)} 处硬编码的文件名: {savefig_matches}")
            code_to_execute = re.sub(savefig_pattern, "plt.savefig(target_filename)", code_to_execute)
            print(f"   [DEBUG] ✓ 已将文件名替换为 target_filename 变量")

        exec_vars = {**global_vars, **local_vars}

        original_savefig = plt.savefig

        def forced_savefig(fname=None, *args, **kwargs):
            import os
            actual_filename = os.path.abspath(target_filename)
            print(f"   [DEBUG] 🎯 强制保存到: {actual_filename}")
            return original_savefig(actual_filename, *args, **kwargs)

        plt.savefig = forced_savefig

        execution_success = False
        execution_error = None

        try:
            print(f"   [DEBUG] 开始执行生成的代码...")
            with redirect_stdout(captured_stdout), redirect_stderr(captured_stderr):
                exec(code_to_execute, exec_vars)
            print(f"   [DEBUG] 代码执行完成")
            execution_success = True
        except Exception as exec_error:
            execution_error = str(exec_error)
            print(f"   [DEBUG] ✗ 代码执行异常: {execution_error}")
            execution_success = False
        finally:
            plt.savefig = original_savefig
            print(f"   [DEBUG] ✓ 已恢复原始的 plt.savefig 函数")

        # 获取捕获的输出
        stdout_content = captured_stdout.getvalue()
        stderr_content = captured_stderr.getvalue()
        execution_output = f"STDOUT:\n{stdout_content}\nSTDERR:\n{stderr_content}"
        if execution_error:
            execution_output += f"\nEXCEPTION:\n{execution_error}"

        time.sleep(0.5)

        files_after = set(glob.glob(os.path.join(images_dir, "plot_*.png")))
        print(f"   [DEBUG] 执行后存在的 plot 文件: {files_after}")

        new_files = files_after - files_before
        print(f"   [DEBUG] 新创建的文件: {new_files}")

        if new_files:
            new_files_list = list(new_files)
            if len(new_files_list) > 1:
                new_files_list.sort(key=os.path.getmtime, reverse=True)
                print(f"   [DEBUG] 检测到 {len(new_files_list)} 个新文件，选择最新的: {new_files_list[0]}")

            new_file = new_files_list[0]
            print(f"   [DEBUG] ✓ 使用新生成的文件: {new_file}")

            print(f"   [DEBUG] 重命名文件: {new_file} -> {target_filename}")
            os.rename(new_file, target_filename)

            file_size = os.path.getsize(target_filename)
            print(f"   [DEBUG] ✓ 最终文件: {target_filename} (大小: {file_size} 字节)")
            return {
                "image_path": target_filename,
                "execution_output": execution_output,
                "execution_success": True
            }

        if os.path.exists(target_filename):
            file_size = os.path.getsize(target_filename)
            print(f"   [DEBUG] ✓ 找到目标文件（可能是更新后的）: {target_filename} (大小: {file_size} 字节)")
            return {
                "image_path": target_filename,
                "execution_output": execution_output,
                "execution_success": True
            }

        print(f"   [DEBUG] ✗ 图片生成失败，没有生成新文件且目标文件不存在")
        return {
            "error": "图片生成失败，代码执行后未生成图片",
            "execution_output": execution_output,
            "execution_success": False
        }
    except Exception as e:
        import traceback
        error_msg = f"执行代码失败: {str(e)}"
        print(f"   [DEBUG] ✗ 异常发生: {error_msg}")
        print(f"   [DEBUG] 完整堆栈跟踪:")
        traceback.print_exc()

        # 构建执行输出
        exc_output = error_msg + "\n" + traceback.format_exc()
        return {
            "error": error_msg,
            "execution_output": f"STDOUT:\n\nSTDERR:\n\nEXCEPTION:\n{exc_output}",
            "execution_success": False
        }

def save_image(state: GraphState) -> GraphState:
    """验证并保存图片信息"""
    print("4. 正在验证图片保存...")

    if state.get("error"):
        print(f"   [DEBUG] 状态中已包含错误，跳过验证: {state['error']}")
        return state

    try:
        image_path = state["image_path"]
        print(f"   [DEBUG] 验证图片路径: '{image_path}'")

        if os.path.exists(image_path):
            size = os.path.getsize(image_path)
            print(f"   [DEBUG] ✓ 图片验证成功: {image_path} (大小: {size} 字节)")
            return {"image_size": size}
        else:
            print(f"   [DEBUG] ✗ 图片文件不存在: {image_path}")
            return {"error": "图片保存失败"}
    except Exception as e:
        import traceback
        error_msg = f"验证图片失败: {str(e)}"
        print(f"   [DEBUG] ✗ 异常发生: {error_msg}")
        print(f"   [DEBUG] 完整堆栈跟踪:")
        traceback.print_exc()
        return {"error": error_msg}

def analyze_execution_result(state: GraphState) -> GraphState:
    """分析代码执行结果，决定是否需要修复重试（CodeAct核心节点）"""
    print("4. [CodeAct] 正在分析执行结果...")

    # 如果执行成功，直接进入保存流程
    if state.get("execution_success", False):
        print("   [DEBUG] ✓ 代码执行成功，准备保存图片")
        # 清除之前的错误状态（如果有）
        return {"error": "", "need_retry": False}

    # 检查重试次数
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)

    if retry_count >= max_retries:
        print(f"   [DEBUG] ✗ 已达到最大重试次数 ({max_retries})，停止重试")
        return {
            "error": f"达到最大重试次数({max_retries})仍无法生成图片",
            "need_retry": False
        }

    print(f"   [DEBUG] ⚠️ 代码执行失败 (第 {retry_count + 1}/{max_retries + 1} 次尝试)")
    print(f"   [DEBUG] 执行输出: {state.get('execution_output', 'N/A')[:500]}...")

    # 调用AI分析错误并生成修复反馈
    try:
        # 初始化LLM客户端
        client = LLMClientFactory.create_client()

        # 基础返回值（清除之前的错误状态，准备重试）
        base_result = {
            "error": "",
            "need_retry": True,
            "retry_count": retry_count + 1
        }

        if not client.config.api_key or client.config.api_key == 'ollama':
            if client.config.provider == 'deepseek':
                print("   [WARNING] 未设置API Key，使用简单错误重试")
                base_result["fix_feedback"] = f"执行失败，请修复以下错误：\n{state.get('execution_output', '')}"
                return base_result
            # Ollama provider - continue to use AI
            print(f"   [DEBUG] 使用 {client.config.provider} 进行错误分析")

        # 构建分析提示词
        analysis_prompt = f"""你是一个专业的Python代码调试专家，专门修复matplotlib绘图代码。

## 原始需求
{state.get('user_prompt', '')}

## 润色后的需求
{state.get('refined_prompt', '')}

## 当前代码（执行失败）
```python
{state.get('generated_code', '')}
```

## 执行输出
```
{state.get('execution_output', '')}
```

## 你的任务
请分析上述代码执行失败的原因，并提供具体的修复指导。

### 常见问题检查清单
1. **语法错误**：括号未闭合、引号未配对、缩进错误
2. **变量未定义**：使用了未定义的变量
3. **matplotlib导入问题**：缺少必要的导入
4. **数据问题**：NaN/Inf值、空数组、除零错误
5. **文件路径问题**：savefig路径错误、目录不存在
6. **中文字体问题**：字体配置错误
7. **LaTeX语法错误**：特殊字符格式错误

## 输出格式
请直接输出修复建议，格式如下：

**问题诊断**：[简要说明问题原因]

**修复方案**：[具体的修复步骤]

**修复后的代码**：
```python
[完整的修复后的代码]
```

注意：修复后的代码必须是完整的、可执行的，包含所有必要的导入、数据定义、绘图和保存操作。"""

        print("   [DEBUG] 正在调用AI分析错误...")
        response = client.chat_completion(
            messages=[
                {"role": "system", "content": "你是Python matplotlib代码调试专家"},
                {"role": "user", "content": analysis_prompt}
            ],
            model=client.config.model_name,
            temperature=0.3,
            max_tokens=4096,
            stream=False,
            think=client.config.enable_thinking  # 新增：启用 thinking 模式
        )

        fix_feedback = response.choices[0].message.content.strip()
        print(f"   [DEBUG] ✓ AI分析完成，反馈长度: {len(fix_feedback)} 字符")
        print(f"   [DEBUG] AI反馈片段: {fix_feedback[:300]}...")

        base_result["fix_feedback"] = fix_feedback
        return base_result

    except Exception as e:
        import traceback
        print(f"   [WARNING] AI分析失败: {str(e)}")
        traceback.print_exc()

        # AI分析失败时，使用简单的重试机制
        base_result["fix_feedback"] = f"代码执行失败：\n{state.get('execution_output', '')}\n\n请重新生成正确的代码。"
        return base_result

def fix_code_with_feedback(state: GraphState, stream_callback=None) -> GraphState:
    """根据AI分析反馈修复代码（CodeAct核心节点）

    Args:
        state: 工作流状态
        stream_callback: 可选的回调函数，用于发送流式响应内容
    """
    retry_count = state.get("retry_count", 1)
    print(f"5. [CodeAct] 正在修复代码 (第 {retry_count} 次尝试)...")

    try:
        # 初始化LLM客户端
        client = LLMClientFactory.create_client()

        # 基础返回值（清除之前的错误状态，准备重新执行）
        base_result = {"error": "", "generated_code": ""}

        if not client.config.api_key or client.config.api_key == 'ollama':
            if client.config.provider == 'deepseek':
                return {"error": "未设置 DEEPSEEK_API_KEY", "need_retry": False}

        # 构建修复提示词
        fix_prompt = f"""你是一个专业的Python matplotlib代码修复专家。

## 原始需求
{state.get('user_prompt', '')}

## 润色后的需求
{state.get('refined_prompt', '')}

## 失败的代码
```python
{state.get('generated_code', '')}
```

## 执行输出
```
{state.get('execution_output', '')}
```

## AI分析反馈
{state.get('fix_feedback', '')}

## 你的任务
根据上述分析反馈，修复代码并输出完整可执行的版本。

## 修复原则
1. **直接修复**：根据分析反馈直接修复问题
2. **保持完整**：确保代码包含所有必要的导入、数据、绘图和保存
3. **避免相同错误**：确保不会重复相同的错误
4. **自包含代码**：所有变量和数据必须显式定义
5. **使用target_filename**：保存时使用 target_filename 变量

## 绘图规范（必须遵守）
- 中文字体配置：matplotlib.rcParams['font.sans-serif'] = ['STHeiti', 'Heiti TC', 'PingFang SC', 'Arial Unicode MS', 'SimHei']
- 特殊字符使用LaTeX格式：r'$\alpha$', r'$\theta$' 等
- 显式设置坐标轴范围：ax.set_xlim(), ax.set_ylim()
- 数据验证：检查NaN/Inf，使用 np.nan_to_num() 处理
- 密集数据点：至少1000个点

请直接输出完整的修复后的Python代码，不要包含任何解释。"""

        print("   [DEBUG] 正在调用AI修复代码...")
        stream = client.chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": get_drawing_system_prompt()
                },
                {"role": "user", "content": fix_prompt}
            ],
            model=client.config.model_name,
            temperature=0.3,
            max_tokens=8192,
            stream=True,
            think=client.config.enable_thinking  # 新增：启用 thinking 模式
        )

        # 收集流式响应
        fixed_code = ""
        print("   [DEBUG] 开始接收修复后的代码...")

        if stream is None:
            return {"error": "LLM API 返回空响应，请检查模型配置和网络连接"}

        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content is not None:
                content = delta.content
                fixed_code += content
                # 如果有流式回调，实时发送内容
                if stream_callback:
                    stream_callback(content, content_type='content')

        fixed_code = fixed_code.strip()
        print(f"   [DEBUG] ✓ 修复代码接收完成，长度: {len(fixed_code)} 字符")

        # 去除可能的markdown格式
        if fixed_code.startswith('```python'):
            fixed_code = fixed_code[10:-3].strip()
            print("   [DEBUG] 移除了 ```python 标记")
        elif fixed_code.startswith('```'):
            fixed_code = fixed_code[3:-3].strip()
            print("   [DEBUG] 移除了 ``` 标记")

        print(f"   [DEBUG] 最终代码长度: {len(fixed_code)} 字符")
        print(f"   [DEBUG] 代码片段 (前200字符):\n{fixed_code[:200]}")

        base_result["generated_code"] = fixed_code
        return base_result  # 包含 error="", 允许重新执行

    except Exception as e:
        import traceback
        error_msg = f"修复代码失败: {str(e)}"
        print(f"   [DEBUG] ✗ {error_msg}")
        traceback.print_exc()
        return {"error": error_msg, "need_retry": False, "generated_code": state.get('generated_code', '')}  # 修复失败，不再重试

def create_graph():
    """创建并编译工作流图（CodeAct模式：带反馈循环）"""
    workflow = StateGraph(GraphState)

    # 添加所有节点
    workflow.add_node("refine_prompt", refine_prompt)
    workflow.add_node("generate_code", generate_code)
    workflow.add_node("execute_code", execute_code)
    workflow.add_node("analyze_execution_result", analyze_execution_result)  # 新增
    workflow.add_node("fix_code_with_feedback", fix_code_with_feedback)    # 新增
    workflow.add_node("save_image", save_image)

    workflow.set_entry_point("refine_prompt")

    # 定义工作流边（线性流程 + CodeAct反馈循环）
    workflow.add_edge("refine_prompt", "generate_code")
    workflow.add_edge("generate_code", "execute_code")
    workflow.add_edge("execute_code", "analyze_execution_result")  # 修改：执行后先分析

    # 条件边：根据分析结果决定是保存还是重试
    def should_retry(state: GraphState) -> str:
        """判断是否需要重试修复代码

        优先级顺序：
        1. 如果 need_retry=True，说明需要修复代码（不管是否有旧错误）
        2. 如果有 error，说明达到最大重试次数或其他致命错误，结束工作流
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

def main():
    """主函数, 处理用户输入并运行工作流"""
    if len(sys.argv) > 1:
        user_prompt = ' '.join(sys.argv[1:])
    else:
        user_prompt = input("请输入你的绘图需求：")

    try:
        graph = create_graph()

        result = graph.invoke({
            "user_prompt": user_prompt,
            "generated_code": "",
            "image_path": "",
            "image_size": 0,
            "error": "",
            "custom_filename": "",
            # CodeAct 模式初始化字段
            "execution_output": "",
            "execution_success": False,
            "retry_count": 0,
            "max_retries": 3,
            "fix_feedback": "",
            "need_retry": False
        })

        if result.get("error"):
            print(f"❌ 错误: {result['error']}")
            sys.exit(1)
        else:
            print(f"✅ 绘图成功！图片已保存到: {result['image_path']}")
            print(f"📏 图片大小: {result['image_size'] / 1024:.2f} KB")
            print(f"📝 生成的代码:\n{result['generated_code']}")

            abs_path = os.path.abspath(result['image_path'])
            print(f"📍 图片绝对路径: {abs_path}")

    except Exception as e:
        print(f"❌ 工作流运行失败: {str(e)}")
        sys.exit(1)


# ==================== 公共函数（供 draw_pic.py 和 write_md_with_images.py 共同使用）====================

def get_drawing_system_prompt() -> str:
    """
    获取绘图系统提示词（包含完整的绘图规范）

    这个函数被两种模式共同使用

    返回:
        完整的绘图系统提示词
    """
    return r"""你是一个专业的数据可视化和工程绘图专家，请根据用户需求生成高质量的Python绘图代码。

## 零、代码质量要求（最重要）

### 0.1 语法正确性
**括号匹配生死攸关**：生成代码后必须检查所有括号闭合：
- 每个`()`、`[]`、`{}`必须正确配对
- 每个函数调用必须以`)`结尾
- 特别注意`ax.annotate()`, `ax.plot()`, `dict()`等嵌套函数
- 所有字符串引号必须闭合

### 0.2 代码完整性
- 代码必须完整结束，不被截断
- 所有函数调用参数完整
- 多行语句使用正确续行

### 0.3 变量定义完整性
**绝对禁止使用未定义变量**：
- 所有变量在使用前必须明确定义
- 禁止引用假设的外部数据（如article、data、result等）
- 禁止使用单字母未定义变量（如x、y、k等）
- 数据必须在代码中显式定义或生成

## 一、技术要求

1. 只使用matplotlib库（配合numpy等基础库）
2. 代码完整：导入、数据生成、绘图、保存
3. 保存路径使用target_filename变量
4. 只返回可执行代码，无解释文字
5. **代码生成完成后，必须运行它来生成图片**（使用target_filename保存）
6. **代码自包含**：所有变量在代码中定义，不假设外部数据
7. **matplotlib导入规范**：
   - 基础：`import matplotlib.pyplot as plt`和`import matplotlib.patches as patches`
   - 图形类：`from matplotlib.patches import Rectangle, Circle, Arc, Polygon`
   - 箭头用`ax.annotate()`的`arrowprops`参数
   - **禁止**：`from matplotlib.patches import Line2D`（应从`matplotlib.lines`导入）
   - **禁止**：`from matplotlib.patches import pathpatch_2d_to_3d`（不存在）
   - 3D绘图：直接使用mpl_toolkits.mplot3d的方法
8. **样式规范**：禁止使用已弃用样式（如`plt.style.use('seaborn-darkgrid')`）
9. **颜色线型规范**（生死攸关）：
   - **禁止**：在`color`参数中使用格式字符串（如'k--', 'b-'等）
   - 正确：分离指定`color='blue', linestyle='--'`或使用位置参数`'k--'`
10. **中文显示**：
    ```python
    matplotlib.rcParams['font.sans-serif'] = [
        'STHeiti', 'Heiti TC', 'Heiti SC', 'Hiragino Sans GB',
        'PingFang SC', 'Arial Unicode MS', 'SimHei', 'STSong', 'Songti SC'
    ]
    matplotlib.rcParams['axes.unicode_minus'] = False
    ```

## 二、通用绘图规范

### 2.1 图形尺寸
- figsize=(10, 8)，dpi=100或更高
- 使用`plt.tight_layout()`自动调整

### 2.2 线条样式
- 主要元素：linewidth=2-3
- 次要元素：linewidth=1-1.5
- 辅助线：linewidth=0.5-1

### 2.3 标注规范
- 所有重要部分有中文标注
- **图片中的文字语言原则**：除科学符号（如LaTeX格式的数学符号、希腊字母、量子态符号等）和必要的英文字符（如变量名、函数名、专有名词等）外，所有文字都应使用中文
- 使用`ax.annotate()`添加箭头标注
- **实心物体文字在外部**，空心物体可在内部
- 使用`bbox=dict(boxstyle='round', facecolor='white', alpha=0.8)`添加背景
- 标题14-16，轴标签12-14，标注10-12

### 2.4 颜色方案
- 推荐色：蓝色('#1f77b4')、红色('#d62728')、绿色('#2ca02c')
- 背景白色

### 2.5 坐标轴
- 使用`plt.grid(True, alpha=0.3)`添加网格
- 比例图形使用`ax.set_aspect('equal')`
- 保存使用`bbox_inches='tight'`

### 2.6 特殊字符规范（最重要！**全部使用LaTeX格式**）
**核心原则**：所有特殊字符必须用LaTeX格式，禁止Unicode字符
- 希腊字母：`r'$\alpha$'`、`r'$\theta$'`、`r'$\pi$'`等
- 量子态：`r'$|0\rangle$'`、`r'$|1\rangle$'`、`r'$\langle\psi|$'`等
- 数学符号：`r'$\infty$'`、`r'$\pm$'`、`r'$\times$'`等
- **必须**：原始字符串前缀`r` + 美元符号`$...$`包围
- **禁止**：不支持的LaTeX命令（如`\xrightarrow`）

### 2.7 图层顺序
- 背景(zorder=0-1)→网格(zorder=1)→辅助线(zorder=2)→主体(zorder=3-5)→填充(zorder=3-4, alpha=0.3-0.7)→边框(zorder=5-6)→箭头(zorder=10)→文字(zorder=10)

### 2.8 文字标注布局（最重要！**无重叠**）
**核心原则**：图示和文字在空白位置，相互不重叠
- 预先规划标注位置，利用空白区域
- 实心物体标注在外部，使用箭头指向
- 分散标注到不同空白区域
- 使用引线延伸到外部空白区域
- 调整坐标轴范围创造更多空白
- 为所有标注添加半透明背景盒
- 使用`transform=ax.transAxes`定位到图形边缘
- 多个标注使用不同xytext偏移量
- 密集区域使用弯曲引线引导到外部

### 2.9 元素重叠规范（最重要！**所有元素不重叠**）
**核心原则**：绘图中的各个元素都不应有重叠
- 图形元素之间互不重叠
- 文字标注不与图形元素重叠
- 文字标注之间互不重叠
- 箭头不穿过其他元素
- 使用图层顺序和透明度处理必要重叠
- 通过坐标调整避免元素重叠
- 必要时扩大图形尺寸或调整布局

## 三、分类绘图规范

### 3.1 数据可视化类
**基本要求**：标题、轴标签、图例、网格、marker符号
**防止空白图像**：
- 数据范围验证：打印数据范围，检查NaN/Inf
- 颜色显式指定：所有`ax.plot()`指定`color`
- 坐标轴范围显式设置：`ax.set_xlim/ylim()`
- 特殊函数输出验证：使用`np.nan_to_num()`清理
- 子图数据单独验证
**数据生成**：使用numpy生成密集数据（至少1000点）
**曲线绘制**：`linewidth=2-3`，颜色醒目
**坐标轴**：显式设置范围，标签用LaTeX格式
**特殊标注**：标注关键点（极值、临界点、能隙等），LaTeX格式，空白区域
**元素重叠检查**：多条曲线使用不同颜色，确保可区分；图例不遮挡曲线

### 3.2 物理示意图类
**刚体约束**：
- 接触面完全贴合，无穿模或间隙
- 斜面物体底部精确计算坐标（三角函数）
- 轮子接触面，轮心到接触面距离=半径
- 重力严格垂直向下
- 角度精确，标注一致
**角度标注**：顶点在支点/转轴，绘制垂直向下虚线参考
**力的标注**：
- 重力mg：垂直向下
- 支持力N：垂直接触面（三角函数计算）
- 拉力T：沿绳远离物体
- 摩擦力f：沿接触面
- 力符号用LaTeX格式`r'$mg$'`等
- **力箭头文字在空白区域，分散放置**
**文字标注**：实心物体外部，空心物体可内外，空白区域
**元素重叠检查**：物体间不重叠，力箭头不穿过物体

### 3.3 几何图形类
- Arc中心点为顶点，width=height=2*半径
- theta1/theta2为角度值（度数）
- 角度符号LaTeX格式
- **角度文字在空白区域**
- 保持比例`ax.set_aspect('equal')`
- **元素重叠检查**：几何图形间不重叠，角度标注不干扰图形

### 3.4 流程图/架构图
- 矩形框表示模块
- 箭头表示流程
- 层级清晰，统一间距
- **文字在空白区域**
- **元素重叠检查**：模块框互不重叠，箭头不穿过模块

### 3.5 函数图像类
- 密集数据点（np.linspace）
- 标注关键点
- 特殊字符LaTeX格式
- **标注在空白区域，避免与曲线重叠**
- **元素重叠检查**：曲线与坐标轴、标注分离，确保清晰可读

## 四、代码结构模板

### 4.1 基础模板
```python
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle, Circle, Arc, Polygon
from matplotlib.lines import Line2D
import numpy as np

# 中文字体
matplotlib.rcParams['font.sans-serif'] = [
    'STHeiti', 'Heiti TC', 'Heiti SC', 'Hiragino Sans GB',
    'PingFang SC', 'Arial Unicode MS', 'SimHei', 'STSong', 'Songti SC'
]
matplotlib.rcParams['axes.unicode_minus'] = False

fig, ax = plt.subplots(figsize=(10, 8), dpi=100)

# 数据定义和验证（必须）
x = np.linspace(0, np.pi, 1000)
y = np.sin(x)
print(f"数据范围: {y.min()}, {y.max()}")
if np.all(y == 0) or np.any(np.isnan(y)) or np.any(np.isinf(y)):
    raise ValueError("数据无效")

# 绘图
ax.plot(x, y, 'b-', linewidth=2, label=r'$\sin(x)$')  # LaTeX格式

# 标注（空白区域）
ax.annotate('标注', xy=(x1, y1), xytext=(x2, y2),
            arrowprops=dict(arrowstyle='->', lw=1.5),
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))

# 设置
ax.set_xlim(x.min(), x.max())
ax.set_ylim(y.min()*0.9, y.max()*1.1)
ax.set_xlabel(r'$x$', fontsize=12)
ax.set_ylabel(r'$y$', fontsize=12)
ax.grid(True, alpha=0.3)
ax.legend()
plt.tight_layout()
plt.savefig(target_filename, dpi=100, bbox_inches='tight')
plt.close()
```

## 五、角度标注示例

```python
# 单摆角度
theta_deg = 30
arc = Arc((pivot_x, pivot_y), width=0.6, height=0.6, angle=0,
          theta1=270, theta2=270+theta_deg, color='red', lw=2)
ax.add_patch(arc)

# 角度文字（空白区域）
mid_angle = np.radians(270 + theta_deg/2)
label_x = pivot_x + 0.45 * np.cos(mid_angle)
label_y = pivot_y + 0.45 * np.sin(mid_angle)
ax.annotate(r'$\theta$', xy=(label_x, label_y), fontsize=14,
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))
```

## 六、力标注示例

```python
# 斜面上的力
theta = np.radians(30)
center_x, center_y = 2.0, 1.0

# 重力
ax.annotate(r'$mg$', xy=(center_x, center_y-0.3),
            xytext=(center_x-0.7, center_y-0.7),  # 空白区域
            arrowprops=dict(arrowstyle='->', color='red', lw=2))

# 支持力
normal_angle = theta - np.pi/2
ax.annotate(r'$N$', xy=(center_x+0.4*np.cos(normal_angle), center_y+0.4*np.sin(normal_angle)),
            xytext=(center_x+0.7*np.cos(normal_angle), center_y+0.7*np.sin(normal_angle)),
            arrowprops=dict(arrowstyle='->', color='green', lw=2))
```

## 七、质量检查清单

### 语法检查
□ 所有括号`()`、`[]`、`{}`闭合
□ 所有引号`'"`闭合
□ 每个函数调用以`)`结尾
□ 所有变量已定义
□ 数据点足够密集（≥1000）
□ 坐标轴范围显式设置

### 特殊字符检查（最重要！）
□ 希腊字母LaTeX格式：`r'$\alpha$'`，不是`'α'`
□ 量子态LaTeX格式：`r'$|0\rangle$'`，不是`'|0⟩'`
□ 数学符号LaTeX格式：`r'$\infty$'`，不是`'∞'`
□ 所有LaTeX字符串有`r`前缀
□ 数学表达式用`$...$`包围
□ 避免不支持的LaTeX命令

### 布局检查（最重要！）
□ 所有标注在空白区域
□ 标注不与图形重叠
□ 标注不互相重叠
□ 使用半透明背景盒
□ 多个标注分散到不同空白区域
□ 引线不穿过图形元素
□ 坐标轴范围适当，留出边距

### 元素重叠检查（最重要！）
□ 图形元素之间互不重叠
□ 文字标注不与图形元素重叠
□ 文字标注之间互不重叠
□ 箭头不穿过其他元素
□ 图例不遮挡数据曲线
□ 多条曲线使用不同颜色确保可区分
□ 物体间无穿模或间隙
□ 力箭头不穿过物体

### 文字语言检查
□ 除科学符号和必要英文字符外，所有文字使用中文
□ 标题使用中文
□ 轴标签使用中文
□ 标注说明使用中文
□ 图例使用中文

### 防止空白图像
□ 数据验证代码存在
□ 颜色显式指定
□ 坐标轴范围动态设置
□ 特殊函数输出验证
□ 子图数据单独验证

### 物理示意图
□ 刚体约束满足（贴合接触面）
□ 角度顶点在支点
□ 力的方向正确（重力垂直，支持力垂直接触面）
□ 力符号LaTeX格式
□ 力箭头文字在空白区域

### 导入和图层
□ 从`matplotlib.lines`导入Line2D
□ 图层顺序正确
□ 使用zorder参数
□ 填充区域有alpha透明度

## 八、最终检查

**输出前必须执行**：
1. 括号匹配检查：逐个检查每个`(`都有`)`
2. 变量定义检查：所有使用变量已定义
3. 数据有效性检查：打印范围，验证NaN/Inf
4. 特殊字符检查：全部使用LaTeX格式
5. 布局检查：所有标注在空白区域，无重叠
6. 文字语言检查：除科学符号和英文外使用中文
7. **元素重叠检查：绘图中的各个元素都不应有重叠**
8. 脑中执行：确认每行代码完整

**输出后必须执行**：
9. **运行生成的代码**：执行代码生成图片文件（保存到target_filename）
10. 确认图片生成成功且质量符合要求

**✓ 检查全部通过后输出代码并运行生成图片！**
**✗ 发现任何问题立即修复！**"""


def generate_single_image(description: str, custom_filename: str = None) -> dict:
    """
    生成单张图片(供文本+图模式调用)

    这个函数封装了绘图工作流,提供简单的接口供文档模式调用

    参数:
        description: 图片描述(用户需求)
        custom_filename: 自定义文件名,如 "plot_something_20260104_123456.png"
                       如果为None,则使用默认命名规则

    返回:
        dict: {
            'success': bool,        # 是否成功
            'image_path': str,      # 图片完整路径(成功时)
            'image_size': int,      # 文件大小(成功时)
            'relative_path': str,   # 相对路径 "../images/xxx.png"(成功时)
            'error': str            # 错误信息(失败时)
        }
    """
    try:
        print(f"\n[WORKFLOW] ===== 单图生成工作流启动 =====")
        print(f"[WORKFLOW] 图片描述: '{description}'")
        if custom_filename:
            print(f"[WORKFLOW] 自定义文件名: '{custom_filename}'")

        # 创建工作流
        graph = create_graph()

        # 准备初始状态
        initial_state = {
            "user_prompt": description,
            "refined_prompt": "",
            "generated_code": "",
            "image_path": "",
            "image_size": 0,
            "error": "",
            "custom_filename": custom_filename or "",  # 传递自定义文件名
            # CodeAct 模式初始化字段
            "execution_output": "",
            "execution_success": False,
            "retry_count": 0,
            "max_retries": 3,
            "fix_feedback": "",
            "need_retry": False
        }

        # 执行工作流
        print(f"[WORKFLOW] 开始执行工作流...")
        result = graph.invoke(initial_state)

        print(f"[WORKFLOW] ===== 工作流执行完成 =====")

        # 处理结果
        if result.get("error"):
            print(f"[WORKFLOW] ❌ 生成失败: {result['error']}")
            return {
                'success': False,
                'error': result['error']
            }

        # 成功生成图片
        image_path = result['image_path']
        image_size = result['image_size']

        # 计算相对路径(相对于 docs 目录)
        filename = os.path.basename(image_path)
        relative_path = f"../images/{filename}"

        print(f"[WORKFLOW] ✅ 生成成功:")
        print(f"[WORKFLOW]   - 完整路径: {image_path}")
        print(f"[WORKFLOW]   - 相对路径: {relative_path}")
        print(f"[WORKFLOW]   - 文件大小: {image_size} 字节")

        return {
            'success': True,
            'image_path': image_path,
            'image_size': image_size,
            'relative_path': relative_path
        }

    except Exception as e:
        import traceback
        error_msg = f"工作流异常: {str(e)}"
        print(f"[WORKFLOW] ❌ {error_msg}")
        traceback.print_exc()
        return {
            'success': False,
            'error': error_msg
        }


if __name__ == "__main__":
    main()
