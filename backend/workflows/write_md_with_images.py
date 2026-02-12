import os
import sys
import re
from typing import TypedDict, List, Dict
from langgraph.graph import StateGraph, END
from openai import OpenAI
from dotenv import load_dotenv
from config import Config

# 加载.env文件中的环境变量
load_dotenv()

# 定义状态结构
class GraphState(TypedDict):
    user_prompt: str
    refined_prompt: str
    document_outline: str
    markdown_content: str
    image_requests: List[Dict]  # 图片生成请求列表
    generated_images: List[Dict]  # 生成的图片信息
    final_content: str  # 带图片的最终文档内容
    output_path: str
    file_size: int
    error: str

# 润色写作需求的节点
def refine_prompt(state: GraphState) -> GraphState:
    """使用AI润色用户的写作需求，使其更适合生成高质量的文档"""
    print("1. 正在润色写作需求...")
    user_prompt = state["user_prompt"]

    try:
        print(f"✅ 原始需求: '{user_prompt}'")

        enhanced_prompt = f"""{user_prompt}

## 文档写作要求

### 基本要求
1. 使用标准的 Markdown 语法
2. 文档结构清晰，层次分明
3. 内容准确、详实、有深度
4. 语言简洁、专业、易懂
5. 适当地使用标题、列表、代码块、表格等格式
6. 包含必要的示例和说明
7. 在适当位置插入图表、示意图等可视化内容
8. 对于技术、科学、数据相关内容，确保包含必要的图表

### 可视化内容要求
- 对于数据说明，使用图表（柱状图、折线图、散点图等）
- 对于物理概念，使用力学示意图、电路图等
- 对于流程说明，使用流程图、架构图
- 对于数学概念，使用函数图像、几何图形
- 图表应该与正文内容紧密相关，帮助读者理解

### 数学公式要求（重要）
**如果文档包含数学公式，必须严格遵守以下规则：**
1. **使用 KaTeX 兼容的语法**：前端使用 KaTeX 渲染数学公式，仅支持 KaTeX 支持的 LaTeX 命令
2. **避免不兼容的命令**：
   - ❌ 不要使用 `\\cdotp`、`\\*` 等不兼容命令
   - ✅ 使用 `\\cdot` 代替 `\\cdotp`
   - ✅ 使用简单的 LaTeX 命令，确保兼容性
3. **公式格式**：
   - 行内公式：使用 `$公式$` 或 `\\(公式\\)`
   - 独立公式块：使用 `$$公式$$` 或 `\\[公式\\]`
4. **常用且兼容的数学符号**：
   - 希腊字母：`\\alpha`, `\\beta`, `\\gamma`, `\\delta`, `\\theta`, `\\lambda`, `\\mu`, `\\sigma`, `\\phi`, `\\omega` 等
   - 运算符：`\\cdot`, `\\times`, `\\div`, `\\pm`, `\\mp`, `\\approx`, `\\equiv`, `\\sim`, `\\propto`
   - 关系符号：`\\leq`, `\\geq`, `\\ll`, `\\gg`, `\\neq`, `\\subset`, `\\supset`, `\\in`, `\\notin`
   - 箭头：`\\rightarrow`, `\\leftarrow`, `\\Rightarrow`, `\\Leftarrow`, `\\leftrightarrow`, `\\Leftrightarrow`
    - 上下标：`x^2`, `x_1`, `x^{{2n}}`, `x_{{i,j}}`
    - 分数：`\\frac{{a}}{{b}}`
    - 根号：`\\sqrt{{x}}`, `\\sqrt[n]{{x}}`
    - 求和与积分：`\\sum`, `\\int`, `\\prod`, `\\lim`
    - 矩阵与括号：`\\begin{{matrix}} ... \\end{{matrix}}`, `\\left( \\right)`, `\\left[ \\right]`

### 文档结构规范
- **标题层级**：使用 # ## ### #### 等标记标题层级
- **段落组织**：段落之间空一行，提高可读性
- **列表使用**：
  - 无序列表使用 - 或 *
  - 有序列表使用 1. 2. 3.
  - 列表项适当缩进
- **代码块**：使用 ```语言名称 ... ``` 包裹代码
- **强调**：使用 **粗体** 或 *斜体* 强调重点
- **图片引用**：使用标准Markdown语法 ![描述](路径)"""

        print(f"✅ 增强后的提示词已生成")
        return {"refined_prompt": enhanced_prompt}
    except Exception as e:
        error_msg = f"润色提示词失败: {str(e)}"
        print(f"❌ {error_msg}")
        return {"refined_prompt": user_prompt}

# 生成文档大纲的节点
def generate_outline(state: GraphState, stream_callback=None) -> GraphState:
    """根据润色后的需求生成文档大纲
    
    Args:
        state: 工作流状态
        stream_callback: 可选的回调函数，用于发送流式响应内容
    """
    print("2. 正在生成文档大纲...")
    user_prompt = state["refined_prompt"]

    try:
        api_key = os.getenv("DEEPSEEK_API_KEY")
        print(f"   [DEBUG] API Key 状态: {'已设置' if api_key else '未设置'}")

        if not api_key:
            return {"error": "未设置 DEEPSEEK_API_KEY，请在 .env 文件中配置"}

        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )

        print(f"   [DEBUG] 正在调用 DeepSeek 模型生成大纲（流式模式）...")
        stream = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": """你是一个专业的文档架构师，擅长为各种主题设计清晰、完整的文档大纲。

请根据用户需求生成一个详细的文档大纲，要求：
1. 大纲应包含多级标题（使用 Markdown 的 # ## ### #### 语法）
2. 每个主要部分应该有简短的内容说明
3. 结构合理，逻辑清晰
4. 覆盖主题的所有重要方面
5. 标注哪些章节需要图表或可视化内容
6. 在需要图表的章节后添加 [需要图表] 标记
7. 只返回大纲内容，不要有其他解释性文字

示例格式：
# 主标题

## 第一部分：简介 [需要图表]
- 背景介绍
- 核心概念

## 第二部分：核心内容
### 2.1 概念一 [需要图表]
- 详细说明
- 示例

### 2.2 概念二
- 详细说明
- 示例 [需要图表]
"""
                },
                {
                    "role": "user",
                    "content": f"""请为以下主题生成一个详细的文档大纲：

{user_prompt}

要求：
1. 生成完整的文档大纲结构
2. 包含多级标题
3. 每个主要部分有内容说明
4. 标记需要图表的章节（添加 [需要图表]）
5. 只返回大纲内容，使用Markdown格式"""
                }
            ],
            temperature=0.5,
            max_tokens=3000,
            stream=True
        )

        # 收集流式响应
        outline = ""
        print(f"   [DEBUG] 开始接收流式响应...")
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                outline += content
                # 如果有流式回调，实时发送内容
                if stream_callback:
                    stream_callback(content)
                
        outline = outline.strip()
        print(f"   [DEBUG] 大纲生成完成，长度: {len(outline)} 字符")
        print(f"   [DEBUG] 流式响应接收完成")

        if outline.startswith('```markdown'):
            outline = outline[12:-3].strip()
        elif outline.startswith('```'):
            outline = outline[3:-3].strip()

        print(f"✅ 文档大纲生成完成")
        return {"document_outline": outline}
    except Exception as e:
        import traceback
        error_msg = f"生成大纲失败: {str(e)}"
        print(f"❌ {error_msg}")
        traceback.print_exc()
        default_outline = f"# {state['user_prompt']}\n\n## 简介 [需要图表]\n- 背景介绍\n\n## 主要内容\n- 核心概念 [需要图表]\n- 详细说明\n\n## 总结\n- 要点总结\n"
        print(f"   [INFO] 使用默认大纲")
        return {"document_outline": default_outline}

# 生成Markdown文档内容的节点
def generate_content(state: GraphState, stream_callback=None) -> GraphState:
    """根据大纲生成完整的Markdown文档内容（包含图片占位符）
    
    Args:
        state: 工作流状态
        stream_callback: 可选的回调函数，用于发送流式响应内容
    """
    print("3. 正在生成文档内容...")

    try:
        api_key = os.getenv("DEEPSEEK_API_KEY")

        if not api_key:
            return {"error": "未设置 DEEPSEEK_API_KEY，请在 .env 文件中配置"}

        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )

        outline = state["document_outline"]
        user_prompt = state["refined_prompt"]

        print(f"   [DEBUG] 正在调用 DeepSeek 模型生成完整文档（流式模式）...")
        stream = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": """你是一个专业的技术文档作家，擅长撰写高质量的技术文档、教程和说明文档。

## 文档写作指南

### 1. Markdown 语法规范
- **标题**：使用 # ## ### #### 等标记层级，标题前后空一行
- **列表**：
  - 无序列表使用 - 或 *，每个列表项占一行
  - 有序列表使用 1. 2. 3.
  - 列表嵌套时使用2个空格缩进
- **代码块**：使用 ```language ... ``` 包裹，指定语言类型
- **代码行内**：使用 `代码` 包裹行内代码
- **强调**：使用 **粗体** 或 *斜体*
- **链接**：使用 [文字](URL) 格式
- **表格**：使用标准 Markdown 表格语法
- **图片**：使用标准语法 ![描述](图片路径)

### 2. 图片占位符规则
- 在大纲中标记 [需要图表] 的地方，插入图片占位符
- 占位符格式：`<!-- IMAGE_PLACEHOLDER: 1: 图片描述 -->`
- 编号从1开始递增
- 图片描述要清晰，说明图表应该展示什么内容
- 占位符应该放在段落后，独立成行

示例：
## 数据分析 [需要图表]
数据集包含1000条记录。

<!-- IMAGE_PLACEHOLDER: 1: 展示数据分布的柱状图 -->
下表显示了详细数据...

### 3. 内容组织原则
- **结构清晰**：按照大纲结构展开内容
- **段落分明**：段落之间空一行
- **逻辑连贯**：内容前后呼应，逻辑流畅
- **重点突出**：适当使用粗体、列表等方式突出重点

### 4. 内容质量要求
- **准确性**：信息准确，术语使用正确
- **完整性**：覆盖大纲中的所有要点
- **可读性**：语言简洁易懂，避免冗长
- **实用性**：提供有价值的知识和示例
- **专业性**：保持专业语气，使用恰当的术语

### 5. 数学公式要求（重要）
**如果文档包含数学公式，必须严格遵守以下规则：**
1. **使用 KaTeX 兼容的语法**
2. **避免不兼容的命令**：不要使用 `\\cdotp`、`\\*` 等不兼容命令
3. **公式格式**：
   - 行内公式：使用 `$公式$` 或 `\\(公式\\)`
   - 独立公式块：使用 `$$公式$$` 或 `\\[公式\\]`
4. **常用符号**：\\alpha, \\beta, \\cdot, \\frac{a}{b}, \\sqrt{x}, \\sum, \\int 等

### 6. 输出要求
- 只返回 Markdown 格式的文档内容
- 不要包含任何解释性文字或meta信息
- 确保每个标题、段落、列表格式正确
- 在适当位置插入图片占位符
- 代码块语法高亮标记正确"""
                },
                {
                    "role": "user",
                    "content": f"""请根据以下大纲生成完整的 Markdown 文档：

## 大纲：
{outline}

## 原始需求：
{user_prompt}

## 要求：
1. 严格按照大纲结构展开内容
2. 在标记 [需要图表] 的地方插入图片占位符 <!-- IMAGE_PLACEHOLDER: N: 描述 -->
3. 每个章节都要有详实的内容
4. 使用正确的 Markdown 语法
5. 内容准确、专业、易懂
6. 包含适当的示例和说明
7. 只返回文档内容，不要有其他解释

请开始生成完整文档："""
                }
            ],
            temperature=0.4,
            max_tokens=8000,
            stream=True
        )

        # 收集流式响应
        content = ""
        print(f"   [DEBUG] 开始接收流式响应...")
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                chunk_content = chunk.choices[0].delta.content
                content += chunk_content
                # 如果有流式回调，实时发送内容
                if stream_callback:
                    stream_callback(chunk_content)
                
        content = content.strip()
        print(f"   [DEBUG] 文档生成完成，长度: {len(content)} 字符")
        print(f"   [DEBUG] 流式响应接收完成")

        if content.startswith('```markdown'):
            content = content[12:-3].strip()
        elif content.startswith('```'):
            content = content[3:-3].strip()

        import re
        def fix_latex_backslashes(text):
            text = text.replace('\\\\\n', '___NEWLINE___')
            text = re.sub(r'\\\\([a-zA-Z]+)', r'\\\1', text)
            text = text.replace('___NEWLINE___', '\\\\\n')
            return text

        content = fix_latex_backslashes(content)

        print(f"✅ Markdown 文档内容生成完成")
        return {"markdown_content": content}
    except Exception as e:
        import traceback
        error_msg = f"生成文档内容失败: {str(e)}"

        error_str = str(e)
        if "401" in error_str or "403" in error_str or "Unauthorized" in error_str:
            error_msg = "DeepSeek API Key 无效或无权限。请检查 .env 文件中的 DEEPSEEK_API_KEY"
        elif "429" in error_str or "rate" in error_str.lower():
            error_msg = "DeepSeek API 调用频率限制，请稍后重试"
        elif "balance" in error_str.lower() or "insufficient" in error_str.lower():
            error_msg = "DeepSeek API 余额不足，请充值后重试"

        print(f"❌ {error_msg}")
        traceback.print_exc()
        return {"error": error_msg}

# 识别图片请求的节点
def identify_image_requests(state: GraphState) -> GraphState:
    """从文档内容中识别所有图片占位符，生成图片请求"""
    print("4. 正在识别图片需求...")

    try:
        content = state["markdown_content"]
        
        # 使用正则表达式查找所有图片占位符
        # 格式: <!-- IMAGE_PLACEHOLDER: N: 描述 -->
        pattern = r'<!--\s*IMAGE_PLACEHOLDER:\s*(\d+):\s*(.+?)\s*-->'
        matches = re.findall(pattern, content, re.IGNORECASE)
        
        image_requests = []
        for match in matches:
            image_num = int(match[0])
            description = match[1].strip()
            image_requests.append({
                "number": image_num,
                "description": description,
                "placeholder": f"<!-- IMAGE_PLACEHOLDER: {image_num}: {description} -->"
            })
        
        print(f"   [DEBUG] 识别到 {len(image_requests)} 个图片需求")
        for req in image_requests:
            print(f"   [DEBUG]   - 图片 {req['number']}: {req['description']}")
        
        print(f"✅ 图片需求识别完成")
        return {"image_requests": image_requests}
    except Exception as e:
        import traceback
        error_msg = f"识别图片需求失败: {str(e)}"
        print(f"❌ {error_msg}")
        traceback.print_exc()
        return {"image_requests": []}

# 增强图片描述的函数
def enhance_image_prompt_with_llm(image_description: str, document_context: str, original_prompt: str) -> str:
    """使用大模型增强图片描述，使其更适合生成高质量绘图"""
    try:
        api_key = os.getenv("DEEPSEEK_API_KEY")
        
        if not api_key:
            print(f"   [WARNING] 未设置 DEEPSEEK_API_KEY，跳过图片描述增强")
            return image_description
        
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        
        print(f"   [DEBUG] 正在增强图片描述: '{image_description}'")
        
        stream = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": """你是一个专业的数据可视化专家，需要将简短的图片需求转换为详细的绘图指令。

你的任务是将简单的图片描述转换为专业的绘图指令，添加必要的绘图规范、技术要求和细节。

要求：
1. 保持原始需求的核心意图
2. 添加专业的绘图技术要求
3. 指定图表类型、数据生成方式、视觉效果等
4. 确保生成的指令可以直接用于高质量的Python代码生成
5. 保持与文档主题和上下文的一致性

示例：
输入："展示波函数概率分布的图"
输出："绘制量子力学波函数的概率分布图，使用numpy生成x轴范围0到5，计算基态和第一激发态的波函数，用不同颜色表示，添加概率密度曲线，标注能级位置，设置中文标题和坐标轴标签"

直接输出增强后的绘图指令，不要添加解释。"""
                },
                {
                    "role": "user",
                    "content": f"""原始用户需求：{original_prompt}

文档上下文：{document_context}

图片需求：{image_description}

请提供增强后的绘图指令："""
                }
            ],
            temperature=0.3,
            max_tokens=500,
            stream=True
        )
        
        # 收集流式响应
        enhanced_description = ""
        print(f"   [DEBUG] 开始接收流式响应...")
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                chunk_content = chunk.choices[0].delta.content
                enhanced_description += chunk_content
                
        enhanced_description = enhanced_description.strip()
        print(f"   [DEBUG] 图片描述增强完成: '{enhanced_description[:100]}...'")
        print(f"   [DEBUG] 流式响应接收完成")
        return enhanced_description
        
    except Exception as e:
        print(f"   [WARNING] 图片描述增强失败: {str(e)}，使用原始描述")
        return image_description

# 提取文档上下文的辅助函数
def extract_document_context(state: GraphState, image_request: dict) -> str:
    """提取图片相关的文档上下文"""
    try:
        # 获取文档大纲和润色后的提示词
        document_outline = state.get("document_outline", "")
        refined_prompt = state.get("refined_prompt", "")
        
        # 提取图片占位符周围的上下文
        markdown_content = state.get("markdown_content", "")
        placeholder = image_request.get("placeholder", "")
        
        # 查找占位符在文档中的位置
        placeholder_index = markdown_content.find(placeholder)
        if placeholder_index == -1:
            return f"文档主题: {state.get('user_prompt', '')}\n文档大纲: {document_outline[:200]}..."
        
        # 提取占位符前后各5行作为上下文
        lines_before = []
        lines_after = []
        
        # 分割文档为行
        all_lines = markdown_content.split('\n')
        
        # 找到占位符所在行
        placeholder_line_index = -1
        for i, line in enumerate(all_lines):
            if placeholder in line:
                placeholder_line_index = i
                break
        
        if placeholder_line_index != -1:
            # 获取前5行
            start_index = max(0, placeholder_line_index - 5)
            lines_before = all_lines[start_index:placeholder_line_index]
            
            # 获取后5行
            end_index = min(len(all_lines), placeholder_line_index + 6)
            lines_after = all_lines[placeholder_line_index + 1:end_index]
        
        context_lines = lines_before + lines_after
        context_text = '\n'.join(context_lines)
        
        # 组合上下文信息
        full_context = f"""文档主题: {state.get('user_prompt', '')}
文档大纲: {document_outline[:300]}...
图片所在上下文:
{context_text}"""
        
        return full_context
        
    except Exception as e:
        print(f"   [WARNING] 提取文档上下文失败: {str(e)}")
        return f"文档主题: {state.get('user_prompt', '')}"

# 生成所有图片的节点
def generate_images(state: GraphState) -> GraphState:
    """根据图片请求生成所有需要的图片(复用绘图工作流)"""
    print("5. 正在生成图表...")

    try:
        # 导入公共的图片生成函数
        from workflows.draw_pic import generate_single_image

        image_requests = state["image_requests"]
        generated_images = []

        if not image_requests:
            print(f"   [INFO] 没有需要生成的图片")
            return {"generated_images": []}

        # 生成每张图片
        for i, req in enumerate(image_requests, 1):
            print(f"   [DEBUG] 正在生成图片 {i}/{len(image_requests)}: {req['description']}")

            try:
                # 提取文档上下文
                document_context = extract_document_context(state, req)
                original_prompt = state.get("user_prompt", "")
                
                # 使用大模型增强图片描述
                enhanced_description = enhance_image_prompt_with_llm(
                    req['description'], 
                    document_context, 
                    original_prompt
                )
                
                # 生成自定义文件名（基于原始描述）
                from datetime import datetime
                import re
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_description = re.sub(r'[^\w\u4e00-\u9fa5]', '_', req['description'][:20])
                custom_filename = f"plot_{safe_description}_{timestamp}.png"

                # 调用统一的绘图工作流（使用增强后的描述）
                result = generate_single_image(enhanced_description, custom_filename)

                if result['success']:
                    # 图片生成成功
                    generated_images.append({
                        "number": req['number'],
                        "description": req['description'],
                        "enhanced_description": enhanced_description,
                        "placeholder": req['placeholder'],
                        "path": result['image_path'],
                        "relative_path": result['relative_path'],
                        "size": result['image_size']
                    })
                    print(f"   [DEBUG] ✓ 图片 {i} 生成成功: {custom_filename} (大小: {result['image_size']} 字节)")
                    print(f"   [DEBUG]   原始描述: {req['description']}")
                    print(f"   [DEBUG]   增强描述: {enhanced_description[:100]}...")
                else:
                    # 图片生成失败
                    print(f"   [DEBUG] ✗ 图片 {i} 生成失败: {result.get('error', '未知错误')}")
                    generated_images.append({
                        "number": req['number'],
                        "description": req['description'],
                        "enhanced_description": enhanced_description,
                        "placeholder": req['placeholder'],
                        "path": None,
                        "relative_path": None,
                        "size": 0
                    })

            except Exception as e:
                print(f"   [DEBUG] ✗ 图片 {i} 生成失败: {str(e)}")
                import traceback
                traceback.print_exc()
                enhanced_description = enhance_image_prompt_with_llm(
                    req['description'], 
                    extract_document_context(state, req), 
                    state.get("user_prompt", "")
                )
                generated_images.append({
                    "number": req['number'],
                    "description": req['description'],
                    "enhanced_description": enhanced_description,
                    "placeholder": req['placeholder'],
                    "path": None,
                    "relative_path": None,
                    "size": 0
                })

        print(f"✅ 图表生成完成，共 {len(generated_images)} 张")
        return {"generated_images": generated_images}
    except Exception as e:
        import traceback
        error_msg = f"生成图表失败: {str(e)}"
        print(f"❌ {error_msg}")
        traceback.print_exc()
        return {"error": error_msg}

# 整合图片到文档的节点
def embed_images(state: GraphState) -> GraphState:
    """将生成的图片路径嵌入到文档中，替换占位符"""
    print("6. 正在整合图片到文档...")

    try:
        content = state["markdown_content"]
        generated_images = state["generated_images"]
        
        final_content = content
        
        # 替换每个占位符为实际的图片引用
        for img_info in generated_images:
            if img_info["path"]:
                # 生成图片 Markdown 语法
                image_ref = f"""
![{img_info['description']}]({img_info['relative_path']})
"""
                # 替换占位符
                final_content = final_content.replace(img_info["placeholder"], image_ref)
                print(f"   [DEBUG] 已嵌入图片 {img_info['number']}: {img_info['description']}")
            else:
                # 如果图片生成失败，替换为提示信息
                placeholder_text = f"""
> ⚠️ 图片生成失败：{img_info['description']}
"""
                final_content = final_content.replace(img_info["placeholder"], placeholder_text)
                print(f"   [DEBUG] 图片 {img_info['number']} 生成失败，已添加提示")
        
        print(f"✅ 图片整合完成")
        return {"final_content": final_content}
    except Exception as e:
        import traceback
        error_msg = f"整合图片失败: {str(e)}"
        print(f"❌ {error_msg}")
        traceback.print_exc()
        return {"error": error_msg}

# 保存文档到文件的节点
def save_document(state: GraphState) -> GraphState:
    """将生成的Markdown文档（带图片）保存到文件"""
    print("7. 正在保存文档...")

    try:
        import re
        from datetime import datetime

        docs_dir = Config.DOCS_DIR

        if not os.path.exists(docs_dir):
            os.makedirs(docs_dir)
            print(f"   [DEBUG] 创建 docs 目录: {docs_dir}")

        user_prompt = state["user_prompt"]
        print(f"   [DEBUG] 用户提示词: '{user_prompt}'")

        keywords = re.sub(r'[^\w\u4e00-\u9fa5]+', '_', user_prompt)
        keywords = keywords[:20].strip('_')
        print(f"   [DEBUG] 提取的关键词: '{keywords}'")

        if not keywords:
            keywords = "document_with_images"
            print(f"   [DEBUG] 关键词为空，使用默认值: 'document_with_images'")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(docs_dir, f"doc_{keywords}_{timestamp}.md")
        print(f"   [DEBUG] 目标文件名: '{output_path}'")

        content = state["final_content"]
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        file_size = os.path.getsize(output_path)
        print(f"   [DEBUG] ✓ 文档已保存: {output_path} (大小: {file_size} 字节)")

        print(f"✅ 文档保存完成")
        return {"output_path": output_path, "file_size": file_size}
    except Exception as e:
        import traceback
        error_msg = f"保存文档失败: {str(e)}"
        print(f"❌ {error_msg}")
        traceback.print_exc()
        return {"error": error_msg}

# 验证文档的节点
def verify_document(state: GraphState) -> GraphState:
    """验证生成的文档"""
    print("8. 正在验证文档...")

    if state.get("error"):
        print(f"   [DEBUG] 状态中已包含错误，跳过验证: {state['error']}")
        return state

    try:
        output_path = state["output_path"]
        print(f"   [DEBUG] 验证文档路径: '{output_path}'")

        if os.path.exists(output_path):
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()

            lines = content.count('\n') + 1
            words = len(content)
            headers = content.count('#')
            images = content.count('![')

            print(f"   [DEBUG] ✓ 文档验证成功")
            print(f"   [STATS] 行数: {lines}, 字符数: {words}, 标题数: {headers}, 图片数: {images}")

            has_code = '```' in content
            has_list = '- ' in content or '* ' in content or '1. ' in content
            has_bold = '**' in content

            print(f"   [STATS] 包含代码块: {'是' if has_code else '否'}")
            print(f"   [STATS] 包含列表: {'是' if has_list else '否'}")
            print(f"   [STATS] 包含粗体: {'是' if has_bold else '否'}")
            print(f"   [STATS] 包含图片: {'是' if images > 0 else '否'}")

            return state
        else:
            print(f"   [DEBUG] ✗ 文档文件不存在: {output_path}")
            return {"error": "文档文件不存在"}
    except Exception as e:
        import traceback
        error_msg = f"验证文档失败: {str(e)}"
        print(f"❌ {error_msg}")
        traceback.print_exc()
        return {"error": error_msg}

# 创建工作流图
def create_graph():
    """创建并编译工作流图"""
    workflow = StateGraph(GraphState)

    workflow.add_node("refine_prompt", refine_prompt)
    workflow.add_node("generate_outline", generate_outline)
    workflow.add_node("generate_content", generate_content)
    workflow.add_node("identify_image_requests", identify_image_requests)
    workflow.add_node("generate_images", generate_images)
    workflow.add_node("embed_images", embed_images)
    workflow.add_node("save_document", save_document)
    workflow.add_node("verify_document", verify_document)

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

# 主函数
def main():
    """主函数, 处理用户输入并运行工作流"""
    if len(sys.argv) > 1:
        user_prompt = ' '.join(sys.argv[1:])
    else:
        user_prompt = input("请输入你要写的文档主题或需求：")

    print(f"\n{'='*60}")
    print(f"📝 带图片的 Markdown 文档生成智能体")
    print(f"{'='*60}\n")

    try:
        graph = create_graph()

        result = graph.invoke({
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
        })

        print(f"\n{'='*60}")
        if result.get("error"):
            print(f"❌ 错误: {result['error']}")
            print(f"{'='*60}\n")
            sys.exit(1)
        else:
            print(f"✅ 文档生成成功！")
            print(f"📁 保存路径: {result['output_path']}")
            print(f"📏 文件大小: {result['file_size'] / 1024:.2f} KB")
            print(f"📊 生成图片数: {len(result.get('generated_images', []))}")
            print(f"{'='*60}\n")

            abs_path = os.path.abspath(result['output_path'])
            print(f"📍 文档绝对路径: {abs_path}\n")

            try:
                view = input("是否查看文档内容？(y/n): ").strip().lower()
                if view == 'y' or view == 'yes':
                    print(f"\n{'='*60}")
                    print(f"📄 文档内容预览：")
                    print(f"{'='*60}\n")
                    print(result['final_content'][:2000])
                    print(f"\n... (文档已截断，完整内容请查看文件)")
                    print(f"{'='*60}\n")
            except (EOFError, KeyboardInterrupt):
                pass

    except Exception as e:
        import traceback
        print(f"❌ 工作流运行失败: {str(e)}")
        traceback.print_exc()
        print(f"{'='*60}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
