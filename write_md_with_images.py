import os
import sys
import re
from typing import TypedDict, List, Dict
from langgraph.graph import StateGraph, END
from openai import OpenAI
from dotenv import load_dotenv

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
def generate_outline(state: GraphState) -> GraphState:
    """根据润色后的需求生成文档大纲"""
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

        print(f"   [DEBUG] 正在调用 DeepSeek 模型生成大纲...")
        response = client.chat.completions.create(
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
            max_tokens=3000
        )

        outline = response.choices[0].message.content.strip()
        print(f"   [DEBUG] 大纲生成完成，长度: {len(outline)} 字符")

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
def generate_content(state: GraphState) -> GraphState:
    """根据大纲生成完整的Markdown文档内容（包含图片占位符）"""
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

        print(f"   [DEBUG] 正在调用 DeepSeek 模型生成完整文档...")
        response = client.chat.completions.create(
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
            max_tokens=8000
        )

        content = response.choices[0].message.content.strip()
        print(f"   [DEBUG] 文档生成完成，长度: {len(content)} 字符")

        if hasattr(response, 'usage') and response.usage:
            total_tokens = response.usage.total_tokens
            completion_tokens = response.usage.completion_tokens
            print(f"   [DEBUG] Token使用情况 - 总计: {total_tokens}, 生成: {completion_tokens}")

            if completion_tokens >= 7800:
                print(f"   [WARNING] ⚠️ 文档接近token限制，可能被截断！")

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

# 生成所有图片的节点
def generate_images(state: GraphState) -> GraphState:
    """根据图片请求生成所有需要的图片"""
    print("5. 正在生成图表...")

    try:
        image_requests = state["image_requests"]
        generated_images = []
        
        if not image_requests:
            print(f"   [INFO] 没有需要生成的图片")
            return {"generated_images": []}
        
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            return {"error": "未设置 DEEPSEEK_API_KEY，请在 .env 文件中配置"}
        
        # 准备绘图环境（确保在函数内部设置）
        import matplotlib
        # 设置非交互式后端
        if matplotlib.get_backend() != 'Agg':
            matplotlib.use('Agg', force=True)
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches
        
        # 获取脚本目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        images_dir = os.path.join(script_dir, "images")
        if not os.path.exists(images_dir):
            os.makedirs(images_dir)
            print(f"   [DEBUG] 创建 images 目录: {images_dir}")
        
        # 生成每张图片
        for i, req in enumerate(image_requests, 1):
            print(f"   [DEBUG] 正在生成图片 {i}/{len(image_requests)}: {req['description']}")
            
            try:
                # 生成绘图代码
                client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
                
                # 根据描述类型选择不同的提示策略
                is_physics_diagram = any(keyword in req['description'] for keyword in
                    ['力', '受力', '斜面', '支持力', '摩擦力', '重力', '力学', '示意图'])
                is_flowchart = any(keyword in req['description'] for keyword in
                    ['流程图', '架构图', '流程', '步骤', '阶段', '流程：', '展示'])

                if is_flowchart:
                    # 流程图/架构图特殊提示
                    drawing_prompt = f"""请根据以下描述生成 Python 绘图代码，绘制专业的流程图：

描述：{req['description']}

**重要要求（必须严格遵守）**：

1. **绘图方法**：使用 matplotlib.patches 绘制矩形框和箭头
   - 每个步骤用一个矩形框表示：`Rectangle((x, y), width, height, facecolor='lightblue', edgecolor='black', linewidth=2)`
   - 使用 `ax.add_patch()` 添加矩形到图表
   - 使用 `ax.annotate()` 添加箭头连接，格式：`ax.annotate('', xy=(终点x, 终点y), xytext=(起点x, 起点y), arrowprops=dict(arrowstyle='->', lw=2))`
   - 使用 `ax.text()` 在矩形框中心添加文字说明

2. **布局要求（最重要）**：
   - 从上到下或从左到右排列流程步骤
   - 每个步骤之间留足够间距（建议间距1.5-2个单位）
   - 矩形框尺寸统一（建议 width=3, height=1）
   - 整体居中显示，留出适当边距

3. **代码结构（必须遵循）**：
   ```python
   import matplotlib.pyplot as plt
   import matplotlib.patches as patches
   from matplotlib.patches import Rectangle
   import matplotlib
   matplotlib.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'WenQuanYi Micro Hei']

   fig, ax = plt.subplots(figsize=(12, 8))

   # 定义步骤位置（从上到下）
   steps = [
       ('步骤1名称', 4, 7),    # (文字, x中心, y中心)
       ('步骤2名称', 4, 5.5),
       ('步骤3名称', 4, 4),
       # ... 更多步骤
   ]

   # 绘制矩形框和文字
   for text, x, y in steps:
       rect = Rectangle((x-1.5, y-0.5), 3, 1, facecolor='lightblue', edgecolor='black', linewidth=2)
       ax.add_patch(rect)
       ax.text(x, y, text, ha='center', va='center', fontsize=12, fontweight='bold')

   # 绘制箭头连接
   for i in range(len(steps)-1):
       ax.annotate('', xy=(steps[i+1][1], steps[i+1][2]+0.5),
                   xytext=(steps[i][1], steps[i][2]-0.5),
                   arrowprops=dict(arrowstyle='->', lw=2, color='black'))

   ax.set_xlim(0, 8)
   ax.set_ylim(0, 8)
   ax.axis('off')
   plt.tight_layout()
   plt.savefig(target_filename, dpi=150, bbox_inches='tight', facecolor='white')
   plt.close()
   ```

4. **颜色方案**：
   - 矩形框：浅蓝色填充 'lightblue'，黑色边框
   - 箭头：黑色，线宽2
   - 文字：黑色或深灰色，加粗，字号12-14

5. **必须确保**：
   - 每个步骤都有矩形框
   - 步骤之间有箭头连接
   - 文字清晰可读，居中对齐
   - 整体布局美观，不拥挤
   - 不要显示坐标轴（使用 ax.axis('off')）

只返回完整的 Python 代码，不要任何解释。
"""
                elif is_physics_diagram:
                    drawing_prompt = f"""请根据以下描述生成 Python 绘图代码：

描述：{req['description']}

要求：
1. 使用 matplotlib 绘图
2. **物理规律要求（非常重要）**：
   - 支持力（法向力）方向必须**垂直于斜面表面**
   - 重力方向必须**竖直向下**
   - 摩擦力方向必须**平行于斜面**
   - 确保所有箭头角度准确反映物理规律
3. 添加适当的标题、坐标轴标签、图例
4. 使用清晰的配色方案（建议：重力用红色，支持力用绿色，摩擦力用蓝色）
5. 图表要专业、美观、易于理解
6. 只返回可执行的 Python 代码，不要任何解释
7. 确保中文正常显示
8. 图表尺寸合适，不拥挤
9. 必须使用 plt.savefig(target_filename, dpi=150, bbox_inches='tight') 保存图片
10. 不要调用 plt.show()
"""
                else:
                    drawing_prompt = f"""请根据以下描述生成 Python 绘图代码：

描述：{req['description']}

要求：
1. 使用 matplotlib 绘图
2. 添加适当的标题、坐标轴标签、图例
3. 使用清晰的配色方案
4. 图表要专业、美观、易于理解
5. 只返回可执行的 Python 代码，不要任何解释
6. 确保中文正常显示
7. 图表尺寸合适，不拥挤
8. 必须使用 plt.savefig(target_filename, dpi=150, bbox_inches='tight') 保存图片
9. 不要调用 plt.show()
"""
                
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {
                            "role": "system",
                            "content": """你是一个专业的数据可视化和绘图专家。请根据用户需求生成高质量的 Python 绘图代码。

技术要求：
1. 只使用 matplotlib 库（可配合 numpy）
2. 代码必须完整可执行
3. 设置中文字体支持：matplotlib.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'WenQuanYi Micro Hei']
4. 图片保存使用变量 target_filename
5. 不要生成被截断的代码
6. 确保所有括号都闭合
7. 重要：不要使用 plt.show()，直接使用 plt.savefig() 保存图片

绘图规范：
- 使用清晰的配色方案
- 添加适当的标题和标签
- 使用图例说明
- 线条粗细有层次
- 布局合理，使用 tight_layout()

**物理示意图特殊要求（重要）**：
如果用户需求涉及受力分析、力学示意图等：
- **支持力（法向力）方向必须垂直于接触面**
- **重力方向必须竖直向下**
- **摩擦力方向必须平行于接触面**
- 使用角度计算确保箭头方向准确（如使用 numpy 的三角函数）
- 斜面角度 θ 与力的方向关系：
  * 重力：竖直向下（-90°）
  * 支持力：垂直于斜面向上（θ - 90°）
  * 摩擦力：沿斜面向上或向下（θ 或 θ + 180°）

**流程图/架构图特殊要求（重要）**：
如果用户需求涉及流程图、架构图、步骤说明等：
- **必须使用 matplotlib.patches.Rectangle 绘制矩形框**
- **每个步骤用一个矩形框表示**，不要只用文字
- **使用 ax.annotate() 添加箭头连接**步骤
- **矩形框必须有填充色**（如 facecolor='lightblue'）和边框
- **步骤文字必须在矩形框内部**，使用 ax.text() 居中显示
- **必须隐藏坐标轴**：使用 ax.axis('off')
- **布局必须清晰**：从上到下或从左到右，步骤间距足够
- 示例结构：
  ```python
  # 定义步骤位置
  steps = [('步骤1', 4, 7), ('步骤2', 4, 5.5), ...]
  # 绘制矩形和文字
  for text, x, y in steps:
      rect = Rectangle((x-1.5, y-0.5), 3, 1, facecolor='lightblue', edgecolor='black', linewidth=2)
      ax.add_patch(rect)
      ax.text(x, y, text, ha='center', va='center', fontsize=12)
  # 绘制箭头
  for i in range(len(steps)-1):
      ax.annotate('', xy=(...), xytext=(...), arrowprops=dict(arrowstyle='->', lw=2))
  ```

只返回 Python 代码，不要任何解释。"""
                        },
                        {
                            "role": "user",
                            "content": drawing_prompt
                        }
                    ],
                    temperature=0.3,
                    max_tokens=3000
                )
                
                generated_code = response.choices[0].message.content.strip()
                
                # 去除 markdown 标记
                if generated_code.startswith('```python'):
                    generated_code = generated_code[10:-3].strip()
                elif generated_code.startswith('```'):
                    generated_code = generated_code[3:-3].strip()
                
                # 移除 plt.show() 调用（非交互式环境不支持）
                import re
                generated_code = re.sub(r'plt\.show\(\)', '# plt.show()  # 已禁用（非交互式环境）', generated_code)
                generated_code = re.sub(r'plt\.show\(\s*\)', '# plt.show()  # 已禁用（非交互式环境）', generated_code)
                
                # 添加调试日志
                print(f"   [DEBUG] 生成的代码长度: {len(generated_code)} 字符")
                if len(generated_code) < 500:
                    print(f"   [DEBUG] 生成代码: {generated_code}")
                
                # 生成文件名
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_description = re.sub(r'[^\w\u4e00-\u9fa5]', '_', req['description'][:20])
                target_filename = os.path.join(images_dir, f"plot_{safe_description}_{timestamp}.png")
                
                # 执行代码生成图片（每个图片使用独立的图形）
                local_vars = {
                    'plt': plt,
                    'matplotlib': matplotlib,
                    'patches': patches,
                    'np': __import__('numpy'),
                    'os': os,
                    'target_filename': target_filename
                }

                # 先编译代码检查语法
                compile(generated_code, '<string>', 'exec')

                # 清理 matplotlib 状态（在执行前）
                plt.close('all')

                # 保存原始工作目录并切换到 images 目录
                # 这样即使 AI 生成的代码使用相对路径，文件也会保存到正确的位置
                original_cwd = os.getcwd()
                os.chdir(images_dir)
                print(f"   [DEBUG] 临时切换工作目录到: {images_dir}")

                try:
                    # 执行代码
                    exec(generated_code, globals(), local_vars)

                    # 确保图片被保存（如果 AI 的代码没有调用 savefig，这里强制调用）
                    try:
                        # 使用相对路径文件名，因为当前目录已经是 images_dir
                        relative_filename = os.path.basename(target_filename)
                        plt.savefig(relative_filename, dpi=150, bbox_inches='tight', facecolor='white')
                        print(f"   [DEBUG] 强制保存图片到: {relative_filename}")
                    except Exception as save_error:
                        print(f"   [DEBUG] 强制保存失败: {str(save_error)}")
                finally:
                    # 恢复原始工作目录
                    os.chdir(original_cwd)
                    print(f"   [DEBUG] 恢复工作目录到: {original_cwd}")

                # 强制关闭所有图形，确保文件已写入
                plt.close('all')
                
                # 验证图片生成
                if os.path.exists(target_filename):
                    file_size = os.path.getsize(target_filename)
                    # 计算相对于 docs 目录的路径
                    relative_path = f"../images/{os.path.basename(target_filename)}"
                    
                    generated_images.append({
                        "number": req['number'],
                        "description": req['description'],
                        "placeholder": req['placeholder'],
                        "path": target_filename,
                        "relative_path": relative_path,
                        "size": file_size
                    })
                    print(f"   [DEBUG] ✓ 图片 {i} 生成成功: {os.path.basename(target_filename)} (大小: {file_size} 字节)")
                else:
                    print(f"   [DEBUG] ✗ 图片 {i} 生成失败: 文件未创建")
                    print(f"   [DEBUG] 目标路径: {target_filename}")
                    print(f"   [DEBUG] 生成的代码:")
                    print("-" * 80)
                    print(generated_code)
                    print("-" * 80)
                    # 即使图片生成失败，也记录以便后续处理
                    generated_images.append({
                        "number": req['number'],
                        "description": req['description'],
                        "placeholder": req['placeholder'],
                        "path": None,
                        "relative_path": None,
                        "size": 0
                    })
                    
            except Exception as e:
                print(f"   [DEBUG] ✗ 图片 {i} 生成失败: {str(e)}")
                import traceback
                traceback.print_exc()
                print(f"   [DEBUG] 生成的代码:")
                print("-" * 80)
                print(generated_code)
                print("-" * 80)
                generated_images.append({
                    "number": req['number'],
                    "description": req['description'],
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

        script_dir = os.path.dirname(os.path.abspath(__file__))
        docs_dir = os.path.join(script_dir, "docs")

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
