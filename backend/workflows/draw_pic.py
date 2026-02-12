import os
import matplotlib.pyplot as plt
import sys
from typing import TypedDict
from langgraph.graph import StateGraph, END
from openai import OpenAI
from dotenv import load_dotenv
from config import Config

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

# 润色绘图需求的节点
def refine_prompt(state: GraphState) -> GraphState:
    """使用AI润色用户的绘图需求，使其更适合生成高质量的绘图代码"""
    print("1. 正在润色绘图需求...")
    user_prompt = state["user_prompt"]
    
    try:
        # 直接使用原始提示词进行增强，不调用AI模型
        # 这种方式更可靠，避免了AI模型返回空内容的问题
        print(f"✅ 原始需求: '{user_prompt}'")
        
        # 手动增强提示词，添加必要的绘图要求
        enhanced_prompt = rf"""{user_prompt}

## 核心绘图要求（必须严格遵守）

 ### 通用基本要求
1. 使用matplotlib库绘制，配合numpy等基础库
2. **确保中文正常显示**（最重要）：
    ```python
    import matplotlib
    # 设置中文字体,优先使用macOS系统字体
    matplotlib.rcParams['font.sans-serif'] = [
        'STHeiti',           # 华文黑体(系统自带,推荐)
        'Heiti TC',          # 黑体-繁
        'Heiti SC',          # 黑体-简
        'Hiragino Sans GB',  # 冬青黑体
        'PingFang SC',       # 苹方-简
        'Arial Unicode MS',  # Arial Unicode(备选)
        'SimHei',            # 黑体(Windows/Linux)
        'STSong',            # 华文宋体
        'Songti SC',         # 宋体-简
        'WenQuanYi Micro Hei'
    ]
    matplotlib.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
    ```
3. **原始字符串（r前缀）是生死攸关的要求**：
   ```python
   # ❌ 错误：普通字符串中的反斜杠会被当作转义字符
   '以概率 $|\alpha|^2$ 坍缩到 $|0\rangle$'  # \a和\b是转义序列，会导致错误

   # ✅ 正确：使用原始字符串（r前缀）
   r'以概率 $|\alpha|^2$ 坍缩到 $|0\rangle$'  # 反斜杠被正确保留

   # ❌ 错误示例
   ax.text(x, y, '$|\alpha|^2$')      # \a会被转义
   ax.annotate(r'标签 $x_i$', ...)   # 混用，有r前缀但部分字符串没有

   # ✅ 正确示例 - 所有包含LaTeX的字符串都必须有r前缀
   ax.text(x, y, r'$|\alpha|^2$')
   ax.annotate(r'标签 $x_i$', ...)
   plt.title(r'函数 $f(x) = x^2$')
   ax.set_xlabel(r'角度 $\theta$ (rad)')
   ```
   **核心规则**：
   - 只要字符串中包含 `$` 符号（LaTeX公式），就必须在字符串引号前加 `r`
   - 不要使用普通字符串 `'...'`，必须使用原始字符串 `r'...'`
   - 包括但不限于：`ax.text()`, `ax.annotate()`, `plt.title()`, `ax.set_xlabel()`, `ax.set_ylabel()`, `ax.legend()`

4. **数学符号必须使用LaTeX格式**：
   - 希腊字母：`r'$\alpha$'`（α）、`r'$\beta$'`（β）、`r'$\gamma$'`（γ）、`r'$\pi$'`（π）、`r'$\theta$'`（θ）
   - **量子态符号**（必须用LaTeX）：
     * `|0⟩` → `r'$|0\\rangle$'` 或 `r'$\\langle 0|$'`
     * `|1⟩` → `r'$|1\\rangle$'`
     * `|ψ⟩` → `r'$|\\psi\\rangle$'` 或 `r'$\\langle\\psi|$'`
     * 示例：`ax.annotate(r'测量坍缩 → $|0\\rangle$', ...)`
   - **上下标必须使用LaTeX格式**（生死攸关，绝对不能违反！）：
     * **致命错误**：绝不能使用Unicode下标字符（如 ₁₂₃₄₅₆₇₈₉₀ₐₑᵢₒᵤᵩ 等）
     * **错误示例**（会导致显示异常）：
       ```python
       # ❌ 绝对禁止 - Unicode下标字符
       lagrange_points = [(L1_x, 0, 'L₁', 'red'), (L2_x, 0, 'L₂', 'orange')]
       ax.text(x, y, 'xₙ')              # 直接使用Unicode下标
       ax.set_xlabel('位置 xᵢ')         # 直接使用Unicode下标
       ```
     * **正确示例**（必须遵循）：
       ```python
       # ✅ 正确 - 使用LaTeX下标格式
       lagrange_points = [(L1_x, 0, r'$L_1$', 'red'), (L2_x, 0, r'$L_2$', 'orange')]
       ax.text(x, y, r'$x_n$')                    # LaTeX格式下标
       ax.set_xlabel(r'位置 $x_i$')               # LaTeX格式下标
       ax.plot(x, y, label=r'曲线 $f_{max}(x)$')  # LaTeX格式下标
       ```
     * 上标格式：`$x^2$`、`$x^n$`、`$a^{b+c}$`  # type: ignore
     * 下标格式：`$x_1$`、`$x_n$`、`$L_{max}$`
     * 分数格式：`$\frac{{a}}{{b}}$`
   - 特殊数学符号：`r'$\infty$'`（∞）、`r'$\pm$'`（±）、`r'$\times$'`（×）
   - **禁止使用特殊Unicode符号**（生死攸关，绝对不能违反！）：
     * **致命错误**：绝不能直接使用matplotlib无法显示的Unicode符号
     * **常见问题符号**：
       - `•` (项目符号，U+2022) → 无法显示，会导致显示为方块或乱码
       - `→` (箭头，U+2192) → 无法显示，应使用LaTeX的 `$\rightarrow$` 或 `$\to$`
       - `°` (度数符号，U+00B0) → 无法显示，应使用LaTeX的 `$^\circ$`
       - `±` (正负号，U+00B1) → 无法显示，应使用LaTeX的 `$\pm$`
       - `×` (乘号，U+00D7) → 无法显示，应使用LaTeX的 `$\times$`
       - `÷` (除号，U+00F7) → 无法显示，应使用LaTeX的 `$\div$`
       - `≤` (小于等于，U+2264) → 无法显示，应使用LaTeX的 `$\le$`
       - `≥` (大于等于，U+2265) → 无法显示，应使用LaTeX的 `$\ge$`
     * **错误示例**（会导致显示异常）：
       ```python
       # ❌ 绝对禁止 - 直接使用Unicode特殊符号
       ax.text(x, y, '要点一 • 要点二 • 要点三')  # • 无法显示
       ax.annotate('A → B', ...)                # → 无法显示
       ax.set_title('温度变化 ± 5°C')            # ± 和 ° 无法显示
       plt.xlabel('长度 ≥ 0')                    # ≥ 无法显示
       ```
     * **正确示例**（必须遵循）：
       ```python
       # ✅ 正确 - 使用LaTeX格式
       ax.text(x, y, r'要点一 $\cdot$ 要点二 $\cdot$ 要点三')  # 使用 \cdot
       ax.annotate(r'A $\rightarrow$ B', ...)                        # 使用 \rightarrow
       ax.set_title(r'温度变化 $\pm$ 5$^\circ$C')               # 使用 \pm 和 ^\circ
       plt.xlabel(r'长度 $\ge$ 0')                               # 使用 \ge
       ```
     * **LaTeX替代方案对照表**：
       | Unicode | LaTeX | 说明 |
       |---------|-------|------|
       | `•` | `$\cdot$` 或 `$\bullet$` | 项目符号/乘点 |
       | `→` | `$\rightarrow$` 或 `$\to$` | 箭头 |
       | `←` | `$\leftarrow$` 或 `$\gets$` | 左箭头 |
       | `↔` | `$\leftrightarrow$` | 双向箭头 |
       | `°` | `$^\circ$` | 度数 |
       | `±` | `$\pm$` | 正负号 |
       | `×` | `$\times$` | 乘号 |
       | `÷` | `$\div$` | 除号 |
       | `≤` | `$\le$` | 小于等于 |
       | `≥` | `$\ge$` | 大于等于 |
       | `≠` | `$\neq$` | 不等于 |
       | `∞` | `$\infty$` | 无穷 |
       | `√` | `$\sqrt{x}$` | 根号 |  # type: ignore
   - 负号、减号使用matplotlib设置：`matplotlib.rcParams['axes.unicode_minus'] = False`
4. 添加适当的标题、坐标轴标签、图例
5. 使用清晰的配色方案（推荐：蓝色、红色、绿色、橙色、紫色）
6. 设置合理的图形尺寸(figsize=(10, 8))和dpi=100
7. **防止图示和文本遮挡的布局优化**（重要）：
   - 必须使用 `plt.tight_layout()` 或 `plt.subplots_adjust()` 自动调整布局
   - 保存图片时使用 `bbox_inches='tight'` 避免元素被裁剪
   - 标注文字必须与图形主体保持适当距离，避免重叠
   - 使用 `bbox=dict(boxstyle='round', facecolor='white', alpha=0.8)` 为文字添加半透明背景
   - 精确调整文字位置，使用 `xytext` 参数控制标注位置
   - 当多个标注可能重叠时，手动调整坐标，使用不同的偏移量
8. 确保代码可以直接执行，无语法错误

### 数据可视化类图形（曲线图、折线图等）特定要求
8. **数据点生成**（最重要）：
   - 使用numpy生成密集的数据点：`x = np.linspace(起始值, 结束值, 1000)`
   - 确保x轴范围足够覆盖所需区域（如0到π、0到2等）
   - 计算y值时使用明确的数学公式，不要使用未定义的变量
   - 示例：`y = np.sin(x)` 或 `y = (1 - (t/t_c)**8)**0.125`

9. **曲线绘制**（必须严格遵守）：
   - **致命错误警告**：绝不能在 `color` 参数中使用格式字符串（如 'k--', 'b-', 'r--' 等）
   - **错误示例**（会导致执行失败）：
     ```python
     # ❌ 绝对禁止
     ax.plot(x, y, color='k--', linewidth=2)  # 错误！'k--'不是有效的颜色值
     ax.plot(x, y, color='b-', linewidth=2)   # 错误！'b-'不是有效的颜色值
     ```
   - **正确做法**（二选一）：
     ```python
     # ✅ 方案1：使用分离的 color 和 linestyle 参数（推荐）
     ax.plot(x, y, color='black', linestyle='--', linewidth=2, label='曲线名称')
     ax.plot(x, y, color='blue', linestyle='-', linewidth=2, label='曲线名称')

     # ✅ 方案2：使用格式字符串作为位置参数（第三参数）
     ax.plot(x, y, 'k--', linewidth=2, label='曲线名称')
     ax.plot(x, y, 'b-', linewidth=2, label='曲线名称')
     ```
   - **参数使用规则**：
     * 格式字符串（如 'k--', 'b-', 'r:'）只能作为位置参数（第三参数），不能放在 `color=` 中
     * 使用关键字参数时，必须分别指定 `color='颜色名'` 和 `linestyle='线型'`
     * 常用颜色：`'black'`, `'blue'`, `'red'`, `'green'`, `'orange'`, `'purple'`
     * 常用线型：`'-'` 实线, `'--'` 虚线, `':'` 点线, `'-.'` 点划线
   - 线条宽度设为2-3，颜色醒目
   - 确保曲线在图形范围内清晰可见

10. **坐标轴设置**：
    - 设置合理的x轴和y轴范围（使用ax.set_xlim和ax.set_ylim）
    - 添加网格线：`plt.grid(True, alpha=0.3)`辅助读数
    - 添加坐标轴标签和标题，使用中文标注

11. **特殊标注**（如需要）：
    - 标注关键点（极值、零点、交点、临界点等）
    - 添加文字注释说明特殊点或区域
    - 对于能隙、相变点等重要位置，使用箭头或虚线标注

 12. **代码完整性**（生死攸关）：
     - 所有变量必须在代码中显式定义或生成
     - 不要使用任何未定义的变量（如data、result等）
     - 确保所有函数调用都完整，特别是括号闭合
     - 数据必须完整，不能有undefined values

  13. **物理规律正确性**：
      - 曲线形状必须符合物理规律（如能谱的连续性、磁化强度在临界点的平滑变化等）
      - 数学公式必须正确（如二维Ising模型的临界指数β=1/8）
      - 数据范围和比例关系必须合理

  14. **单摆/摆动系统角度标注**（必须严格遵守）：
      - **角度顶点定位**：角度θ的顶点必须在支点/转轴处，绝不能标注在摆球或其他运动物体上
      - **参考线绘制**：必须绘制垂直向下的虚线作为角度参考线（从支点垂直向下延伸）
      - **角度弧线绘制**：使用Arc绘制角度弧线，弧的圆心必须在支点坐标
      - **角度计算**：对于单摆，从垂直向下方向（270度）开始，到摆线方向（270+θ度）
      - **弧线参数**：theta1和theta2必须是角度值（0-360度），不是弧度
      - **标签位置**：角度标签放置在弧线中点附近，确保清晰可见

  15. **刚体约束条件和物理真实性**（必须严格遵守）：
     - **接触面约束**：物体（如小车、滑块）必须完全贴合接触面，不能有穿模或间隙
     - **斜面约束**：斜面上的物体底部必须与斜面线精确重合，使用三角函数计算坐标
     - **刚体完整性**：物体内部不能有任何线条穿模，所有几何关系必须精确计算
     - **轮子约束**：轮子必须接触地面或斜面，轮心到接触面的距离等于半径
     - **运动连续性**：如果展示运动状态，轨迹必须连续且平滑
     - **角度精确性**：所有角度必须与标注一致，不能有视觉上的偏差
     - **比例一致性**：同类物体的大小比例必须合理，符合物理直觉
     - **重力方向**：重力必须严格垂直向下，不能有偏差
     - **力系平衡**：静止物体的受力分析必须满足平衡条件

### 重要提醒
- 如果绘制曲线图，必须使用numpy生成足够多的数据点（至少1000个）
- 必须显式设置坐标轴范围，确保曲线完整显示在图形中
- 曲线的数学关系必须准确，不能凭空捏造数据
- 对于物理系统的曲线，必须遵循已知的理论公式或规律"""
        print(f"✅ 增强后的提示词: '{enhanced_prompt}'")
        
        return {"refined_prompt": enhanced_prompt}
    except Exception as e:
        error_msg = f"润色提示词失败: {str(e)}"
        print(f"❌ {error_msg}")
        # 如果增强失败，直接使用原始提示词继续流程
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
        # 初始化DeepSeek客户端（兼容OpenAI API）
        api_key = os.getenv("DEEPSEEK_API_KEY")
        print(f"   [DEBUG] API Key 状态: {'已设置' if api_key else '未设置'}")

        if not api_key:
            return {"error": "未设置 DEEPSEEK_API_KEY，请在 .env 文件中配置"}

        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )

        # 调用DeepSeek模型生成代码（使用流式API）
        print(f"   [DEBUG] 正在调用 DeepSeek 模型（流式模式）...")
        
        # 使用流式API调用
        stream = client.chat.completions.create(
            model="deepseek-chat",  # 使用DeepSeek的聊天模型
            messages=[
                {
                    "role": "system",
                    "content": r"""你是一个专业的数据可视化和工程绘图专家，请根据用户需求生成高质量的Python绘图代码。

## 零、代码质量要求（最重要，必须严格遵守）

### 0.1 语法正确性（生死攸关，绝对不能出错）
**特别警告**：未闭合的括号会导致代码完全无法执行！生成代码后必须进行括号匹配检查：

**常见错误示例（必须避免）**：
```python
# ❌ 错误1：函数调用缺少右括号
ax.annotate('文字', xy=(0, 0), xytext=(1, 1), arrowprops=dict(arrowstyle='->'  # 缺少 )

# ❌ 错误2：函数调用参数列表未闭合
plt.plot(x, y, 'b-', linewidth=2, label='曲线'  # 缺少 )

# ❌ 错误3：嵌套括号未正确配对
ax.plot([x1, x2, x3], [y1, y2,  # 缺少 ])

# ❌ 错误4：字符串引号未闭合
ax.set_title('这是一段未闭合的标题  # 缺少 '

# ❌ 错误5：字典参数缺少右括号
arrowprops=dict(facecolor='red', arrowstyle='->'  # 缺少 )
```

**正确示例（必须遵循）**：
```python
# ✅ 正确1：完整的函数调用
ax.annotate('文字', xy=(0, 0), xytext=(1, 1), arrowprops=dict(arrowstyle='->'))

# ✅ 正确2：完整的绘图语句
plt.plot(x, y, 'b-', linewidth=2, label='曲线')

# ✅ 正确3：嵌套括号正确配对
ax.plot([x1, x2, x3], [y1, y2, y3], 'r-')

# ✅ 正确4：字符串正确闭合
ax.set_title('这是一段完整的标题')

# ✅ 正确5：字典参数完整
arrowprops=dict(facecolor='red', arrowstyle='->')
```

**必须执行的检查步骤**（生成代码前必须按此顺序检查）：
1. 从代码开头到结尾，数一数每个 `(` 是否都有对应的 `)`
2. 检查每个函数调用的最后一行是否以 `)` 结尾
3. 检查每个字符串（用引号括起来的内容）是否都有结束引号
4. 特别注意 `ax.annotate()`, `ax.plot()`, `dict()` 等有多层嵌套的函数调用
5. **确认无误后再输出代码**

### 0.2 代码完整性
- 不要生成被截断的代码（代码必须完整结束）
- 确保每个函数调用都有完整的参数列表
- 确保多行语句使用正确的续行符（反斜杠 `\` 或括号内的隐式续行）
- 代码最后必须确保所有括号都闭合

### 0.3 变量定义完整性（生死攸关，绝对不能出错！）
**常见错误示例（必须避免）**：
```python
# ❌ 错误1：使用单字母未定义变量（最常见！）
plt.plot(x, y, 'b-')  # x, y 未定义

# ❌ 错误2：变量名拼写错误或引用不存在的变量
x_val = 5
y_val = 3  # 假设定义了 y_val
print(z_val)  # z_val 未定义，会报错：name 'z_val' is not defined

# ❌ 错误3：假设外部数据存在
data = article['values']  # article 未定义
result = processed_data  # processed_data 未定义
```

**正确示例（必须遵循）**：
```python
# ✅ 正确1：在使用变量前明确定义
import numpy as np
x = np.linspace(0, 10, 100)  # 定义 x
y = np.sin(x)                  # 定义 y
plt.plot(x, y, 'b-')          # 现在可以使用了

# ✅ 正确2：定义所有需要的数据
x_val = 5
y_val = 3
z_val = x_val + y_val  # z_val 是基于已定义的 x_val 和 y_val 计算的
print(z_val)   # 现在可以使用了

# ✅ 正确3：显式生成数据，不依赖外部源
data = [1, 2, 3, 4, 5]  # 直接定义数据
plt.plot(data)
```

**必须执行的检查步骤**（生成代码前必须逐项检查）：
1. 逐行检查代码，确保每个使用的变量都已定义
2. 特别注意单字母变量（x, y, a, b, k, t 等）是否在使用前定义
3. 检查数组操作中的变量（如 data[:, 0]）是否 data 已定义
4. 确认没有引用任何"假设存在"的外部数据
5. **确认无误后再输出代码**

## 一、技术要求
1. 只使用matplotlib库（可配合numpy等基础库）
2. 代码要完整，包括导入、数据生成（如果需要）、绘图、保存图片
3. 图片保存路径必须使用变量 target_filename（已预定义为带时间戳的唯一文件名）
4. 生成的代码必须可以直接执行，不要包含任何解释性文字
5. 代码风格要简洁、规范、可读性强
6. **确保中文正常显示**（最重要）：
   ```python
   import matplotlib
   matplotlib.rcParams['font.sans-serif'] = [
       'STHeiti',           # 华文黑体(系统自带,推荐)
       'Heiti TC',          # 黑体-繁
       'Heiti SC',          # 黑体-简
       'Hiragino Sans GB',  # 冬青黑体
       'PingFang SC',       # 苹方-简
       'Arial Unicode MS',  # Arial Unicode(备选)
       'SimHei',            # 黑体(Windows/Linux)
       'STSong',            # 华文宋体
       'Songti SC'          # 宋体-简
   ]
   matplotlib.rcParams['axes.unicode_minus'] = False
   ```
7. 只返回可执行的Python代码，不要返回任何其他内容（如解释、说明等）
8. **代码必须完全自包含**（最重要）：
    - **所有变量都必须在使用前明确定义**
    - **不要使用任何未在代码中定义的变量名**（如 article、data、result 等）
    - **不要假设任何预定义的数据或变量存在**（除了 target_filename）
    - **所有需要的数据（数值、列表、数组等）都必须在代码中显式定义或生成**
    - **示例错误**：`plt.plot(article['data'])` ❌（article 未定义）
    - **示例正确**：`data = [1, 2, 3, 4, 5]` 然后 `plt.plot(data)` ✅
9. **matplotlib 导入规范**（重要）：
    - 基本导入：`import matplotlib.pyplot as plt` 和 `import matplotlib.patches as patches`
    - 图形类导入：
      - 矩形：`from matplotlib.patches import Rectangle`
      - 圆形：`from matplotlib.patches import Circle`
      - 弧线：`from matplotlib.patches import Arc`
      - 多边形：`from matplotlib.patches import Polygon`
      - 箭头：使用 `ax.annotate()` 的 `arrowprops` 参数，不要导入 Arrow 类
    - **线条类注意**（重要）：不要使用 `matplotlib.patches.Line2D`，这是错误的！
      - 绘制线条使用：`ax.plot()`, `ax.axhline()`, `ax.axvline()` 等方法
      - 如需 Line2D 类，使用：`from matplotlib.lines import Line2D`
    - **3D绘图注意**（重要）：不要使用不稳定的3D函数！
      - 禁止使用：`from matplotlib.patches import pathpatch_2d_to_3d`（该函数不存在！）
      - 绘制3D图形时，直接使用mpl_toolkits.mplot3d的方法：
        ```python
        from mpl_toolkits.mplot3d import Axes3D
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        # 直接使用ax的3D方法，如 ax.plot_surface(), ax.plot_wireframe() 等
        ```
      - 不要将2D patches转换为3D，这会导致错误
    - 不要随意导入不确定的类，优先使用 plt 和 ax 的方法
10. **样式设置规范**（重要）：
    - **禁止使用已弃用的样式**：不要使用 `plt.style.use('seaborn-darkgrid')` 或类似的旧版 seaborn 样式
    - 这些样式在新版 matplotlib 中已被移除，会导致 `'seaborn-darkgrid' is not a valid package style` 错误
    - **正确的做法**：不要调用 `plt.style.use()`，直接使用默认样式即可
    - 如需美化图形，通过设置 rcParams 或直接在绘图时指定颜色、线型等参数来实现
    - 示例错误：`plt.style.use('seaborn-darkgrid')` ❌
    - 示例正确：使用 `ax.plot(x, y, color='blue', linewidth=2)` 或 `plt.grid(True, alpha=0.3)` ✅

11. **颜色和线型参数规范**（生死攸关，绝对不能违反！）：
    - **致命错误**：绝不能在 `color` 参数中使用格式字符串（如 'k--', 'b-', 'r--' 等）
    - **错误示例**（会导致执行失败）：
      ```python
      # ❌ 错误1：color参数包含格式字符串
      ax.plot(x, y, color='k--', linewidth=2)  # 会报错：'k--' is not a valid value for color
      ax.plot(x, y, color='b-', linewidth=2)   # 会报错：'b-' is not a valid value for color
      ax.plot(x, y, color='r--', linewidth=2)  # 会报错：'r--' is not a valid value for color

      # ❌ 错误2：使用多字母颜色名加符号
      ax.plot(x, y, color='purple-', linewidth=2)  # 错误！

      # ❌ 错误3：在color参数中混合颜色和线型
      ax.plot(x, y, color='blue--', linewidth=2)  # 错误！
      ```
    - **正确做法**（必须严格遵守）：
      ```python
      # ✅ 正确1：将颜色和线型分开指定（推荐）
      ax.plot(x, y, color='black', linestyle='--', linewidth=2)

      # ✅ 正确2：使用格式字符串作为位置参数（第三参数）
      ax.plot(x, y, 'k--', linewidth=2)

      # ✅ 正确3：使用命名的颜色
      ax.plot(x, y, color='blue', linestyle='-', linewidth=2)
      ax.plot(x, y, color='red', linestyle='--', linewidth=2)
      ax.plot(x, y, color='green', linestyle=':', linewidth=2)

      # ✅ 正确4：使用十六进制颜色代码
      ax.plot(x, y, color='#1f77b4', linestyle='-', linewidth=2)
      ```
    - **格式字符串使用规则**：
      * 格式字符串（如 'k--', 'b-', 'r:'）只能作为位置参数使用
      * 绝不能放在 `color=`、`linestyle=` 等关键字参数中
      * 如果使用关键字参数，必须分别指定 `color` 和 `linestyle`
    - **常用颜色名称**（用于 color 参数）：
      * `'black'` 或 `'k'`, `'blue'` 或 `'b'`, `'red'` 或 `'r'`
      * `'green'` 或 `'g'`, `'orange'`, `'purple'`, `'brown'`, `'pink'`
      * 或使用十六进制：`'#1f77b4'`, `'#d62728'`, `'#2ca02c'` 等
    - **常用线型**（用于 linestyle 参数）：
      * `'-'` 实线, `'--'` 虚线, `':'` 点线, `'-.'` 点划线
      * `'none'` 或 `''` 无线条
    - **生成代码前检查**：
      1. 搜索所有 `color=` 参数，确认不包含 `'--'`, `'-'`, `':'` 等线型符号
      2. 如果 `color` 参数中有 `-` 或 `:` 等符号，立即修正
      3. 推荐始终使用分离的 `color` 和 `linestyle` 参数

## 二、通用绘图规范

### 2.1 图形尺寸和清晰度
- 使用 figsize=(10, 8) 或根据实际需要调整，确保图形清晰不拥挤
- 设置 dpi=100 或更高，保证图片质量
- 使用 plt.tight_layout() 自动调整布局

### 2.2 线条和样式规范
- **主要元素**：linewidth=2-3，使用醒目颜色
- **次要元素**：linewidth=1-1.5，使用辅助色
- **辅助线/参考线**：linewidth=0.5-1，使用虚线或浅色
- 添加适当的箭头、标记符号辅助说明

 ### 2.3 标注和文字规范
- 所有重要部分都要有清晰的中文标注
- 使用 ax.annotate() 添加带箭头的标注，格式：ax.annotate('文字', xy=(x,y), xytext=(偏移), arrowprops=dict(facecolor='color'))
- **文字标注位置规范**（非常重要，必须严格遵守）：
    - **实心物体**（如填充的矩形、圆形等）：文字必须标注在物体外部，绝对不能遮挡物体
    - **空心物体**（如圆环、空心框、仅边线的图形）：文字可以在内部或外部标注
    - 使用箭头指向物体（xy 参数指向物体边缘，xytext 参数在外部设置文字位置）
    - 如果必须标注物体内部属性（如质量、名称），使用引线将文字引到外部
    - 多个标注时，手动调整 xytext 坐标，确保文字之间不重叠
- **防止文本和图形遮挡的额外措施**：
   - 所有文字标注使用 `bbox=dict(boxstyle='round', facecolor='white', alpha=0.8)` 添加半透明背景
   - 使用 `zorder` 参数确保文字在所有图形之上（文字 zorder=10 或更高）
   - 当标注多个物体时，使用不同的 xytext 偏移量分散文字位置
   - 在添加标注前检查潜在的重叠，必要时调整坐标
   - 使用 `plt.tight_layout()` 和 `bbox_inches='tight'` 优化整体布局
- 标题字体 fontsize=14-16，轴标签 fontsize=12-14，标注文字 fontsize=10-12
- 标注位置要合理，不遮挡图形主体
- 添加图例（plt.legend()）说明不同元素

### 2.4 颜色方案
- 使用专业配色方案，避免过于鲜艳刺眼的颜色
- 推荐颜色：蓝色('#1f77b4')、红色('#d62728')、绿色('#2ca02c')、橙色('#ff7f0e')、紫色('#9467bd')
- 背景保持白色
- 重要部分用醒目颜色标注，次要部分用浅色

 ### 2.5 坐标轴和布局
- 根据需要设置坐标轴标签和标题
- 对于需要保持比例的图形（如圆形、正方形），使用 ax.set_aspect('equal')
- 使用 plt.grid(True, alpha=0.3) 添加网格线（数据可视化类）
- 主体居中显示，留出适当边距
- **布局优化防止遮挡**（重要）：
   - 使用 `plt.tight_layout()` 自动调整子图间距
   - 使用 `plt.subplots_adjust(left=0.1, right=0.95, top=0.95, bottom=0.1)` 手动调整边距
   - 保存图片时必须使用 `bbox_inches='tight'` 避免元素被裁剪
   - 为文字标注添加半透明背景防止与图形重叠

### 2.6 特殊字符和数学符号显示规范（非常重要）
- **希腊字母**：优先使用LaTeX格式，确保正确显示
  ```python
  # 正确做法
  ax.set_xlabel(r'$\alpha$', fontsize=12)      # α
  ax.set_ylabel(r'$\beta$', fontsize=12)       # β
  ax.annotate(r'$\theta$', ...)               # θ
  ax.set_title(r'$\pi$ 的计算', fontsize=16)    # π
  ```
- **上下标和分数**：
  ```python
  # 正确做法
  ax.set_xlabel(r'$x^2$', fontsize=12)                    # 上标
  ax.set_ylabel(r'$x_1$', fontsize=12)                    # 下标
  ax.annotate(r'$\frac{a}{b}$', ...)                    # 分数
  ax.set_title(r'$e^{i\pi} + 1 = 0$', fontsize=16)       # 复杂公式
  ```
- **特殊数学符号**：
  ```python
  # 常用符号
  r'$\infty$'    # 无穷大 ∞
  r'$\pm$'       # 加减 ±
  r'$\times$'    # 乘 ×
  r'$\div$'      # 除 ÷
  r'$\approx$'   # 约 ≈
  r'$\leq$'      # 小于等于 ≤
  r'$\geq$'      # 大于等于 ≥
  ```
- **量子态符号**（必须使用LaTeX，不能用Unicode字符如⟨⟩）：
  ```python
  # 量子态右矢 |ψ⟩
  r'$|0\rangle$'      # |0⟩
  r'$|1\rangle$'      # |1⟩
  r'$|\psi\rangle$'   # |ψ⟩
  r'$|\phi\rangle$'   # |φ⟩

  # 量子态左矢 ⟨ψ|
  r'$\langle 0|$'     # ⟨0|
  r'$\langle 1|$'     # ⟨1|
  r'$\langle\psi|$'   # ⟨ψ|

  # 叠加态
  r'$\alpha|0\rangle + \beta|1\rangle$'  # α|0⟩ + β|1⟩

  # 实际使用示例
  ax.annotate(r'测量 → $|0\rangle$', xy=(x, y), fontsize=12)
  ax.text(0.5, 0.5, r'$\langle\psi|\hat{H}|\psi\rangle$', fontsize=14)

  # ❌ 错误：直接使用Unicode字符会显示为方框或空白
  # ax.annotate('测量 → |0⟩', ...)  # ⟨ 和 ⟩ 无法正确显示
  ```
- **物理量符号**：
  ```python
  # 物理量使用斜体（LaTeX默认）
  r'$m$', r'$F$', r'$N$', r'$T$', r'$\theta$', r'$\omega$'
  ```
- **注意事项**：
  - 所有LaTeX字符串前加 `r` 前缀（原始字符串）：`r'$\alpha$'`
  - 使用双美元符号 `$$` 表示行间公式：`$$\alpha^2 + \beta^2 = \gamma^2$$`
  - 避免使用生僻Unicode字符，如不确定则使用LaTeX格式
  - 负号已通过 `matplotlib.rcParams['axes.unicode_minus'] = False` 设置
- **mathtext不支持的LaTeX命令（必须避免）**：
  ```python
  # ❌ 错误：matplotlib mathtext不支持这些命令
  r'$\xrightarrow{...}$'   # 不支持，使用 Unicode '→' 或 r'$\rightarrow$' 代替
  r'$\xleftarrow{...}$'   # 不支持
  r'$\overset{...}{...}$' # 不支持
  r'$\underset{...}{...}$' # 不支持

  # ✅ 正确替代方案
  '→'                     # 使用 Unicode 箭头（推荐）
  r'$\rightarrow$'        # 或使用普通箭头符号
  r'$|0\rangle \xrightarrow{测量} |1\rangle$'  # ❌ 错误
  r'$|0\rangle \rightarrow |1\rangle$'        # ✅ 正确
  '流程：状态A → 状态B → 状态C'                  # ✅ 正确（使用Unicode箭头）
  ```
- **文字和公式的混合标注**：
  ```python
  # 正确示例
  ax.annotate(f'α = {value:.2f}',
              xy=(x, y),
              xytext=(x+0.3, y+0.3),
              bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
  ```

### 2.7 图层顺序和避免遮挡（重要）
- **绘图顺序原则**：按照"背景→网格线→辅助线→主体图形→填充区域→边框→箭头→文字标注"的顺序绘制
- **避免遮挡的具体方法**：
   - 先绘制大型背景元素（如网格、辅助线）
   - 再绘制主体图形（如矩形、圆形、线条等）
   - 然后绘制填充区域（使用 alpha 参数设置透明度，避免完全遮挡）
   - 最后绘制箭头和文字标注（确保在最上层）
- **使用 zorder 参数**：
   - 背景元素：zorder=0-1
   - 网格线：zorder=1
   - 辅助线：zorder=2
   - 主体图形：zorder=3-5
   - 填充区域：zorder=3-4（设置 alpha=0.3-0.7 透明度）
   - 边框线：zorder=5-6
   - 箭头：zorder=10（确保在所有图形上方）
   - 文字标注：zorder=10（确保在所有元素上方）
- **特殊场景处理**：
   - 当填充区域可能遮挡其他元素时，使用 alpha 参数（0.3-0.7）设置半透明
   - 当多个图形重叠时，使用不同的 zorder 值控制前后顺序
   - 使用 bbox=dict(boxstyle='round', facecolor='white', alpha=0.8) 为文字添加背景，避免文字与图形重叠
- **透明度设置**：
   - 填充区域默认使用 alpha=0.5 半透明
   - 重叠的填充区域使用不同 alpha 值区分层次
   - 文字背景使用 alpha=0.8 保证可读性

## 三、分类绘图规范

### 3.1 数据可视化类（折线图、曲线图、柱状图等）——最重要！

#### 3.1.1 基本要求
- 必须有清晰的标题、轴标签、图例
- 数据点要清晰可见，使用 marker 符号（折线图、散点图）
- 柱状图添加数值标签（ax.bar_label）
- 饼图添加百分比标注（autopct='%1.1f%%'）
- 使用合适的图表类型表达数据关系
- 添加网格线辅助读数

#### 3.1.2 防止空白图像的特别要求（生死攸关，必须严格遵守）
**警告**：以下情况会导致生成全白或全黑图像，必须严格避免！

**常见错误原因及解决方案**：

1. **数据范围错误**：
   ```python
   # ❌ 错误：数据值太小或太大，导致超出坐标轴范围
   y = [1e-10, 2e-10, 3e-10]  # 值太小
   ax.plot(x, y)  # 会在默认y轴范围内看不见

   # ✅ 正确：显式设置坐标轴范围或使用归一化数据
   ax.plot(x, y)
   ax.set_ylim(0, max(y) * 1.1)  # 根据数据动态设置范围
   ```

2. **数据全为零或未定义**：
   ```python
   # ❌ 错误：计算结果全为零
   y = np.zeros(1000)  # 全是零
   ax.plot(x, y)  # 只能看到一条底线

   # ✅ 正确：检查数据是否有效，添加调试代码
   y = calculate_function(x)
   if np.all(y == 0):
       raise ValueError("计算结果全为零，请检查函数实现")
   print(f"数据范围: {y.min()} 到 {y.max()}")  # 调试信息
   ax.plot(x, y)
   ```

3. **绘图背景与线条颜色冲突**：
   ```python
   # ❌ 错误：白色线条在白色背景上
   ax.plot(x, y, color='white', linewidth=2)

   # ✅ 正确：使用深色线条
   ax.plot(x, y, color='blue', linewidth=2)  # 蓝色
   ax.plot(x, y, color='#1f77b4', linewidth=2)  # 或使用十六进制颜色
   ```

4. **子图绘制问题**：
   ```python
   # ❌ 错误：子图循环中某个图数据有问题，导致整个图像空白
   fig, axes = plt.subplots(1, 3)
   for ax, data in zip(axes, datasets):
       P = calculate(data)  # 如果 calculate 返回 None 或空数组
       ax.plot(x, P)  # 会画不出东西

   # ✅ 正确：添加数据验证
   fig, axes = plt.subplots(1, 3)
   for ax, data in zip(axes, datasets):
       P = calculate(data)
       if P is None or len(P) == 0 or np.all(np.isnan(P)):
           print(f"警告: 数据无效")
           continue
       print(f"子图数据范围: {P.min()} 到 {P.max()}")  # 调试
       ax.plot(x, P, color='blue', linewidth=2)  # 明确指定颜色
   ```

5. **matplotlib 导入错误（Line2D 问题）**：
   ```python
   # ❌ 错误：从 matplotlib.patches 导入 Line2D（该模块没有这个类！）
   from matplotlib.patches import Line2D  # AttributeError: module 'matplotlib.patches' has no attribute 'Line2D'

   # ✅ 正确：从 matplotlib.lines 导入 Line2D
   from matplotlib.lines import Line2D
   legend_elements = [
       patches.Patch(facecolor='blue', label='区域'),
       Line2D([0], [0], color='red', lw=2, label='线条')
   ]
   ax.legend(handles=legend_elements)

   # ✅ 替代方案：使用 ax.plot() 生成图例，更简单
   ax.plot([], [], 'b-', label='线条')  # 空数据用于生成图例项
   ax.legend()
   ```

6. **matplotlib 3D绘图错误（pathpatch_2d_to_3d 问题）**：
   ```python
   # ❌ 错误：从 matplotlib.patches 导入 pathpatch_2d_to_3d（该函数不存在！）
   from matplotlib.patches import pathpatch_2d_to_3d  # AttributeError: module 'matplotlib.patches' has no attribute 'pathpatch_2d_to_3d'

   # ✅ 正确：直接使用3D轴的方法，不要转换2D patches
   from mpl_toolkits.mplot3d import Axes3D
   fig = plt.figure(figsize=(10, 8))
   ax = fig.add_subplot(111, projection='3d')

   # 使用3D绘图方法
   ax.plot_surface(X, Y, Z, cmap='viridis')
   ax.plot_wireframe(X, Y, Z, color='blue')
   # 或者直接在3D轴上绘制
   ax.plot(x, y, z, 'r-', linewidth=2, label='3D曲线')
   ```

7. **坐标轴范围未设置或设置不当**：
   ```python
   # ❌ 错误：自动范围设置不当
   ax.plot(x, y)  # 如果 y 值很小，可能看不见

   # ✅ 正确：显式设置合理的坐标轴范围
   ax.plot(x, y, 'b-', linewidth=2)
   ax.set_xlim(x.min(), x.max())
   ax.set_ylim(y.min() * 0.9, y.max() * 1.1)  # 留出10%边距
   ```

6. **特殊函数计算错误**（如拉盖尔多项式、贝塞尔函数等）：
   ```python
   # ❌ 错误：特殊函数返回 NaN 或 Inf
   from scipy import special
   L = special.genlaguerre(n-l-1, 2*l+1)(rho)  # 可能返回无效值
   y = np.exp(-rho/2) * (rho**l) * L  # 如果 L 包含 NaN，结果也是 NaN

   # ✅ 正确：验证特殊函数的输出
   L = special.genlaguerre(n-l-1, 2*l+1)(rho)
   if np.any(np.isnan(L)) or np.any(np.isinf(L)):
       raise ValueError("拉盖尔多项式计算结果包含 NaN 或 Inf")
   y = np.exp(-rho/2) * (rho**l) * L
   y = np.nan_to_num(y, nan=0.0, posinf=0.0, neginf=0.0)  # 清理无效值
   ```

**必须执行的检查清单**（生成代码前必须逐项检查）：
□ 所有绘图语句都显式指定了颜色（color='blue' 或 color='#1f77b4'）
□ 数据生成后立即打印数据范围（print(f"Min: {y.min()}, Max: {y.max()}"））
□ 检查数据是否包含 NaN 或 Inf（np.any(np.isnan(y)) 或 np.any(np.isinf(y))））
□ 显式设置了坐标轴范围（ax.set_xlim 和 ax.set_ylim）
□ 如果使用子图，每个子图都单独验证了数据有效性
□ 对于特殊函数计算，添加了错误处理和无效值清理
□ **绝对禁止使用 `from matplotlib.patches import Line2D`**（应使用 `from matplotlib.lines import Line2D`）
□ **绝对禁止使用 `from matplotlib.patches import pathpatch_2d_to_3d`**（该函数不存在，直接使用mpl_toolkits.mplot3d的方法）

#### 3.1.2 数据生成规范（生死攸关，必须严格遵守）
**所有数据必须在代码中显式定义或生成，不能有任何未定义的变量！**

**错误示例（必须避免）**：
```python
# ❌ 错误1：使用未定义的变量
plt.plot(x, y)  # x 和 y 未定义

# ❌ 错误2：使用假设的数据
data = article['values']  # article 未定义

# ❌ 错误3：数据点太少导致曲线不平滑
x = [0, 1, 2, 3]  # 只有4个点
y = [0, 1, 4, 9]
plt.plot(x, y)  # 曲线会很粗糙
```

**正确示例（必须遵循）**：
```python
# ✅ 正确1：使用 numpy 生成密集数据点
import numpy as np
x = np.linspace(0, np.pi, 1000)  # 生成1000个点，确保曲线平滑
y = np.sin(x)
plt.plot(x, y, 'b-', linewidth=2)

# ✅ 正确2：明确定义所有参数
import numpy as np
# 能谱示例
k = np.linspace(0, np.pi, 1000)  # 波矢范围 0 到 π
Lambda_k = np.abs(np.cos(k/2))   # 能谱公式
plt.plot(k, Lambda_k, 'r-', linewidth=2)

# ✅ 正确3：二维 Ising 模型磁化强度示例
import numpy as np
T = np.linspace(0, 1.5, 1000)    # T/T_c 范围
T_c = 1.0
# 对于 T < T_c，使用临界指数 β=1/8
M = np.zeros_like(T)
mask_below = T < T_c
M[mask_below] = (1 - T[mask_below]/T_c)**(1/8)
plt.plot(T, M, 'g-', linewidth=2)

# ✅ 正确4：添加适当的坐标轴范围和网格
plt.xlim(0, np.pi)
plt.ylim(0, 1.1)
plt.grid(True, alpha=0.3)
```

#### 3.1.3 曲线绘制规范
- 使用 `ax.plot(x, y, 'b-', linewidth=2, label='曲线名称')` 格式
- 线条宽度设为 2-3，颜色醒目
- 确保曲线在图形范围内清晰可见
- 对于多条曲线，使用不同颜色和线型区分

#### 3.1.4 坐标轴设置规范
- **必须显式设置坐标轴范围**（使用 ax.set_xlim 和 ax.set_ylim），确保曲线完整显示
- 添加坐标轴标签，使用中文
- 添加标题，说明图形内容
- 添加网格线：`plt.grid(True, alpha=0.3)`
- 使用清晰的刻度标记

#### 3.1.5 特殊标注规范
- 标注关键点（极值、零点、交点、临界点、能隙等）
- 添加文字注释说明特殊点或区域
- 对于能隙、相变点等重要位置，使用箭头或虚线标注
- 示例：
```python
# 标注临界点
ax.axvline(x=1, color='red', linestyle='--', alpha=0.5, label='T_c')
ax.annotate('临界点 T_c', xy=(1, 0), xytext=(1.1, 0.2),
            arrowprops=dict(arrowstyle='->', color='red'),
            fontsize=12)
```

#### 3.1.6 物理规律正确性
- 曲线形状必须符合物理规律（如能谱的连续性、磁化强度在临界点的平滑变化等）
- 数学公式必须正确（如二维Ising模型的临界指数β=1/8）
- 数据范围和比例关系必须合理
- 对于物理系统的曲线，必须遵循已知的理论公式或规律

 ### 3.2 物理示意图类（力学、电路、光学、机械结构等）
  - **刚体约束条件和物理真实性**（最重要，必须严格遵守）：
     - **接触面约束**：物体必须完全贴合接触面，不能有穿模或间隙
     - **斜面约束**：斜面上的物体底部必须与斜面线精确重合，使用三角函数计算坐标
     - **刚体完整性**：物体内部不能有任何线条穿模，所有几何关系必须精确计算
     - **轮子约束**：轮子必须接触地面或斜面，轮心到接触面的距离等于半径
     - **运动连续性**：如果展示运动状态，轨迹必须连续且平滑
     - **角度精确性**：所有角度必须与标注一致，不能有视觉上的偏差
     - **角度顶点定位**：摆动系统的角度顶点必须在支点/转轴处，绝不能标注在摆球或运动物体上
     - **角度参考线**：必须绘制垂直向下的虚线作为角度参考线，从支点垂直向下延伸
     - **比例一致性**：同类物体的大小比例必须合理，符合物理直觉
     - **重力方向**：重力必须严格垂直向下，不能有偏差
     - **力系平衡**：静止物体的受力分析必须满足平衡条件

 - **物体表示**：使用标准几何形状，圆形用 Circle，矩形用 Rectangle
 - **物体填充规范**：
    - 实心物体使用 fill=True，填充适当的颜色（如 facecolor='lightblue'）
    - 空心物体使用 fill=False，仅绘制边框

 - **斜面物体的精确绘制**（非常重要，必须严格遵守）：
    - **斜面上物体定位原则**：
      * 物体底部必须完全贴合斜面，不能有穿模或间隙
      * 使用三角函数精确计算，不能凭估计设置坐标
    - **斜面角度转换**：
      * 角度必须转换为弧度：theta_rad = np.radians(theta)
    - **矩形物体在斜面上的绘制方法**：
     ```python
     # 斜面参数
     theta = np.radians(30)  # 斜面角度转弧度
     incline_start_x = 0     # 斜面起点x
     incline_start_y = 0     # 斜面起点y
     distance_along_incline = 2  # 物体沿斜面的位置

     # 物体底部中心在斜面上的坐标
     bottom_center_x = incline_start_x + distance_along_incline * np.cos(theta)
     bottom_center_y = incline_start_y + distance_along_incline * np.sin(theta)

     # 矩形尺寸
     rect_width = 1.0
     rect_height = 0.5

     # 计算矩形四个顶点的坐标（考虑斜面旋转）
     # 使用旋转矩阵：
     # x' = x*cos(θ) - y*sin(θ)
     # y' = x*sin(θ) + y*cos(θ)
     # 其中(x,y)是未旋转时的相对坐标，(x',y')是旋转后的绝对坐标

     # 未旋转时矩形的四个顶点（相对于底部中心）
     corners = [
         (-rect_width/2, 0),  # 左下
         (rect_width/2, 0),   # 右下
         (rect_width/2, rect_height),   # 右上
         (-rect_width/2, rect_height)   # 左上
     ]

     # 旋转并平移到正确位置
     rotated_corners = []
     for x, y in corners:
         rot_x = x * np.cos(theta) - y * np.sin(theta)
         rot_y = x * np.sin(theta) + y * np.cos(theta)
         rotated_corners.append((
             bottom_center_x + rot_x,
             bottom_center_y + rot_y
         ))

     # 使用Polygon绘制旋转后的矩形
     from matplotlib.patches import Polygon
     rect = Polygon(rotated_corners, facecolor='lightblue', edgecolor='black', linewidth=2)
     ax.add_patch(rect)
     ```
    - **轮子（圆形）在斜面上的绘制方法**：
      ```python
      # 轮子必须接触斜面（刚体约束条件）
      wheel_radius = 0.15
      wheel_center_x = bottom_center_x - (rect_width/2 - 0.1) * np.cos(theta)
      wheel_center_y = bottom_center_y - (rect_width/2 - 0.1) * np.sin(theta) + wheel_radius

      # 注意：轮子中心的y坐标应该是斜面高度 + 轮子半径
      # 确保轮子底部刚好接触斜面（物理真实性约束）
      # 必须保证：轮心到斜面的垂直距离 = 轮子半径

      wheel = Circle((wheel_center_x, wheel_center_y), wheel_radius,
                     facecolor='black', edgecolor='black')
      ax.add_patch(wheel)
      ```

- **文字标注位置**（重要）：
   - 实心物体（如重物方块、填充的滑轮）：文字必须在物体外部，使用箭头指向
   - 空心物体（如线框、无填充圆环）：文字可以在内部或外部
   - 示例：ax.annotate('文字', xy=(物体边缘), xytext=(外部位置), arrowprops=dict(arrowstyle='->'))
- **连接关系**：绳索、导线、连杆等用直线，linewidth=2-2.5
- **关键点**：支点、节点、连接点用实心圆点标记（marker='o', markersize=8）
- **力和方向标注规范**（非常重要，必须严格遵守）：
   - **重力 mg**：必须垂直向下（从物体指向地心，即 -y 方向），箭头向下
   - **支持力 N（法向力）**：**必须垂直于接触面**（最重要！）
     * 斜面上的物体：支持力方向垂直于斜面向上，角度 = 斜面角度 - 90°
     * 使用三角函数精确计算：nx = sin(θ), ny = cos(θ)
     * 示例：斜面角度30°时，支持力角度为30°-90°=-60°（即120°）
   - **拉力 T**：沿绳索方向，远离物体
   - **摩擦力 f**：沿接触面，与相对运动或运动趋势方向相反
     * 斜面摩擦力：平行于斜面方向，角度 = 斜面角度或斜面角度 + 180°
   - 箭头使用 ax.annotate() 添加：ax.annotate('力名', xy=(起点), xytext=(终点), arrowprops=dict(arrowstyle='->', lw=2))
   - 力的箭头应该从施力物体指向受力物体，或表示运动趋势方向
   - 所有力必须标注清楚符号和大小（如有）
   - **物理规律强制要求**：
     * 使用 numpy 三角函数精确计算力的方向角度
     * 不要凭视觉估计，必须用数学公式计算
     * 斜面角度 θ 的力方向关系（单位：度）：
       - 重力：-90°（竖直向下）
       - 支持力：θ - 90°（垂直于斜面向上）
       - 摩擦力沿斜面上：θ（沿斜面向上）
       - 摩擦力沿斜面下：θ + 180°（沿斜面向下）
 - **角度标注规范**（最重要）：
    - **角的顶点定位原则**：角度的顶点必须在支点或转动轴上，绝不能标注在摆球或其他运动物体上
    - **单摆角度标注**（必须严格遵守）：
       * 角度θ的顶点在单摆的固定支点处
       * 一条边沿垂直向下方向（平衡位置，即0度或270度方向）
       * 另一条边沿摆线方向（实际摆动位置）
       - 使用 matplotlib.patches.Arc 绘制角度弧线，弧的圆心必须在支点坐标
       - 弧线半径适中（0.15-0.25 倍图形尺寸），不要太大或太小
       - theta1 和 theta2 参数必须是角度值（0-360），不是弧度
       - 从垂直向下方向（270度）开始，到摆线方向（270+θ度）
       - 角度文字使用 ax.annotate() 放置在弧线中间位置
       - 标准格式：Arc(xy=顶点坐标, width=2*半径, height=2*半径, angle=0, theta1=起始角, theta2=结束角, color='颜色')
    - **辅助线标注**（重要）：
       - 必须绘制垂直向下的虚线作为角度参考线（从支点垂直向下）
       - 使用 ax.plot() 绘制虚线：`ax.plot([支点x, 支点x], [支点y, 支点y - 长度], 'k--', alpha=0.5)`
       - 确保角度弧线清晰显示在两条边之间
- **尺寸标注**：添加必要的长度、半径标注
- **符号规范**：使用标准物理符号（如 F、mg、N、T、θ、α 等）
- 坐标轴比例相等（ax.set_aspect('equal')）
- 去除不必要的刻度，突出主体

### 3.3 几何图形类（三角形、圆形、多边形等）
- 使用几何图形的标准画法
- **角度标注**（重要）：
   - 使用 matplotlib.patches.Arc 绘制角度弧线
   - Arc 的中心点(xy)必须是角的顶点坐标
   - width 和 height 设为相同值（2*半径），确保是圆弧
   - theta1 和 theta2 必须是角度值（0-360度），计算从正x轴逆时针旋转的角度
   - 角度文字标签放置在弧线中点附近（使用三角函数计算中点坐标）
   - 示例：对于顶点在(0,0)，边线指向0°和60°的角，使用 Arc(xy=(0,0), width=0.4, height=0.4, angle=0, theta1=0, theta2=60)
- 标注顶点、边长、角度、半径等关键参数
- 使用 ax.set_aspect('equal') 保持比例
- 添加辅助线（虚线）帮助理解
- 重要的几何关系要明确标注

### 3.4 流程图/架构图
- 使用矩形框表示模块/步骤
- 使用箭头表示流程方向
- 层级清晰，从上到下或从左到右
- 添加简短的文字说明每个模块
- 使用统一的框体大小和间距

### 3.5 函数图像类
- 绘制函数曲线（使用 np.linspace 生成密集点）
- 标注关键点（极值、零点、交点等）
- 添加渐变填充或阴影突出区域
- 标注函数表达式和定义域

## 四、代码结构模板

**⚠️ 使用模板前必须确认**：按照【零、代码质量要求】检查生成的代码，确保所有括号都闭合！

### 4.1 数据可视化类模板（折线图、曲线图等）——最常用！
```python
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.patches as patches
from matplotlib.patches import Rectangle, Circle, Arc, Polygon
from matplotlib.lines import Line2D  # 用于图例中的线条
import numpy as np

# 设置中文字体(优先使用macOS系统字体)
matplotlib.rcParams['font.sans-serif'] = [
    'STHeiti',           # 华文黑体(系统自带,推荐)
    'Heiti TC',          # 黑体-繁
    'Heiti SC',          # 黑体-简
    'Hiragino Sans GB',  # 冬青黑体
    'PingFang SC',       # 苹方-简
    'Arial Unicode MS',  # Arial Unicode(备选)
    'SimHei',            # 黑体(Windows/Linux)
    'STSong',            # 华文宋体
    'Songti SC',         # 宋体-简
    'WenQuanYi Micro Hei'
]
matplotlib.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# 创建图形
fig, ax = plt.subplots(figsize=(10, 8), dpi=100)

# 【重要】所有数据必须在代码中显式定义
# 示例1：绘制能谱曲线
k = np.linspace(0, np.pi, 1000)      # 波矢范围 0 到 π
Lambda_k = np.abs(np.cos(k/2))      # 能谱公式

# 【关键】数据验证和调试（防止空白图像）
print(f"数据范围: Lambda_k.min() = {Lambda_k.min()}, Lambda_k.max() = {Lambda_k.max()}")
if np.all(Lambda_k == 0):
    raise ValueError("数据全为零，请检查计算公式")
if np.any(np.isnan(Lambda_k)) or np.any(np.isinf(Lambda_k)):
    raise ValueError("数据包含 NaN 或 Inf，请检查计算公式")

ax.plot(k, Lambda_k, 'b-', linewidth=2, label='能谱 Λ_k')

# 设置坐标轴
plt.xlabel('波矢 k', fontsize=12)
plt.ylabel('能谱 Λ_k', fontsize=12)
plt.title('能谱随波矢的变化', fontsize=16)

# 设置坐标轴范围（必须显式设置，防止数据看不见）
plt.xlim(0, np.pi)
plt.ylim(0, 1.1)

# 添加网格和图例
plt.grid(True, alpha=0.3)
plt.legend()

# 调整布局
plt.tight_layout()

# 保存图片
plt.savefig(target_filename, dpi=100, bbox_inches='tight')
plt.close()

# 示例2：绘制包含特殊函数的曲线（如径向概率密度）
# 注意：特殊函数容易产生无效值，需要严格验证
try:
    from scipy import special

    # 生成数据
    r = np.linspace(0, 30, 500)

    # 计算拉盖尔多项式（容易出错的地方）
    n, l = 2, 0
    rho = 2 * r / (n * 0.529)
    L = special.genlaguerre(n-l-1, 2*l+1)(rho)

    # 【关键】验证特殊函数的输出
    if np.any(np.isnan(L)):
        print("警告: 拉盖尔多项式包含 NaN，已清理")
        L = np.nan_to_num(L, nan=0.0)

    # 计算波函数
    R = np.exp(-rho/2) * (rho**l) * L

    # 计算概率密度
    P = (r**2) * (R**2)

    # 【关键】归一化并验证数据
    if P.max() > 0:
        P = P / P.max()  # 归一化到 [0, 1]
    else:
        raise ValueError("概率密度全为零或负数")

    print(f"概率密度范围: {P.min()} 到 {P.max()}")

    # 绘图（明确指定颜色）
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(r, P, 'b-', linewidth=2.5, label='2s 态')
    ax.fill_between(r, 0, P, alpha=0.3, color='blue')

    # 显式设置坐标轴范围
    ax.set_xlim(0, 30)
    ax.set_ylim(0, 1.1)

    ax.set_xlabel('半径 r (Å)', fontsize=12)
    ax.set_ylabel('相对概率密度', fontsize=12)
    ax.set_title('氢原子径向概率密度分布', fontsize=16)
    ax.grid(True, alpha=0.3)
    ax.legend()

    plt.tight_layout()
    plt.savefig(target_filename, dpi=100, bbox_inches='tight')
    plt.close()

except ImportError:
    print("警告: scipy 未安装，跳过特殊函数示例")
except Exception as e:
    print(f"计算或绘图失败: {str(e)}")
    raise

# 示例2：绘制二维Ising模型磁化强度曲线
# T = np.linspace(0, 1.5, 1000)  # T/T_c 范围
# T_c = 1.0
# M = np.zeros_like(T)
# mask_below = T < T_c
# M[mask_below] = (1 - T[mask_below]/T_c)**(1/8)  # 临界指数 β=1/8
# ax.plot(T, M, 'g-', linewidth=2, label='磁化强度 M')
# ax.axvline(x=T_c, color='red', linestyle='--', alpha=0.5, label='T_c')
# ax.annotate('β=1/8', xy=(0.5, 0.8), fontsize=12, ha='center')
```

### 4.2 物理示意图模板
**⚠️ 警告**：物理示意图包含大量嵌套函数调用（如 ax.annotate, ax.plot 等），最容易缺少右括号！
```python
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.patches as patches
from matplotlib.patches import Rectangle, Circle, Arc, Polygon
from matplotlib.lines import Line2D  # 用于图例中的线条
import numpy as np

# 设置中文字体(优先使用macOS系统字体)
matplotlib.rcParams['font.sans-serif'] = [
    'STHeiti',           # 华文黑体(系统自带,推荐)
    'Heiti TC',          # 黑体-繁
    'Heiti SC',          # 黑体-简
    'Hiragino Sans GB',  # 冬青黑体
    'PingFang SC',       # 苹方-简
    'Arial Unicode MS',  # Arial Unicode(备选)
    'SimHei',            # 黑体(Windows/Linux)
    'STSong',            # 华文宋体
    'Songti SC',         # 宋体-简
    'WenQuanYi Micro Hei'
]
matplotlib.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# 创建图形
fig, ax = plt.subplots(figsize=(10, 8), dpi=100)

 # 【重要】所有参数必须在代码中定义
 # 示例：斜面上的物体（必须严格遵守刚体约束条件）
 theta = np.radians(30)  # 斜面角度（转换为弧度）
 incline_start_x = 0     # 斜面起点
 incline_start_y = 0
 incline_length = 5      # 斜面长度
 rect_width = 1.0        # 物体宽度
 rect_height = 0.5       # 物体高度
 distance_along = 2      # 物体沿斜面的位置

 # 计算物体底部中心在斜面上的坐标（精确计算，确保完全贴合斜面）
 bottom_center_x = incline_start_x + distance_along * np.cos(theta)
 bottom_center_y = incline_start_y + distance_along * np.sin(theta)

 # 绘制斜面
 ax.plot([incline_start_x, incline_start_x + incline_length * np.cos(theta)],
         [incline_start_y, incline_start_y + incline_length * np.sin(theta)],
         'k-', linewidth=3)

 # 计算并绘制旋转后的矩形（刚体约束：底部必须完全贴合斜面）
 corners = [
     (-rect_width/2, 0),
     (rect_width/2, 0),
     (rect_width/2, rect_height),
     (-rect_width/2, rect_height)
 ]
 rotated_corners = []
 for x, y in corners:
     rot_x = x * np.cos(theta) - y * np.sin(theta)
     rot_y = x * np.sin(theta) + y * np.cos(theta)
     rotated_corners.append((bottom_center_x + rot_x, bottom_center_y + rot_y))

 rect = Polygon(rotated_corners, facecolor='lightblue', edgecolor='black', linewidth=2)
 ax.add_patch(rect)

# 添加标注
ax.annotate('物体', xy=(bottom_center_x, bottom_center_y + rect_height/2),
            xytext=(bottom_center_x + 0.5, bottom_center_y + rect_height + 0.3),
            arrowprops=dict(arrowstyle='->', lw=2), fontsize=12)

# 设置坐标轴比例相等
ax.set_aspect('equal')
plt.tight_layout()

# 保存图片
plt.savefig(target_filename, dpi=100, bbox_inches='tight')
plt.close()
```

 ## 五、角度标注标准示例

 ### 5.1 单摆角度标注（最重要）
 ```python
 from matplotlib.patches import Arc
 import numpy as np

 # 单摆参数
 pivot_x, pivot_y = 0, 2  # 支点坐标
 theta = np.radians(30)   # 摆角（弧度）
 string_length = 1.5      # 摆长

 # 计算摆球位置
 ball_x = pivot_x + string_length * np.sin(theta)
 ball_y = pivot_y - string_length * np.cos(theta)

 # 绘制支点
 ax.plot(pivot_x, pivot_y, 'ko', markersize=8, zorder=10)

 # 绘制摆线
 ax.plot([pivot_x, ball_x], [pivot_y, ball_y], 'k-', linewidth=2, zorder=5)

 # 绘制摆球
 from matplotlib.patches import Circle
 ball = Circle((ball_x, ball_y), 0.1, facecolor='red', edgecolor='black', zorder=6)
 ax.add_patch(ball)

 # 【关键步骤1】绘制垂直向下的虚线作为角度参考线
 # 从支点垂直向下延伸一定长度
 reference_length = 1.0
 ax.plot([pivot_x, pivot_x],
        [pivot_y, pivot_y - reference_length],
        'k--', alpha=0.5, linewidth=1.5, zorder=3, label='平衡位置')

 # 【关键步骤2】绘制角度弧线
 # 弧的圆心必须在支点坐标（pivot_x, pivot_y）
 # 从垂直向下方向（270度）开始，到摆线方向（270+θ度）
 theta_deg = np.degrees(theta)  # 转换为角度
 arc_radius = 0.3  # 弧线半径
 angle_arc = Arc(
     xy=(pivot_x, pivot_y),      # 弧的圆心（角的顶点必须在支点）
     width=2*arc_radius,
     height=2*arc_radius,
     angle=0,
     theta1=270,                  # 起始角度：垂直向下（270度）
     theta2=270 + theta_deg,     # 结束角度：270+θ度
     color='red',
     linewidth=2,
     zorder=4
 )
 ax.add_patch(angle_arc)

 # 【关键步骤3】计算弧线中点位置并放置角度标签
 mid_angle_deg = 270 + theta_deg / 2  # 弧线中点的角度（度）
 mid_angle_rad = np.radians(mid_angle_deg)  # 转换为弧度
 label_radius = arc_radius * 1.4  # 标签距离
 label_x = pivot_x + label_radius * np.cos(mid_angle_rad)
 label_y = pivot_y + label_radius * np.sin(mid_angle_rad)

 # 添加角度标签
 ax.annotate(
     f'θ',
     xy=(label_x, label_y),
     fontsize=14,
     ha='center',
     va='center',
     bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='none', alpha=0.8)
 )

 # 设置坐标轴比例相等，确保角度显示正确
 ax.set_aspect('equal')
 ```

 ### 5.2 通用角度标注
 ```python
 from matplotlib.patches import Arc
 import numpy as np

 # 角的顶点坐标
 vertex = (0, 0)

 # 两条边的角度（单位：度，从正x轴逆时针测量）
 angle1 = 0    # 第一条边的角度
 angle2 = 60   # 第二条边的角度

 # 绘制角度弧线
 arc_radius = .2  # 弧线半径
 angle_arc = Arc(
     xy=vertex,           # 弧的圆心（角的顶点）
     width=2*arc_radius,  # 宽度=2*半径
     height=2*arc_radius, # 高度=2*半径
     angle=0,             # 弧自身的旋转角度（通常为0）
     theta1=angle1,       # 起始角度（度）
     theta2=angle2,       # 结束角度（度）
     color='red',         # 弧线颜色
     linewidth=1.5
 )
 ax.add_patch(angle_arc)

 # 计算弧线中点位置（用于放置文字标签）
 mid_angle = np.radians((angle1 + angle2) / 2)  # 转换为弧度
 label_radius = arc_radius * 1.5  # 文字距离稍远一点
 label_x = vertex[0] + label_radius * np.cos(mid_angle)
 label_y = vertex[1] + label_radius * np.sin(mid_angle)

 # 添加角度标签
 ax.annotate(
     f'θ',  # 角度符号
     xy=(label_x, label_y),
     fontsize=12,
     ha='center',
     va='center'
 )
 ```

## 六、力的标注标准示例

### 6.1 基本力的标注
```python
# 绘制重力（必须垂直向下）
ax.annotate(
    'mg',  # 重力符号
    xy=(物体x坐标, 物体y坐标 - 0.3),  # 箭头终点（在物体下方）
    xytext=(物体x坐标, 物体y坐标),    # 箭头起点（在物体中心）
    arrowprops=dict(arrowstyle='->', color='red', lw=2),
    fontsize=12,
    ha='center'
)

# 绘制拉力（沿绳索方向，远离物体）
ax.annotate(
    'T',  # 拉力符号
    xy=(物体x坐标 + 0.3, 物体y坐标 + 0.3),  # 箭头终点（远离物体）
    xytext=(物体x坐标, 物体y坐标),          # 箭头起点（在物体中心）
    arrowprops=dict(arrowstyle='->', color='blue', lw=2),
    fontsize=12,
    ha='center'
)
```

### 6.2 斜面上的力标注（最重要，必须使用三角函数精确计算）
```python
import numpy as np

# 斜面参数
theta_deg = 30  # 斜面角度（度）
theta = np.radians(theta_deg)  # 转换为弧度

# 物体底部中心在斜面上的坐标
bottom_center_x = 2.0
bottom_center_y = 1.0
rect_height = 0.5

# 物体中心坐标
center_x = bottom_center_x
center_y = bottom_center_y + rect_height / 2

# 力的箭头长度
force_length = 0.8

# 【关键】使用三角函数精确计算各力的方向
# 重力：竖直向下（-90度）
mg_end_x = center_x
mg_end_y = center_y - force_length
ax.annotate(
    'mg',
    xy=(mg_end_x, mg_end_y),
    xytext=(center_x, center_y),
    arrowprops=dict(arrowstyle='->', color='red', lw=2),
    fontsize=12,
    ha='center'
)

# 支持力（法向力）：垂直于斜面向上
# 方向角度 = 斜面角度 - 90度
normal_angle = np.radians(theta_deg - 90)
n_end_x = center_x + force_length * np.cos(normal_angle)
n_end_y = center_y + force_length * np.sin(normal_angle)
ax.annotate(
    'N',
    xy=(n_end_x, n_end_y),
    xytext=(center_x, center_y),
    arrowprops=dict(arrowstyle='->', color='green', lw=2),
    fontsize=12,
    ha='center'
)

# 摩擦力：沿斜面向上（阻碍下滑）
# 方向角度 = 斜面角度
friction_angle = np.radians(theta_deg)
f_end_x = center_x + force_length * np.cos(friction_angle)
f_end_y = center_y + force_length * np.sin(friction_angle)
ax.annotate(
    'f',
    xy=(f_end_x, f_end_y),
    xytext=(center_x, center_y),
    arrowprops=dict(arrowstyle='->', color='blue', lw=2),
    fontsize=12,
    ha='center'
)

# 验证：支持力应该垂直于斜面，摩擦力应该平行于斜面
# 可以通过计算两个向量之间的夹角来验证
```

## 七、物体文字标注标准示例
```python
# 示例1：实心物体（填充的矩形）- 文字必须在外部
from matplotlib.patches import Rectangle

# 绘制实心矩形（重物）
rect = Rectangle(
    (0, 0),           # 左下角坐标
    width=1,          # 宽度
    height=1,         # 高度
    facecolor='lightblue',  # 填充颜色
    edgecolor='black',      # 边框颜色
    linewidth=2,
    fill=True          # 实心填充
)
ax.add_patch(rect)

# 文字标注在物体外部，使用箭头指向
ax.annotate(
    '重物 m',  # 标注文字
    xy=(0.5, 0),        # 箭头指向物体顶部边缘
    xytext=(0.5, -0.3), # 文字在物体外部（下方）
    arrowprops=dict(arrowstyle='->', color='black', lw=1.5),
    fontsize=12,
    ha='center'
)

# 示例2：空心物体（仅边框的圆形）- 文字可以在内部
from matplotlib.patches import Circle

# 绘制空心圆（滑轮）
circle = Circle(
    (2, 0.5),         # 圆心坐标
    radius=0.4,       # 半径
    facecolor='none', # 无填充（空心）
    edgecolor='black',
    linewidth=2,
    fill=False        # 空心
)
ax.add_patch(circle)

# 文字可以直接标注在物体内部
ax.annotate(
    '滑轮',
    xy=(2, 0.5),  # 在圆心位置
    fontsize=12,
    ha='center',
    va='center'
)
```

 ## 八、质量检查清单
  生成代码前请确认：
 □ **语法正确**（最重要！）
    - 所有 `()` `[]` `{}` 括号都正确配对
    - 所有引号 `'"` 都正确配对
    - 没有未闭合的括号或引号
    - **每个函数调用都以 `)` 结尾**
 □ **所有变量都已明确定义**（最重要！不要使用未定义的变量如 article、data 等）
 □ **所有数据都在代码中显式定义或生成**（不要假设外部数据存在）
 □ **数据点足够密集**（曲线图至少1000个点，确保曲线平滑）
 □ **坐标轴范围已显式设置**（使用 ax.set_xlim 和 ax.set_ylim）
 □ **物理公式正确**（如二维Ising模型的临界指数β=1/8）
 □ **特殊字符和符号显示正确**（重要）：
    - 希腊字母使用LaTeX格式：`r'$\alpha$'`、`r'$\beta$'`、`r'$\theta$'`、`r'$\pi$'`
    - 所有LaTeX字符串使用 `r` 前缀（原始字符串）
    - 负号显示已设置：`matplotlib.rcParams['axes.unicode_minus'] = False`
    - 上下标和分数使用LaTeX：`r'$x^2$'`、`r'$\frac{a}{b}$'`
    - 避免使用可能显示异常的生僻Unicode字符
 □ **布局优化防止遮挡**（重要）：
    - 使用了 `plt.tight_layout()` 自动调整布局
    - 保存图片使用了 `bbox_inches='tight'` 避免元素被裁剪
    - 所有文字标注与图形主体保持适当距离
    - 文字标注使用了半透明背景：`bbox=dict(boxstyle='round', facecolor='white', alpha=0.8)`
    - 使用 `zorder` 参数确保文字在所有图形之上（文字 zorder=10+）
    - 多个标注时手动调整了位置，避免文字重叠

□ **防止空白图像的特殊检查**（最重要！对于特殊函数或复杂数据计算）：
   - **数据有效性验证**：
     * 检查数据是否全为零：`not np.all(y == 0)`
     * 检查数据是否包含 NaN：`not np.any(np.isnan(y))`
     * 检查数据是否包含 Inf：`not np.any(np.isinf(y))`
   - **颜色显式指定**：
     * 所有 `ax.plot()` 都明确指定了 `color='blue'` 或类似颜色
     * 避免使用 `color='white'` 或默认颜色可能导致看不见的情况
   - **坐标轴范围验证**：
     * 使用 `ax.set_ylim(y.min()*0.9, y.max()*1.1)` 动态设置范围
     * 确保 y 轴范围覆盖所有数据点
   - **子图数据验证**：
     * 对于多子图，每个子图的数据都单独验证
     * 某个子图数据无效时跳过或处理，不影响其他子图
   - **特殊函数输出验证**：
     * scipy.special 等特殊函数的输出必须检查 NaN/Inf
     * 使用 `np.nan_to_num()` 清理无效值
     * 添加调试信息：`print(f"数据范围: {y.min()} 到 {y.max()}")`

□ 图形尺寸合适，不拥挤
 □ 所有重要元素都有中文标注
 □ 颜色方案专业、清晰
 □ 线条粗细有层次
 □ 布局合理，主体居中
 □ 需要保持比例的图形设置了 equal
 □ 添加了图例说明
 □ 实心物体的文字标注在外部，空心物体的文字标注可在内部或外部
  □ **角度标注使用了正确的 Arc 参数**（顶点坐标、角度值为度数）
  □ **单摆角度顶点在支点处**，绝不能标注在摆球上
  □ **绘制了垂直向下的虚线**作为角度参考线
  □ **角度弧线清晰可见**，半径适中（0.15-0.25倍图形尺寸）
  □ **角度标签位置合适**，在弧线中点附近
  □ 力的方向正确：重力向下、支持力垂直接触面、拉力沿绳远离物体
 □ **刚体约束条件满足**：物体完全贴合接触面，无穿模或间隙
 □ **物理真实性满足**：轮子接触面，角度精确，重力方向正确
 □ **matplotlib 导入正确**：从 `matplotlib.lines` 导入 Line2D，不是 `matplotlib.patches`
 □ **图例中使用的线条正确**：如需 Line2D，使用了 `from matplotlib.lines import Line2D`
 □ **图层顺序正确**：背景→网格→主体→填充→箭头→文字（使用了正确的 zorder 值）
□ **避免遮挡**：填充区域使用了 alpha 透明度，文字标注在最上层（zorder=10）
□ **导入正确**：没有使用 `matplotlib.patches.Line2D`，线条使用 ax.plot() 等方法
□ **代码可以直接执行，无语法错误**
□ 使用了 target_filename 变量保存文件

---

## 🚨 最终输出前强制检查（必须执行，不得跳过）

**现在你已经完成代码生成，在输出代码前必须执行以下检查**：

1. **括号匹配检查**：从代码第一行开始，逐个检查：
   - 每个 `ax.annotate(` 都有对应的 `)`
   - 每个 `plt.plot(` 都有对应的 `)`
   - 每个 `dict(` 都有对应的 `)`
   - 每个 `[` 都有对应的 `]`

2. **特别检查以下容易出错的行**：
   - 所有包含 `arrowprops=` 的行，确保最后有 `)`
   - 所有包含 `xytext=` 的行，确保最后有 `)`
   - 所有跨越多行的函数调用，确保最后有 `)`

 3. **数据生成检查**（最重要）：
    - 检查所有数据变量（x, y, k, Lambda_k, T, M 等）是否都已定义
    - 检查是否使用了 numpy 生成足够密集的数据点（至少1000个）
    - 检查是否显式设置了坐标轴范围

  4. **空白图像预防检查**（最重要！对于特殊函数或复杂数据计算必须检查）：
    - **是否显式指定了绘图颜色**（color='blue' 或类似）？
    - **是否添加了数据验证代码**？
      * `if np.all(y == 0): raise ValueError(...)`
      * `if np.any(np.isnan(y)): ...`
      * `if np.any(np.isinf(y)): ...`
    - **是否打印了数据范围**（print(f"Min: {y.min()}, Max: {y.max()}"））？
    - **坐标轴范围是否根据数据动态设置**（ax.set_ylim(y.min()*0.9, y.max()*1.1)）？
    - **如果使用了特殊函数（如 scipy.special），是否验证了输出**？
      * 检查返回值是否包含 NaN 或 Inf
      * 使用 np.nan_to_num() 清理无效值
    - **如果是多子图，是否每个子图都单独验证了数据**？

  5. **刚体约束条件检查**（物理示意图必须检查）：
     - 斜面上的物体是否完全贴合斜面，无穿模或间隙
     - 轮子是否接触地面或斜面，轮心到接触面的距离是否等于半径
     - 角度是否与标注一致，使用三角函数精确计算坐标
     - 重力是否严格垂直向下，无偏差

  6. **单摆/摆动系统角度标注检查**（重要，必须检查）：
     - 角度θ的顶点是否在支点/转轴坐标处（绝不能在摆球上）
     - 是否绘制了垂直向下的虚线作为角度参考线
     - 角度弧线的圆心参数xy是否设置为支点坐标
     - 角度弧线的theta1和theta2参数是否为角度值（度数）
     - 对于单摆：theta1=270（垂直向下），theta2=270+θ度
     - 角度标签是否放置在弧线中点附近，清晰可见

  7. **执行测试**：在脑海中逐行执行一遍代码，确认每一行都完整

**✓ 只有完成以上检查，确认代码无语法错误且数据有效后，才能输出！**
**✗ 如果发现任何未闭合的括号、未定义的变量或可能导致空白图像的问题，立即修复后再输出！**

---"""
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
            temperature=0.3,  # 降低温度，让输出更稳定
            max_tokens=8192,   # DeepSeek最大值为8192
            stream=True        # 启用流式输出
        )

        # 收集流式响应
        generated_code = ""
        total_tokens = 0
        completion_tokens = 0
        
        print(f"   [DEBUG] 开始接收流式响应...")
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                generated_code += content
                # 如果有流式回调，实时发送内容
                if stream_callback:
                    stream_callback(content)
                
        generated_code = generated_code.strip()
        print(f"   [DEBUG] AI 返回的内容长度: {len(generated_code)} 字符")
        print(f"   [DEBUG] 流式响应接收完成")

        # 检查token使用情况（流式API可能不提供usage信息）
        if hasattr(stream, 'usage') and stream.usage:
            total_tokens = stream.usage.total_tokens
            completion_tokens = stream.usage.completion_tokens
            print(f"   [DEBUG] Token使用情况 - 总计: {total_tokens}, 生成: {completion_tokens}")

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

        # 检查代码完整性（括号配对、字符串引号）
        print(f"   [DEBUG] 检查代码完整性...")
        def check_code_completeness(code):
            """检查代码括号和引号是否配对"""
            stack = []
            brackets = {'(': ')', '[': ']', '{': '}'}
            in_string = False
            string_char = None
            string_start_line = 1
            i = 0
            current_line = 1

            while i < len(code):
                char = code[i]

                # 跟踪行号用于错误报告
                if char == '\n':
                    current_line += 1

                # 检查三引号字符串（多行字符串）
                if i + 2 < len(code) and code[i:i+3] in ('"""', "'''"):
                    if not in_string:
                        in_string = True
                        string_char = code[i:i+3]
                        string_start_line = current_line
                        i += 3
                        continue
                    elif code[i:i+3] == string_char:
                        in_string = False
                        string_char = None
                        i += 3
                        continue

                # 检查普通字符串引号
                if char in '"\'' and (i == 0 or code[i-1] != '\\') and not in_string:
                    # 检查是否是三引号的开始（已经处理过，这里跳过）
                    if i + 2 < len(code) and code[i:i+3] in ('"""', "'''"):
                        i += 1
                        continue
                    in_string = True
                    string_char = char
                    string_start_line = current_line
                elif char in '"\'' and (i == 0 or code[i-1] != '\\') and in_string:
                    # 检查是否是三引号的结束（已经处理过，这里跳过）
                    if i + 2 < len(code) and code[i:i+3] in ('"""', "'''"):
                        i += 1
                        continue
                    if char == string_char:
                        in_string = False
                        string_char = None

                # 在字符串外检查括号
                if not in_string:
                    if char in brackets:
                        stack.append(char)
                    elif char in brackets.values():
                        if not stack:
                            return False, f"多余的闭合括号 '{char}'"
                        expected = brackets[stack.pop()]
                        if char != expected:
                            return False, f"括号不匹配: 期望 '{expected}'，找到 '{char}'"
                i += 1

            # 检查是否有未闭合的字符串
            if in_string:
                return False, f"未闭合的字符串引号 {repr(string_char)} (从第{string_start_line}行开始)"

            # 检查是否有未闭合的括号
            if stack:
                return False, f"未闭合的括号: {stack}"

            return True, "代码完整"

        is_complete, check_msg = check_code_completeness(generated_code)
        if not is_complete:
            print(f"   [WARNING] ⚠️ {check_msg}，尝试修复...")
            # 尝试自动修复：添加缺失的右括号
            missing_brackets = []
            for bracket in check_msg.split(':')[1].strip().split(', '):
                bracket = bracket.strip().strip('[]\'')
                if bracket in '({[':
                    if bracket == '(':
                        missing_brackets.append(')')
                    elif bracket == '[':
                        missing_brackets.append(']')
                    elif bracket == '{':
                        missing_brackets.append('}')
            if missing_brackets:
                generated_code += ''.join(missing_brackets)
                print(f"   [DEBUG] 已添加缺失的括号: {missing_brackets}")
                is_complete, check_msg = check_code_completeness(generated_code)
                if is_complete:
                    print(f"   [DEBUG] ✓ 代码修复成功")
                else:
                    print(f"   [DEBUG] ⚠️ 自动修复失败，可能仍有问题")
            else:
                print(f"   [DEBUG] ⚠️ 无法自动修复，请检查代码")

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
    """执行生成的绘图代码"""
    print("3. 正在执行绘图代码...")

    try:
        # 设置 matplotlib 使用非交互式后端（在非主线程中必须）
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        # 【重要】禁用LaTeX渲染（防止LaTeX未安装导致的错误）
        matplotlib.rcParams['text.usetex'] = False

        # 【重要】自动配置最佳中文字体
        from matplotlib import font_manager

        # 优先级字体列表（按优先级排序）
        preferred_fonts = [
            'STHeiti',              # 华文黑体 (macOS最佳)
            'Heiti TC',             # 黑体-繁
            'Heiti SC',             # 黑体-简
            'Hiragino Sans GB',     # 冬青黑体
            'PingFang SC',          # 苹方-简
            'PingFang HK',          # 苹方-港
            'Arial Unicode MS',     # Arial Unicode
            'STSong',               # 华文宋体
            'Songti SC',            # 宋体-简
            'Kaiti SC',             # 楷体-简
            'STFangsong',           # 华文仿宋
            'SimHei',               # 黑体 (Windows/Linux)
            'SimSun',               # 宋体 (Windows)
            'WenQuanYi Micro Hei'   # 文泉驿微米黑 (Linux)
        ]

        # 获取系统所有可用字体
        available_fonts = set(f.name for f in font_manager.fontManager.ttflist)

        # 选择可用的字体
        selected_fonts = [f for f in preferred_fonts if f in available_fonts]

        if selected_fonts:
            matplotlib.rcParams['font.sans-serif'] = selected_fonts
            print(f"   [DEBUG] ✓ 已配置中文字体: {selected_fonts[:3]}")
        else:
            # 备选方案：搜索包含关键字的字体
            fallback_keywords = ['Hei', 'Song', 'Kai', 'Fang', 'Unicode']
            for keyword in fallback_keywords:
                matching = [f.name for f in font_manager.fontManager.ttflist if keyword in f.name]
                if matching:
                    matplotlib.rcParams['font.sans-serif'] = matching[:5]
                    print(f"   [DEBUG] ✓ 使用备选中文字体 (关键词: {keyword}): {matching[:3]}")
                    break

        matplotlib.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

        # 创建安全的执行环境，包含常用库
        local_vars = {
            'plt': plt,
            'os': os,
            'matplotlib': __import__('matplotlib'),
            'np': __import__('numpy'),  # 添加numpy库，解决'name np is not defined'错误
            'datetime': __import__('datetime'),
            'time': __import__('time')
        }

        # 从用户提示词中提取关键词作为文件名的一部分
        import re
        import glob
        import time
        from datetime import datetime

        # 使用配置文件中的统一 images 目录
        images_dir = Config.IMAGES_DIR

        # 确保 images 目录存在
        if not os.path.exists(images_dir):
            os.makedirs(images_dir)
            print(f"   [DEBUG] 创建 images 目录: {images_dir}")

        print(f"   [DEBUG] Images 目录: {images_dir}")

        # 提取关键词
        user_prompt = state["user_prompt"]
        print(f"   [DEBUG] 用户提示词: '{user_prompt}'")

        # 去除特殊字符，只保留中文、英文、数字
        keywords = re.sub(r'[^\w\u4e00-\u9fa5]+', '_', user_prompt)
        # 截取前10个字符作为关键词
        keywords = keywords[:10].strip('_')
        print(f"   [DEBUG] 提取的关键词: '{keywords}'")

        # 生成目标文件名
        if state.get("custom_filename"):
            # 使用外部传入的自定义文件名
            target_filename = os.path.join(images_dir, state["custom_filename"])
            print(f"   [DEBUG] 使用自定义文件名: {state['custom_filename']}")
        else:
            # 如果关键词为空，使用默认值
            if not keywords:
                keywords = "graph"
                print(f"   [DEBUG] 关键词为空，使用默认值: 'graph'")

            # 生成唯一文件名：关键词_时间戳.png（使用绝对路径）
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            target_filename = os.path.join(images_dir, f"plot_{keywords}_{timestamp}.png")
            print(f"   [DEBUG] 生成默认文件名: {os.path.basename(target_filename)}")

        # 打印生成的代码前100个字符用于调试
        print(f"   [DEBUG] 生成的代码 (前100字符): {state['generated_code'][:100]}...")

        # 执行生成的代码，并将目标文件名传入执行环境
        local_vars["target_filename"] = target_filename

        # 准备全局执行环境，确保numpy等库在函数内部也可用
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

        # 记录执行前的文件列表（使用绝对路径）
        files_before = set(glob.glob(os.path.join(images_dir, "plot_*.png")))
        print(f"   [DEBUG] 执行前存在的 plot 文件: {files_before}")

        # 先进行语法检查，捕获语法错误
        print(f"   [DEBUG] 开始语法检查...")
        try:
            compile(state["generated_code"], '<string>', 'exec')
            print(f"   [DEBUG] ✓ 语法检查通过")
        except SyntaxError as se:
            error_msg = f"生成的代码存在语法错误（第{se.lineno}行）: {se.msg}"
            print(f"   [DEBUG] ✗ {error_msg}")
            print(f"   [DEBUG] 问题代码片段:\n{se.text}")
            return {"error": error_msg}

        # 检查常见的matplotlib格式字符串错误
        import re
        # 匹配类似 'purple-', 'orange-', 'brown-' 等错误格式（多字母颜色+符号）
        invalid_format_pattern = r"'[a-z]{2,}-'"
        invalid_matches = re.findall(invalid_format_pattern, state["generated_code"])
        if invalid_matches:
            error_msg = f"检测到无效的matplotlib格式字符串: {invalid_matches}。请使用 color='colorname' 或单字母颜色代码（如 'b-', 'r-', 'g-'）"
            print(f"   [DEBUG] ✗ {error_msg}")
            print(f"   [DEBUG] 找到的错误格式: {invalid_matches}")
            return {"error": error_msg}

        # 自动修复：尝试自动修正常见的 color 参数错误
        # 将 color='g--' 等模式自动转换为正确的格式
        code_to_fix = state["generated_code"]
        original_code = code_to_fix

        # 先扫描代码中所有可能的 color 参数错误，用于调试
        all_color_patterns = r"color\s*=\s*['\"][^\']*['\"]"
        all_color_matches = re.findall(all_color_patterns, code_to_fix)
        if all_color_matches:
            print(f"   [DEBUG] 🔍 扫描到 {len(all_color_matches)} 处 color 参数: {all_color_matches}")

        # 修复模式1: color='X-' -> color='colorname', linestyle='-'
        def fix_color_format(match):
            color_code = match.group(1)
            linestyle_chars = match.group(2)
            # 映射单字母颜色到完整颜色名
            color_map = {'k': 'black', 'b': 'blue', 'r': 'red', 'g': 'green',
                        'c': 'cyan', 'm': 'magenta', 'y': 'yellow', 'w': 'white'}
            full_color = color_map.get(color_code, color_code)
            # 映射线型符号到 linestyle 参数值
            linestyle_map = {'-': '-', '--': '--', ':': ':', '-.': '-.'}
            # 获取线型（取第一个字符作为主要线型）
            linestyle = linestyle_map.get(linestyle_chars, linestyle_chars[0] if linestyle_chars else '-')
            print(f"   [DEBUG] 🔧 修复: color='{color_code}{linestyle_chars}' -> color='{full_color}', linestyle='{linestyle}'")
            return f"color='{full_color}', linestyle='{linestyle}'"

        # 修复模式2: color='colorname-' -> color='colorname', linestyle='-'
        # 处理多字母颜色名加线型符号的情况，如 'purple-', 'orange-', 'brown-' 等
        def fix_color_format_multiletter(match):
            color_name = match.group(1)
            linestyle_char = match.group(2)
            # 映射线型符号到 linestyle 参数值
            linestyle_map = {'-': '-', ':': ':', '.': '.'}
            linestyle = linestyle_map.get(linestyle_char, linestyle_char if linestyle_char else '-')
            print(f"   [DEBUG] 🔧 修复多字母: color='{color_name}{linestyle_char}' -> color='{color_name}', linestyle='{linestyle}'")
            return f"color='{color_name}', linestyle='{linestyle}'"

        # 查找并替换 color='XYY' 模式（例如 color='g--', color='b-', color='k:'）
        # 使用更宽松的模式：匹配 color=' 或 color=" 后跟任意单字母颜色+线型符号
        fix_pattern = r"color\s*=\s*['\"]([a-z])([\-:\.]+)['\"]"
        fixed_code = re.sub(fix_pattern, fix_color_format, code_to_fix)

        # 查找并替换 color='colorname-' 模式（多字母颜色名）
        # 匹配如 color='purple-', color='orange-', color='brown-' 等
        fix_pattern2 = r"color\s*=\s*['\"]([a-z]{2,})([\-:\.])['\"]"
        fixed_code = re.sub(fix_pattern2, fix_color_format_multiletter, fixed_code)

        # 根据是否修复了错误，决定使用哪个版本的代码
        if fixed_code != original_code:
            print(f"   [DEBUG] 🔧 自动修正了 color 参数中的格式字符串错误")
            print(f"   [DEBUG] 修正前片段: {original_code[:200]}...")
            print(f"   [DEBUG] 修正后片段: {fixed_code[:200]}...")
            code_to_execute = fixed_code  # 使用修正后的代码
        else:
            code_to_execute = state["generated_code"]  # 使用原始代码

        # 自动修正代码中的文件名：将所有 plt.savefig() 调用中的文件名替换为 target_filename 变量

        # 匹配 plt.savefig('filename.png') 或 plt.savefig("filename.png") 的模式
        savefig_pattern = r"plt\.savefig\(['\"]([^'\"]+\.png)['\"]\)"
        savefig_matches = re.findall(savefig_pattern, code_to_execute)

        if savefig_matches:
            print(f"   [DEBUG] 检测到 {len(savefig_matches)} 处硬编码的文件名: {savefig_matches}")
            # 替换所有硬编码的文件名为 target_filename 变量
            code_to_execute = re.sub(savefig_pattern, "plt.savefig(target_filename)", code_to_execute)
            print(f"   [DEBUG] ✓ 已将文件名替换为 target_filename 变量")

        # 执行代码（合并全局和局部变量，确保函数内部能访问numpy）
        exec_vars = {**global_vars, **local_vars}

        # *** 最后的保险：全局搜索并替换所有可能的 color 参数错误 ***
        # 这个模式会匹配任何 color='...' 或 color="..." 中包含格式字符串的情况
        # 例如：color='k--', color="b-", color='g:' 等
        final_fix_pattern = r"color\s*=\s*(['\"])([a-z])([\-:\.]+)\1"
        def final_fix_color(match):
            quote = match.group(1)
            color_code = match.group(2)
            linestyle = match.group(3)
            color_map = {'k': 'black', 'b': 'blue', 'r': 'red', 'g': 'green',
                        'c': 'cyan', 'm': 'magenta', 'y': 'yellow', 'w': 'white'}
            full_color = color_map.get(color_code, color_code)
            print(f"   [DEBUG] 🚨 最终修复: color={quote}{color_code}{linestyle}{quote} -> color='{full_color}', linestyle='{linestyle}'")
            return f"color='{full_color}', linestyle='{linestyle}'"
        code_to_execute = re.sub(final_fix_pattern, final_fix_color, code_to_execute)

        # *** 自动修复特殊Unicode符号为LaTeX格式 ***
        # 将matplotlib无法显示的Unicode符号替换为LaTeX格式
        print(f"   [DEBUG] 🔍 检查并修复特殊Unicode符号...")

        original_before_unicode_fix = code_to_execute

        # 处理包含 • 符号的代码行
        # 逐行处理，智能识别字符串字面量并添加r前缀
        lines = code_to_execute.split('\n')
        fixed_lines = []

        for line in lines:
            if '•' in line:
                print(f"   [DEBUG] 🔧 发现包含 • 的代码行，进行修复")
                # 先替换 • 为 $\\cdot$
                fixed_line = line.replace('•', r'$\cdot$')

                # 如果替换后包含LaTeX公式，需要确保字符串有r前缀
                if r'$\cdot$' in fixed_line:
                    # 匹配字符串字面量并添加r前缀（如果还没有的话）
                    def add_r_prefix_if_needed(match):
                        s = match.group(0)
                        # 如果字符串包含LaTeX且没有r前缀，添加它
                        if ('$' in s and not s.startswith("r'") and not s.startswith('r"')):
                            # 避免重复添加r前缀
                            if len(s) > 1:
                                if s[0] == "'" and s[1] != 'r':
                                    return 'r' + s
                                elif s[0] == '"' and s[1] != 'r':
                                    return 'r' + s
                        return s

                    # 简化的字符串匹配（不处理转义字符的情况，足以应对大多数场景）
                    fixed_line = re.sub(r"(['\"]).*?\1", add_r_prefix_if_needed, fixed_line)

                fixed_lines.append(fixed_line)
            else:
                fixed_lines.append(line)

        code_to_execute = '\n'.join(fixed_lines)

        if code_to_execute != original_before_unicode_fix:
            print(f"   [DEBUG] ✅ Unicode符号修复完成")
        else:
            print(f"   [DEBUG] ✓ 未发现需要修复的Unicode符号")

        print(f"   [DEBUG] ✓ 最终代码检查完成，准备执行...")

        # *** 强制使用 target_filename 的双重保险 ***
        # 保存原始的 plt.savefig 函数
        original_savefig = plt.savefig

        # 定义强制使用目标文件名的 savefig 包装函数
        def forced_savefig(fname=None, *args, **kwargs):
            """强制使用目标文件名的savefig包装函数"""
            # 忽略AI传入的文件名，始终使用target_filename
            import os
            # 确保使用绝对路径
            actual_filename = os.path.abspath(target_filename)
            print(f"   [DEBUG] 🎯 强制保存到: {actual_filename}")
            return original_savefig(actual_filename, *args, **kwargs)

        # 替换 plt.savefig 为强制版本
        plt.savefig = forced_savefig

        try:
            # 执行代码
            print(f"   [DEBUG] 开始执行生成的代码...")
            exec(code_to_execute, exec_vars)
            print(f"   [DEBUG] 代码执行完成")
        finally:
            # 恢复原始的 plt.savefig 函数
            plt.savefig = original_savefig
            print(f"   [DEBUG] ✓ 已恢复原始的 plt.savefig 函数")

        # 等待文件写入
        time.sleep(0.5)

        # 记录执行后的文件列表（使用绝对路径）
        files_after = set(glob.glob(os.path.join(images_dir, "plot_*.png")))
        print(f"   [DEBUG] 执行后存在的 plot 文件: {files_after}")

        # 找出新创建的文件
        new_files = files_after - files_before
        print(f"   [DEBUG] 新创建的文件: {new_files}")

        # 优先使用新创建的文件，而不是检查目标文件
        # 这样可以避免被覆盖的旧文件造成混淆
        if new_files:
            # 如果有新文件被创建，使用它们
            new_files_list = list(new_files)
            if len(new_files_list) > 1:
                new_files_list.sort(key=os.path.getmtime, reverse=True)
                print(f"   [DEBUG] 检测到 {len(new_files_list)} 个新文件，选择最新的: {new_files_list[0]}")

            new_file = new_files_list[0]
            print(f"   [DEBUG] ✓ 使用新生成的文件: {new_file}")

            # 重命名新文件为目标文件名
            print(f"   [DEBUG] 重命名文件: {new_file} -> {target_filename}")
            os.rename(new_file, target_filename)

            file_size = os.path.getsize(target_filename)
            print(f"   [DEBUG] ✓ 最终文件: {target_filename} (大小: {file_size} 字节)")
            return {"image_path": target_filename}

        # 如果没有新文件，检查目标文件是否被更新
        # （AI可能使用了正确的 target_filename）
        if os.path.exists(target_filename):
            file_size = os.path.getsize(target_filename)
            print(f"   [DEBUG] ✓ 找到目标文件（可能是更新后的）: {target_filename} (大小: {file_size} 字节)")
            return {"image_path": target_filename}

        # 如果都没有，说明生成失败
        print(f"   [DEBUG] ✗ 图片生成失败，没有生成新文件且目标文件不存在")
        return {"error": "图片生成失败，代码执行后未生成图片"}
    except Exception as e:
        import traceback
        error_msg = f"执行代码失败: {str(e)}"
        print(f"   [DEBUG] ✗ 异常发生: {error_msg}")
        print(f"   [DEBUG] 完整堆栈跟踪:")
        traceback.print_exc()
        return {"error": error_msg}

# 保存/验证图片的节点
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
            # 获取图片大小
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

# 创建工作流图
def create_graph():
    """创建并编译工作流图"""
    # 初始化StateGraph，传入状态类型
    workflow = StateGraph(GraphState)
    
    # 添加节点
    workflow.add_node("refine_prompt", refine_prompt)  # 新增：润色提示词节点
    workflow.add_node("generate_code", generate_code)
    workflow.add_node("execute_code", execute_code)
    workflow.add_node("save_image", save_image)
    
    # 设置入口点
    workflow.set_entry_point("refine_prompt")  # 修改：入口点改为润色提示词
    
    # 添加边
    workflow.add_edge("refine_prompt", "generate_code")  # 新增：润色提示词 -> 生成代码
    workflow.add_edge("generate_code", "execute_code")
    workflow.add_edge("execute_code", "save_image")
    workflow.add_edge("save_image", END)
    
    # 编译图
    return workflow.compile()

# 主函数
def main():
    """主函数, 处理用户输入并运行工作流"""
    # 获取用户输入
    if len(sys.argv) > 1:
        user_prompt = ' '.join(sys.argv[1:])
    else:
        user_prompt = input("请输入你的绘图需求：")
    
    try:
        # 创建工作流
        graph = create_graph()
        
        # 运行工作流
        result = graph.invoke({
            "user_prompt": user_prompt,
            "generated_code": "",
            "image_path": "",
            "image_size": 0,
            "error": "",
            "custom_filename": ""  # 初始化为空字符串,使用默认文件名
        })
        
        # 输出结果
        if result.get("error"):
            print(f"❌ 错误: {result['error']}")
            sys.exit(1)
        else:
            print(f"✅ 绘图成功！图片已保存到: {result['image_path']}")
            print(f"📏 图片大小: {result['image_size'] / 1024:.2f} KB")
            print(f"📝 生成的代码:\n{result['generated_code']}")
            
            # 显示图片路径的绝对位置
            abs_path = os.path.abspath(result['image_path'])
            print(f"📍 图片绝对路径: {abs_path}")

    except Exception as e:
        print(f"❌ 工作流运行失败: {str(e)}")
        sys.exit(1)


# ==================== 公共函数（供 draw_pic.py 和 write_md_with_images.py 共同使用）====================

def get_enhanced_drawing_prompt(base_prompt: str) -> str:
    """
    生成增强的绘图提示词（包含详细的绘图规范）

    这个函数被 draw_pic.py 和 write_md_with_images.py 共同使用
    确保两种模式使用相同的高质量绘图规范

    参数:
        base_prompt: 基础的绘图需求描述

    返回:
        增强后的绘图提示词
    """
    enhanced_prompt = rf"""{base_prompt}

## 核心绘图要求（必须严格遵守）

### 通用基本要求
1. 使用matplotlib库绘制，配合numpy、scipy等科学计算库
2. 确保中文正常显示，设置中文字体
3. 添加适当的标题、坐标轴标签、图例
4. 使用清晰的配色方案（推荐：蓝色、红色、绿色、橙色、紫色）
5. 设置合理的图形尺寸(figsize=(10, 8))和dpi=100
6. **布局规划与元素间距**（生死攸关，必须严格遵守）：
   - **绘图前先规划布局**（最重要）：
     * 在绘制任何元素前，先计算所有元素的位置分布
     * 根据元素数量和大小，动态调整figsize确保不拥挤
     * 元素较多时增大图形尺寸：(12, 10)或(14, 10)甚至更大
   - **坐标轴范围强制要求**（最重要）：
     * 必须根据实际内容范围动态设置，不能使用默认值
     * 在所有元素绘制完成后，使用`ax.set_xlim()`和`ax.set_ylim()`设置范围
     * 在最大最小值基础上留出15%-20%的边距，不要让元素贴边
     * 示例：`ax.set_xlim(x_min - 0.5, x_max + 0.5)`
   - **元素间距要求**：
     * 任何两个元素之间至少保持0.5-1.0单位的间距（根据图形尺寸调整）
     * 文字标注与图形主体之间至少偏移0.3-0.5单位
     * 多个标注时使用分层或扇形分布，避免聚集在同一个区域
   - **标注位置优化**：
     * 使用`xytext`参数精确控制标注文字位置，不要直接在元素上标注
     * 标注箭头的起点(xy)和文字位置(xytext)必须分开
     * 示例：`ax.annotate('标签', xy=(x, y), xytext=(x+0.5, y+0.5), arrowprops=dict(arrowstyle='->'))`
   - **布局验证**：
     * 绘制完成后检查是否有元素重叠或过于拥挤
     * 必要时手动调整部分元素位置
7. 使用plt.tight_layout()自动调整布局
8. 确保代码可以直接执行，无语法错误

### 数据可视化类图形（曲线图、折线图等）特定要求
10. **数据点生成**（最重要）：
   - 使用numpy生成密集的数据点：x = np.linspace(起始值, 结束值, 1000)
   - 确保x轴范围足够覆盖所需区域（如0到π、0到2等）
   - 计算y值时使用明确的数学公式，不要使用未定义的变量
   - 示例：y = np.sin(x) 或 y = (1 - (t/t_c)**8)**0.125

11. **曲线绘制**：
   - 使用ax.plot(x, y, 'b-', linewidth=2, label='曲线名称')或ax.plot(x, y, color='blue', linestyle='-', linewidth=2, label='曲线名称')
   - **格式字符串颜色规范**：如果使用格式字符串（如'b-'），只能用单字母颜色代码：
     * 'b' (blue蓝色), 'r' (red红色), 'g' (green绿色), 'c' (cyan青色), 'm' (magenta品红), 'y' (yellow黄色), 'k' (black黑色), 'w' (white白色)
     * **禁止使用多字母颜色名**（如'purple-', 'orange-', 'brown-'等都是错误的！）
   - **正确做法**：使用color参数指定颜色：ax.plot(x, y, color='purple', linestyle='-', linewidth=2)
   - 线条宽度设为2-3，颜色醒目
   - 确保曲线在图形范围内清晰可见

12. **坐标轴设置**：
    - 设置合理的x轴和y轴范围（使用ax.set_xlim和ax.set_ylim）
    - 添加网格线：plt.grid(True, alpha=0.3)辅助读数
    - 添加坐标轴标签和标题，使用中文标注

13. **特殊标注**（如需要）：
    - 标注关键点（极值、零点、交点、临界点等）
    - 添加文字注释说明特殊点或区域
    - 对于能隙、相变点等重要位置，使用箭头或虚线标注

14. **代码完整性**（生死攸关）：
    - 所有变量必须在代码中显式定义或生成
    - 不要使用任何未定义的变量（如data、result等）
    - 确保所有函数调用都完整，特别是括号闭合
    - 数据必须完整，不能有undefined values

15. **物理规律正确性**：
    - 曲线形状必须符合物理规律（如能谱的连续性、磁化强度在临界点的平滑变化等）
    - 数学公式必须正确（如二维Ising模型的临界指数β=1/8）
    - 数据范围和比例关系必须合理

16. **单摆/摆动系统角度标注**（必须严格遵守）：
    - **角度顶点定位**：角度θ的顶点必须在支点/转轴处，绝不能标注在摆球或其他运动物体上
    - **参考线绘制**：必须绘制垂直向下的虚线作为角度参考线（从支点垂直向下延伸）
    - **角度弧线绘制**：使用Arc绘制角度弧线，弧的圆心必须在支点坐标
    - **角度计算**：对于单摆，从垂直向下方向（270度）开始，到摆线方向（270+θ度）

17. **刚体约束条件和物理真实性**（必须严格遵守）：
   - **接触面约束**：物体（如小车、滑块）必须完全贴合接触面，不能有穿模或间隙
   - **斜面约束**：斜面上的物体底部必须与斜面线精确重合，使用三角函数计算坐标
   - **刚体完整性**：物体内部不能有任何线条穿模，所有几何关系必须精确计算
   - **轮子约束**：轮子必须接触地面或斜面，轮心到接触面的距离等于半径
   - **重力方向**：重力必须严格垂直向下，不能有偏差
   - **力系平衡**：静止物体的受力分析必须满足平衡条件

### 重要提醒
- 如果绘制曲线图，必须使用numpy生成足够多的数据点（至少1000个）
- 必须显式设置坐标轴范围，确保曲线完整显示在图形中
- 曲线的数学关系必须准确，不能凭空捏造数据
- 对于物理系统的曲线，必须遵循已知的理论公式或规律
"""
    return enhanced_prompt


def get_drawing_system_prompt() -> str:
    """
    获取绘图系统提示词（包含完整的绘图规范）

    这个函数被两种模式共同使用

    返回:
        完整的绘图系统提示词
    """
    return r"""你是一个专业的数据可视化和工程绘图专家，请根据用户需求生成高质量的Python绘图代码。

## 零、代码质量要求（最重要，必须严格遵守）

### 0.1 语法正确性（生死攸关，绝对不能出错）
**特别警告**：未闭合的括号会导致代码完全无法执行！生成代码后必须进行括号匹配检查。

**必须执行的检查步骤**（生成代码前必须按此顺序检查）：
1. 从代码开头到结尾，确保每个 ( 都有对应的 )
2. 检查每个函数调用的最后一行是否以 ) 结尾
3. 检查每个字符串（用引号括起来的内容）是否都有结束引号
4. 特别注意 ax.annotate(), ax.plot(), dict() 等有多层嵌套的函数调用
5. **确认无误后再输出代码**

### 0.2 代码完整性
- 不要生成被截断的代码（代码必须完整结束）
- 确保每个函数调用都有完整的参数列表
- 确保多行语句使用正确的续行符（反斜杠 \ 或括号内的隐式续行）
- 代码最后必须确保所有括号都闭合

## 一、技术要求

### 1.1 中文字体配置（必须严格遵守，最重要！）

**重要说明**：matplotlib 已在执行环境中预配置最佳中文字体，生成的代码中**不需要再设置字体**！

如果必须在代码中显式设置字体（不推荐），请使用以下配置：

```python
import matplotlib
# 执行环境中已配置的字体列表（按优先级排序）
matplotlib.rcParams["font.sans-serif"] = [
    "STHeiti",              # 华文黑体 (macOS系统最佳字体)
    "Heiti TC",             # 黑体-繁
    "Heiti SC",             # 黑体-简
    "Hiragino Sans GB",     # 冬青黑体
    "PingFang HK",          # 苹方-港
    "Arial Unicode MS",     # Arial Unicode (备选)
    "STSong",               # 华文宋体
    "Songti SC",            # 宋体-简
    "Kaiti SC",             # 楷体-简
    "STFangsong",           # 华文仿宋
    "SimHei",               # 黑体 (Windows/Linux)
    "SimSun",               # 宋体 (Windows)
    "WenQuanYi Micro Hei"   # 文泉驿微米黑 (Linux)
]
matplotlib.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题
```

**注意**：
- 执行环境会自动检测并配置最佳中文字体
- 通常情况下，生成的代码中只需要 `import matplotlib` 和 `import matplotlib.pyplot as plt`
- 不需要重复设置 `rcParams["font.sans-serif"]`

1. 只使用matplotlib库（可配合numpy、scipy等科学计算库）
2. 代码要完整，包括导入、数据生成（如果需要）、绘图、保存图片
3. 图片保存路径必须使用变量 target_filename（已预定义为带时间戳的唯一文件名）
4. 生成的代码必须可以直接执行，不要包含任何解释性文字
5. 代码风格要简洁、规范、可读性强
6. **确保中文正常显示**（最重要）：使用完整的中文字体配置列表，优先使用 macOS 系统字体（STHeiti, Heiti TC/SC, Hiragino Sans GB, PingFang SC 等）
7. 只返回可执行的Python代码，不要返回任何其他内容（如解释、说明等）
8. **代码必须完全自包含**（最重要）：
     - **所有变量都必须在使用前明确定义**
     - **不要使用任何未在代码中定义的变量名**（如 article、data、result 等）
     - **不要假设任何预定义的数据或变量存在**（除了 target_filename）
     - **所有需要的数据（数值、列表、数组等）都必须在代码中显式定义或生成**
9. **matplotlib 导入规范**（重要）：
     - 基本导入：import matplotlib.pyplot as plt 和 import matplotlib.patches as patches
     - 图形类导入：Rectangle, Circle, Arc, Polygon 等
     - 箭头：使用 ax.annotate() 的 arrowprops 参数
     - 不要随意导入不确定的类，优先使用 plt 和 ax 的方法
10. **scipy 科学计算库导入规范**：
     - scipy 已在执行环境中预加载，可以直接使用
     - 常用模块：special（特殊函数）、optimize（优化）、integrate（积分）

## 二、通用绘图规范

### 2.1 图形尺寸和清晰度
- 使用 figsize=(10, 8) 或根据实际需要调整
- 设置 dpi=100 或更高
- 使用 plt.tight_layout() 自动调整布局

### 2.2 布局规划与元素间距（最重要，生死攸关）

**绘图前必须先规划布局，这是最重要的步骤！**

- **步骤1：评估元素数量和分布**
  - 在绘制任何元素前，先确定需要绘制哪些对象
  - 估算每个对象的大小和位置范围
  - 规划对象之间的间距关系

- **步骤2：动态设置坐标轴范围**（生死攸关）
  - **必须使用显式范围设置**，不能依赖自动范围
  - 在所有元素绘制完成后，根据实际范围设置：
    ```python
    # 计算所有元素的边界
    x_min, x_max = min(所有x坐标), max(所有x坐标)
    y_min, y_max = min(所有y坐标), max(所有y坐标)

    # 留出15%-20%的边距（最重要！）
    x_margin = (x_max - x_min) * 0.15 if x_max != x_min else 1.0
    y_margin = (y_max - y_min) * 0.15 if y_max != y_min else 1.0

    # 设置范围（必须留边距）
    ax.set_xlim(x_min - x_margin, x_max + x_margin)
    ax.set_ylim(y_min - y_margin, y_max + y_margin)
    ```
  - **绝对禁止**：让元素贴着坐标轴边缘显示

- **步骤3：确保元素间距**
  - 任何两个独立元素之间至少保持0.5-1.0单位间距
  - 文字标注必须与图形主体分离，使用`xytext`偏移
  - 多个标注应分散在不同区域，不要聚集在一起

- **步骤4：动态调整图形尺寸**
  - 如果元素数量多（>5个），增大figsize：(12, 10)或更大
  - 如果是横向排列的元素，增加宽度：figsize=(14, 8)
  - 如果是纵向排列的元素，增加高度：figsize=(10, 12)

- **布局验证清单**：
  - 所有元素是否完整显示在图形内？
  - 是否有元素重叠或过于拥挤？
  - 文字标注是否清晰可读，不被图形遮挡？
  - 整体布局是否美观，元素分布是否均匀？
  - 边距是否充足，元素是否贴边？

### 2.3 线条和样式规范
- 主要元素：linewidth=2-3，使用醒目颜色
- 次要元素：linewidth=1-1.5，使用辅助色
- 辅助线/参考线：linewidth=0.5-1，使用虚线或浅色

### 2.4 标注和文字规范
- 所有重要部分都要有清晰的中文标注
- 实心物体的文字必须标注在物体外部，不能遮挡物体
- 空心物体的文字可以在内部或外部
- 使用 ax.annotate() 添加带箭头的标注，格式：ax.annotate('文字', xy=(x,y), xytext=(偏移), arrowprops=dict(facecolor='color'))
- **标注位置必须精心规划**：不要让标注挤在一起，使用不同的 xytext 偏移量分散标注
- 文字标注使用半透明背景：bbox=dict(boxstyle='round', facecolor='white', alpha=0.8)

### 2.5 颜色方案
- 推荐颜色：蓝色('#1f77b4')、红色('#d62728')、绿色('#2ca02c')、橙色('#ff7f0e')、紫色('#9467bd')
- 背景保持白色

### 2.6 坐标轴和布局
- 添加坐标轴标签和标题
- 对于需要保持比例的图形，使用 ax.set_aspect('equal')
- 使用 plt.grid(True, alpha=0.3) 添加网格线（数据可视化类）
- **主体居中显示，留出适当边距**（与2.2节的布局规划配合）

### 2.7 图层顺序和避免遮挡（重要）
- 绘图顺序原则：背景→网格线→辅助线→主体图形→填充区域→边框→箭头→文字标注
- 使用 zorder 参数控制图层顺序：
  - 背景元素：zorder=0-1
  - 网格线：zorder=1
  - 辅助线：zorder=2
  - 主体图形：zorder=3-5
  - 填充区域：zorder=3-4（设置 alpha=0.3-0.7 透明度）
  - 边框线：zorder=5-6
  - 箭头：zorder=10（确保在所有图形上方）
  - 文字标注：zorder=10（确保在所有元素上方）

## 三、分类绘图规范

### 3.1 数据可视化类（折线图、曲线图、柱状图等）

#### 3.1.1 防止空白图像的特别要求（生死攸关）

**常见错误原因及解决方案**：

1. **数据范围错误**：
   - 错误：数据值太小或太大，导致超出坐标轴范围
   - 正确：显式设置坐标轴范围或使用归一化数据

2. **数据全为零或未定义**：
   - 错误：计算结果全为零
   - 正确：检查数据是否有效，添加调试代码

3. **绘图背景与线条颜色冲突**：
   - 错误：白色线条在白色背景上
   - 正确：使用深色线条（蓝色、红色等）

4. **坐标轴范围未设置或设置不当**：
   - 错误：自动范围设置不当
   - 正确：显式设置合理的坐标轴范围

5. **特殊函数计算错误**（如拉盖尔多项式、贝塞尔函数等）：
   - 错误：特殊函数返回 NaN 或 Inf
   - 正确：验证特殊函数的输出，使用 np.nan_to_num() 清理无效值

**必须执行的检查清单**：
- 所有绘图语句都显式指定了颜色（color='blue' 或类似）
- 数据生成后立即打印数据范围
- 检查数据是否包含 NaN 或 Inf
- 显式设置了坐标轴范围（ax.set_xlim 和 ax.set_ylim）
- 对于特殊函数计算，添加了错误处理和无效值清理

#### 3.1.2 数据生成规范（生死攸关）

**所有数据必须在代码中显式定义或生成，不能有任何未定义的变量！**

**正确示例（必须遵循）**：
- 使用 numpy 生成密集数据点：x = np.linspace(0, np.pi, 1000)
- 明确定义所有参数
- 添加适当的坐标轴范围和网格

#### 3.1.3 曲线绘制规范
- 使用 ax.plot(x, y, 'b-', linewidth=2, label='曲线名称') 格式
- 线条宽度设为 2-3，颜色醒目
- 确保曲线在图形范围内清晰可见

#### 3.1.4 坐标轴设置规范
- 必须显式设置坐标轴范围（使用 ax.set_xlim 和 ax.set_ylim）
- 添加坐标轴标签，使用中文
- 添加标题，说明图形内容
- 添加网格线：plt.grid(True, alpha=0.3)

### 3.2 物理示意图类

**刚体约束条件和物理真实性**（最重要，必须严格遵守）：
- 接触面约束：物体必须完全贴合接触面，不能有穿模或间隙
- 斜面约束：斜面上的物体底部必须与斜面线精确重合，使用三角函数计算坐标
- 刚体完整性：物体内部不能有任何线条穿模
- 轮子约束：轮子必须接触地面或斜面
- 角度精确性：所有角度必须与标注一致
- 重力方向：重力必须严格垂直向下
- 力系平衡：静止物体的受力分析必须满足平衡条件

**力和方向标注规范**（非常重要）：
- 重力 mg：必须垂直向下
- 支持力 N（法向力）：必须垂直于接触面
- 拉力 T：沿绳索方向，远离物体
- 摩擦力 f：沿接触面，与相对运动或运动趋势方向相反

**角度标注规范**（最重要）：
- 角的顶点定位原则：角度的顶点必须在支点或转动轴上
- 单摆角度标注：角度θ的顶点在单摆的固定支点处
- 必须绘制垂直向下的虚线作为角度参考线

### 3.3 表格绘制规范（重要）
**matplotlib 表格使用注意事项**（生死攸关）：
- **禁止使用 `cell.set_text()` 方法**：该方法不存在，会导致 AttributeError
- **正确设置单元格文本的方式**：
  ```python
  # 错误写法（会报错）
  cell.set_text("文字内容")

  # 正确写法1：通过 cellProps 在创建时设置
  table = ax.table(cellText=data, cellProps=dict(fontsize=12))

  # 正确写法2：获取文本对象后设置
  cell = table[(i, j)]
  cell.get_text().set_text("文字内容")
  cell.get_text().set_fontsize(12)
  cell.get_text().set_color('red')
  ```
- **表格单元格属性设置**：
  - 文本内容：使用 `cell.get_text().set_text()`
  - 文本颜色：使用 `cell.get_text().set_color()`
  - 字体大小：使用 `cell.get_text().set_fontsize()`
  - 背景颜色：使用 `cell.set_facecolor()`
  - 边框宽度：使用 `cell.set_linewidth()`

### 3.4 流程图/架构图
- 使用矩形框表示模块/步骤
- 使用箭头表示流程方向
- 层级清晰，从上到下或从左到右
- 添加简短的文字说明每个模块

## 八、质量检查清单
生成代码前请确认：
- 语法正确（所有括号、引号都配对）
- 所有变量都已明确定义
- 所有数据都在代码中显式定义或生成
- 数据点足够密集（曲线图至少1000个点）
- 坐标轴范围已显式设置
- 物理公式正确
- 防止空白图像的特殊检查（数据有效性、颜色显式指定、坐标轴范围验证）
- 图形尺寸合适，不拥挤
- 所有重要元素都有中文标注
- 颜色方案专业、清晰
- 布局合理，主体居中
- 刚体约束条件满足
- 物理真实性满足
- 图层顺序正确
- 避免遮挡（填充区域使用了 alpha 透明度）
- 代码可以直接执行，无语法错误
- 使用了 target_filename 变量保存文件

只返回 Python 代码，不要任何解释。
"""


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
            "custom_filename": custom_filename or ""  # 传递自定义文件名
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
