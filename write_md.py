import os
import sys
from typing import TypedDict
from langgraph.graph import StateGraph, END
from openai import OpenAI
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

# 定义状态结构
class GraphState(TypedDict):
    user_prompt: str        # 用户输入的主题或需求
    refined_prompt: str     # AI润色后的写作提示词
    document_outline: str   # 文档大纲
    markdown_content: str   # 生成的Markdown文档内容
    output_path: str        # 输出文件路径
    file_size: int          # 文件大小
    error: str              # 错误信息

# 润色写作需求的节点
def refine_prompt(state: GraphState) -> GraphState:
    """使用AI润色用户的写作需求，使其更适合生成高质量的文档"""
    print("1. 正在润色写作需求...")
    user_prompt = state["user_prompt"]

    try:
        print(f"✅ 原始需求: '{user_prompt}'")

        # 手动增强提示词，添加必要的文档写作要求
        enhanced_prompt = f"""{user_prompt}

## 文档写作要求

### 基本要求
1. 使用标准的 Markdown 语法
2. 文档结构清晰，层次分明
3. 内容准确、详实、有深度
4. 语言简洁、专业、易懂
5. 适当地使用标题、列表、代码块、表格等格式
6. 包含必要的示例和说明

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
5. **向量与物理量**：
   - 向量：`\\vec{{v}}` 或 `\\mathbf{{v}}`
   - 物理量常量：使用标准符号如 `\\mu_B`, `\\hbar`, `\\omega`, `\\nu`
6. **测试兼容性**：生成公式后，确认所有命令都是 KaTeX 支持的标准命令

### 文档结构规范
- **标题层级**：使用 # ## ### #### 等标记标题层级
- **段落组织**：段落之间空一行，提高可读性
- **列表使用**：
  - 无序列表使用 - 或 *
  - 有序列表使用 1. 2. 3.
  - 列表项适当缩进
- **代码块**：使用 ```语言名称 ... ``` 包裹代码
- **强调**：使用 **粗体** 或 *斜体* 强调重点
- **链接和图片**：使用正确的 Markdown 语法

### 内容质量要求
1. **准确性**：信息准确无误，术语使用正确
2. **完整性**：覆盖主题的主要方面，不遗漏重要内容
3. **可读性**：逻辑清晰，条理分明，易于理解
4. **实用性**：提供有价值的知识和实用的信息
5. **专业性**：使用专业术语，保持专业态度

### 特殊类型文档要求
- **技术文档**：包含代码示例、API说明、使用指南
- **教程类**：步骤清晰，循序渐进，配以示例
- **说明文档**：全面覆盖功能点，使用场景明确
- **总结类**：提炼要点，结构清晰，便于快速浏览"""

        print(f"✅ 增强后的提示词已生成")
        return {"refined_prompt": enhanced_prompt}
    except Exception as e:
        error_msg = f"润色提示词失败: {str(e)}"
        print(f"❌ {error_msg}")
        # 如果增强失败，直接使用原始提示词继续流程
        return {"refined_prompt": user_prompt}

# 生成文档大纲的节点
def generate_outline(state: GraphState) -> GraphState:
    """根据润色后的需求生成文档大纲"""
    print("2. 正在生成文档大纲...")
    user_prompt = state["refined_prompt"]

    try:
        # 初始化DeepSeek客户端
        api_key = os.getenv("DEEPSEEK_API_KEY")
        print(f"   [DEBUG] API Key 状态: {'已设置' if api_key else '未设置'}")

        if not api_key:
            return {"error": "未设置 DEEPSEEK_API_KEY，请在 .env 文件中配置"}

        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )

        # 调用DeepSeek模型生成大纲
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
5. 只返回大纲内容，不要有其他解释性文字

示例格式：
# 主标题

## 第一部分：简介
- 背景介绍
- 核心概念

## 第二部分：核心内容
### 2.1 概念一
- 详细说明
- 示例

### 2.2 概念二
- 详细说明
- 示例
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
4. 只返回大纲内容，使用Markdown格式"""
                }
            ],
            temperature=0.5,
            max_tokens=3000
        )

        # 提取生成的大纲
        outline = response.choices[0].message.content.strip()
        print(f"   [DEBUG] 大纲生成完成，长度: {len(outline)} 字符")

        # 去除可能的markdown格式
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
        # 如果大纲生成失败，创建一个默认大纲
        default_outline = f"# {state['user_prompt']}\n\n## 简介\n- 背景介绍\n\n## 主要内容\n- 核心概念\n- 详细说明\n\n## 总结\n- 要点总结\n"
        print(f"   [INFO] 使用默认大纲")
        return {"document_outline": default_outline}

# 生成Markdown文档内容的节点
def generate_content(state: GraphState) -> GraphState:
    """根据大纲生成完整的Markdown文档内容"""
    print("3. 正在生成文档内容...")

    try:
        # 初始化DeepSeek客户端
        api_key = os.getenv("DEEPSEEK_API_KEY")

        if not api_key:
            return {"error": "未设置 DEEPSEEK_API_KEY，请在 .env 文件中配置"}

        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )

        # 获取大纲
        outline = state["document_outline"]
        user_prompt = state["refined_prompt"]

        # 调用DeepSeek模型生成完整文档
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

### 2. 内容组织原则
- **结构清晰**：按照大纲结构展开内容
- **段落分明**：段落之间空一行
- **逻辑连贯**：内容前后呼应，逻辑流畅
- **重点突出**：适当使用粗体、列表等方式突出重点

### 3. 内容质量要求
- **准确性**：信息准确，术语使用正确
- **完整性**：覆盖大纲中的所有要点
- **可读性**：语言简洁易懂，避免冗长
- **实用性**：提供有价值的知识和示例
- **专业性**：保持专业语气，使用恰当的术语

### 4. 数学公式要求（重要）
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
   - 上下标：`x^2`, `x_1`, `x^{2n}`, `x_{i,j}`
   - 分数：`\\frac{a}{b}`
   - 根号：`\\sqrt{x}`, `\\sqrt[n]{x}`
   - 求和与积分：`\\sum`, `\\int`, `\\prod`, `\\lim`
   - 矩阵与括号：`\\begin{matrix} ... \\end{matrix}`, `\\left( \\right)`, `\\left[ \\right]`
5. **向量与物理量**：
   - 向量：`\\vec{v}` 或 `\\mathbf{v}`
   - 物理量常量：使用标准符号如 `\\mu_B`, `\\hbar`, `\\omega`, `\\nu`
6. **测试兼容性**：生成公式后，确认所有命令都是 KaTeX 支持的标准命令

### 5. 特殊格式要求
- **代码示例**：
  ```python
  def example():
      print("Hello, World!")
  ```
- **注意事项**：使用 > 引用格式
- **提示信息**：使用 💡 ⚠️ ✅ ❌ 等emoji增强可读性

### 6. 输出要求
- 只返回 Markdown 格式的文档内容
- 不要包含任何解释性文字或meta信息
- 确保每个标题、段落、列表格式正确
- 代码块语法高亮标记正确

请根据提供的大纲，生成完整、专业、高质量的 Markdown 文档。"""
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
2. 每个章节都要有详实的内容
3. 使用正确的 Markdown 语法
4. 内容准确、专业、易懂
5. 包含适当的示例和说明
6. 只返回文档内容，不要有其他解释

请开始生成完整文档："""
                }
            ],
            temperature=0.4,
            max_tokens=8000
        )

        # 提取生成的文档内容
        content = response.choices[0].message.content.strip()
        print(f"   [DEBUG] 文档生成完成，长度: {len(content)} 字符")

        # 检查token使用情况
        if hasattr(response, 'usage') and response.usage:
            total_tokens = response.usage.total_tokens
            completion_tokens = response.usage.completion_tokens
            print(f"   [DEBUG] Token使用情况 - 总计: {total_tokens}, 生成: {completion_tokens}")

            # 检查是否接近限制
            if completion_tokens >= 7800:  # 8000的97.5%
                print(f"   [WARNING] ⚠️ 文档接近token限制，可能被截断！")

        # 去除可能的markdown格式
        if content.startswith('```markdown'):
            content = content[12:-3].strip()
        elif content.startswith('```'):
            content = content[3:-3].strip()

        # 修复双反斜杠问题:将数学公式中错误的双反斜杠替换为单反斜杠
        # AI 可能会从提示词中复制 \\ 到生成的文档,但 LaTeX 只需要单反斜杠
        # 注意:LaTeX 中的换行符用 \\,所以我们需要小心处理

        import re

        def fix_latex_backslashes(text):
            """修复 LaTeX 中的反斜杠"""
            # 策略:将 \\后跟字母 的模式替换为 \后跟字母
            # 但保留 LaTeX 中的换行符 \\ (后面不是字母)

            # 使用正则表达式:匹配 \\ 后跟小写字母,但排除后面还有字母的情况
            # 这样可以保留 \\\\ 但修复 \\alpha 为 \alpha

            # 更简单的方法:直接将所有 \\字母 替换为 \字母
            # 因为 LaTeX 命令格式就是 \命令名

            # 第一步:保护真正的双反斜杠换行符(临时替换)
            text = text.replace('\\\\\n', '___NEWLINE___')

            # 第二步:将所有 \\+字母 替换为 \+字母
            text = re.sub(r'\\\\([a-zA-Z]+)', r'\\\1', text)

            # 第三步:恢复换行符
            text = text.replace('___NEWLINE___', '\\\\\n')

            return text

        content = fix_latex_backslashes(content)

        print(f"✅ Markdown 文档内容生成完成")
        return {"markdown_content": content}
    except Exception as e:
        import traceback
        error_msg = f"生成文档内容失败: {str(e)}"

        # 检查是否是 API 错误
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

# 保存文档到文件的节点
def save_document(state: GraphState) -> GraphState:
    """将生成的Markdown文档保存到文件"""
    print("4. 正在保存文档...")

    try:
        import re
        from datetime import datetime

        # 获取脚本所在目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        docs_dir = os.path.join(script_dir, "docs")

        # 确保 docs 目录存在
        if not os.path.exists(docs_dir):
            os.makedirs(docs_dir)
            print(f"   [DEBUG] 创建 docs 目录: {docs_dir}")

        # 从用户提示词中提取关键词作为文件名
        user_prompt = state["user_prompt"]
        print(f"   [DEBUG] 用户提示词: '{user_prompt}'")

        # 去除特殊字符，只保留中文、英文、数字
        keywords = re.sub(r'[^\w\u4e00-\u9fa5]+', '_', user_prompt)
        # 截取前20个字符作为关键词
        keywords = keywords[:20].strip('_')
        print(f"   [DEBUG] 提取的关键词: '{keywords}'")

        # 如果关键词为空，使用默认值
        if not keywords:
            keywords = "document"
            print(f"   [DEBUG] 关键词为空，使用默认值: 'document'")

        # 生成唯一文件名：关键词_时间戳.md
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(docs_dir, f"doc_{keywords}_{timestamp}.md")
        print(f"   [DEBUG] 目标文件名: '{output_path}'")

        # 写入文件
        content = state["markdown_content"]
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # 获取文件大小
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
    print("5. 正在验证文档...")

    if state.get("error"):
        print(f"   [DEBUG] 状态中已包含错误，跳过验证: {state['error']}")
        return state

    try:
        output_path = state["output_path"]
        print(f"   [DEBUG] 验证文档路径: '{output_path}'")

        if os.path.exists(output_path):
            # 读取文件内容进行基本验证
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 统计基本信息
            lines = content.count('\n') + 1
            words = len(content)
            headers = content.count('#')

            print(f"   [DEBUG] ✓ 文档验证成功")
            print(f"   [STATS] 行数: {lines}, 字符数: {words}, 标题数: {headers}")

            # 检查是否包含基本Markdown元素
            has_code = '```' in content
            has_list = '- ' in content or '* ' in content or '1. ' in content
            has_bold = '**' in content

            print(f"   [STATS] 包含代码块: {'是' if has_code else '否'}")
            print(f"   [STATS] 包含列表: {'是' if has_list else '否'}")
            print(f"   [STATS] 包含粗体: {'是' if has_bold else '否'}")

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
    # 初始化StateGraph，传入状态类型
    workflow = StateGraph(GraphState)

    # 添加节点
    workflow.add_node("refine_prompt", refine_prompt)
    workflow.add_node("generate_outline", generate_outline)
    workflow.add_node("generate_content", generate_content)
    workflow.add_node("save_document", save_document)
    workflow.add_node("verify_document", verify_document)

    # 设置入口点
    workflow.set_entry_point("refine_prompt")

    # 添加边（按顺序执行）
    workflow.add_edge("refine_prompt", "generate_outline")
    workflow.add_edge("generate_outline", "generate_content")
    workflow.add_edge("generate_content", "save_document")
    workflow.add_edge("save_document", "verify_document")
    workflow.add_edge("verify_document", END)

    # 编译图
    return workflow.compile()

# 主函数
def main():
    """主函数, 处理用户输入并运行工作流"""
    # 获取用户输入
    if len(sys.argv) > 1:
        user_prompt = ' '.join(sys.argv[1:])
    else:
        user_prompt = input("请输入你要写的文档主题或需求：")

    print(f"\n{'='*60}")
    print(f"📝 Markdown 文档生成智能体")
    print(f"{'='*60}\n")

    try:
        # 创建工作流
        graph = create_graph()

        # 运行工作流
        result = graph.invoke({
            "user_prompt": user_prompt,
            "refined_prompt": "",
            "document_outline": "",
            "markdown_content": "",
            "output_path": "",
            "file_size": 0,
            "error": ""
        })

        # 输出结果
        print(f"\n{'='*60}")
        if result.get("error"):
            print(f"❌ 错误: {result['error']}")
            print(f"{'='*60}\n")
            sys.exit(1)
        else:
            print(f"✅ 文档生成成功！")
            print(f"📁 保存路径: {result['output_path']}")
            print(f"📏 文件大小: {result['file_size'] / 1024:.2f} KB")
            print(f"{'='*60}\n")

            # 显示文档绝对路径
            abs_path = os.path.abspath(result['output_path'])
            print(f"📍 文档绝对路径: {abs_path}\n")

            # 询问是否查看文档内容
            try:
                view = input("是否查看文档内容？(y/n): ").strip().lower()
                if view == 'y' or view == 'yes':
                    print(f"\n{'='*60}")
                    print(f"📄 文档内容预览：")
                    print(f"{'='*60}\n")
                    print(result['markdown_content'])
                    print(f"\n{'='*60}\n")
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
