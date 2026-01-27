import os
import matplotlib.pyplot as plt
import sys
from typing import TypedDict
from langgraph.graph import StateGraph, END
from openai import OpenAI
from dotenv import load_dotenv

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
        enhanced_prompt = f"""{user_prompt}

## 核心绘图要求（必须严格遵守）

### 通用基本要求
1. 使用matplotlib库绘制，配合numpy等基础库
2. 确保中文正常显示，设置中文字体
3. 添加适当的标题、坐标轴标签、图例
4. 使用清晰的配色方案（推荐：蓝色、红色、绿色、橙色、紫色）
5. 设置合理的图形尺寸(figsize=(10, 8))和dpi=100
6. 使用plt.tight_layout()自动调整布局
7. 确保代码可以直接执行，无语法错误

### 数据可视化类图形（曲线图、折线图等）特定要求
8. **数据点生成**（最重要）：
   - 使用numpy生成密集的数据点：`x = np.linspace(起始值, 结束值, 1000)`
   - 确保x轴范围足够覆盖所需区域（如0到π、0到2等）
   - 计算y值时使用明确的数学公式，不要使用未定义的变量
   - 示例：`y = np.sin(x)` 或 `y = (1 - (t/t_c)**8)**0.125`

9. **曲线绘制**：
   - 使用`ax.plot(x, y, 'b-', linewidth=2, label='曲线名称')`
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
def generate_code(state: GraphState) -> GraphState:
    """根据润色后的提示词使用DeepSeek模型生成绘图代码"""
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

        # 调用DeepSeek模型生成代码
        print(f"   [DEBUG] 正在调用 DeepSeek 模型...")
        response = client.chat.completions.create(
            model="deepseek-chat",  # 使用DeepSeek的聊天模型
            messages=[
                {
                    "role": "system",
                    "content": """你是一个专业的数据可视化和工程绘图专家，请根据用户需求生成高质量的Python绘图代码。

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

## 一、技术要求
1. 只使用matplotlib库（可配合numpy等基础库）
2. 代码要完整，包括导入、数据生成（如果需要）、绘图、保存图片
3. 图片保存路径必须使用变量 target_filename（已预定义为带时间戳的唯一文件名）
4. 生成的代码必须可以直接执行，不要包含任何解释性文字
5. 代码风格要简洁、规范、可读性强
6. 确保中文正常显示：设置多种中文字体备选（['Arial Unicode MS', 'SimHei', 'WenQuanYi Micro Hei', 'Heiti TC', 'STHeiti']）
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
    - 不要随意导入不确定的类，优先使用 plt 和 ax 的方法

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
- **文字标注位置规范**（重要）：
   - **实心物体**（如填充的矩形、圆形等）：文字必须标注在物体外部，不能遮挡物体
   - **空心物体**（如圆环、空心框、仅边线的图形）：文字可以标注在物体内部或外部
   - 使用箭头指向物体（xy 参数指向物体，xytext 参数在外部设置文字位置）
   - 如果必须标注物体内部属性（如质量、名称），使用引线将文字引到外部
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

### 2.6 图层顺序和避免遮挡（重要）
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
- **力和方向标注规范**（重要）：
   - **重力 mg**：必须垂直向下（从物体指向地心，即 -y 方向），箭头向下
   - **支持力 N**：垂直于接触面向外（如桌面的支持力向上）
   - **拉力 T**：沿绳索方向，远离物体
   - **摩擦力 f**：沿接触面，与相对运动或运动趋势方向相反
   - 箭头使用 ax.annotate() 添加：ax.annotate('力名', xy=(起点), xytext=(终点), arrowprops=dict(arrowstyle='->', lw=2))
   - 力的箭头应该从施力物体指向受力物体，或表示运动趋势方向
   - 所有力必须标注清楚符号和大小（如有）
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
import numpy as np

# 设置中文字体
matplotlib.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'WenQuanYi Micro Hei', 'Heiti TC', 'STHeiti']
matplotlib.rcParams['axes.unicode_minus'] = False

# 创建图形
fig, ax = plt.subplots(figsize=(10, 8), dpi=100)

# 【重要】所有数据必须在代码中显式定义
# 示例1：绘制能谱曲线
k = np.linspace(0, np.pi, 1000)      # 波矢范围 0 到 π
Lambda_k = np.abs(np.cos(k/2))      # 能谱公式
ax.plot(k, Lambda_k, 'b-', linewidth=2, label='能谱 Λ_k')

# 设置坐标轴
plt.xlabel('波矢 k', fontsize=12)
plt.ylabel('能谱 Λ_k', fontsize=12)
plt.title('能谱随波矢的变化', fontsize=16)

# 设置坐标轴范围（必须显式设置）
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
import numpy as np

# 设置中文字体
matplotlib.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'WenQuanYi Micro Hei', 'Heiti TC', 'STHeiti']
matplotlib.rcParams['axes.unicode_minus'] = False

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

# 绘制支持力（垂直于接触面向上）
ax.annotate(
    'N',  # 支持力符号
    xy=(物体x坐标, 物体y坐标 + 0.3),  # 箭头终点（在物体上方）
    xytext=(物体x坐标, 物体y坐标),    # 箭头起点（在物体中心）
    arrowprops=dict(arrowstyle='->', color='green', lw=2),
    fontsize=12,
    ha='center'
)
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

  4. **刚体约束条件检查**（物理示意图必须检查）：
     - 斜面上的物体是否完全贴合斜面，无穿模或间隙
     - 轮子是否接触地面或斜面，轮心到接触面的距离是否等于半径
     - 角度是否与标注一致，使用三角函数精确计算坐标
     - 重力是否严格垂直向下，无偏差

  5. **单摆/摆动系统角度标注检查**（重要，必须检查）：
     - 角度θ的顶点是否在支点/转轴坐标处（绝不能在摆球上）
     - 是否绘制了垂直向下的虚线作为角度参考线
     - 角度弧线的圆心参数xy是否设置为支点坐标
     - 角度弧线的theta1和theta2参数是否为角度值（度数）
     - 对于单摆：theta1=270（垂直向下），theta2=270+θ度
     - 角度标签是否放置在弧线中点附近，清晰可见

 5. **执行测试**：在脑海中逐行执行一遍代码，确认每一行都完整

**✓ 只有完成以上检查，确认代码无语法错误后，才能输出！**
**✗ 如果发现任何未闭合的括号或未定义的变量，立即修复后再输出！**

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
            max_tokens=6000   # 增加到6000，确保复杂代码完整
        )

        # 提取生成的代码
        generated_code = response.choices[0].message.content.strip()
        print(f"   [DEBUG] AI 返回的内容长度: {len(generated_code)} 字符")

        # 检查token使用情况
        if hasattr(response, 'usage') and response.usage:
            total_tokens = response.usage.total_tokens
            completion_tokens = response.usage.completion_tokens
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

        # 获取脚本所在目录的绝对路径，确保路径正确
        script_dir = os.path.dirname(os.path.abspath(__file__))
        images_dir = os.path.join(script_dir, "images")

        # 确保 images 目录存在
        if not os.path.exists(images_dir):
            os.makedirs(images_dir)
            print(f"   [DEBUG] 创建 images 目录: {images_dir}")

        print(f"   [DEBUG] 脚本目录: {script_dir}")
        print(f"   [DEBUG] Images 目录: {images_dir}")

        # 提取关键词
        user_prompt = state["user_prompt"]
        print(f"   [DEBUG] 用户提示词: '{user_prompt}'")

        # 去除特殊字符，只保留中文、英文、数字
        keywords = re.sub(r'[^\w\u4e00-\u9fa5]+', '_', user_prompt)
        # 截取前10个字符作为关键词
        keywords = keywords[:10].strip('_')
        print(f"   [DEBUG] 提取的关键词: '{keywords}'")

        # 如果关键词为空，使用默认值
        if not keywords:
            keywords = "graph"
            print(f"   [DEBUG] 关键词为空，使用默认值: 'graph'")

        # 生成唯一文件名：关键词_时间戳.png（使用绝对路径）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target_filename = os.path.join(images_dir, f"plot_{keywords}_{timestamp}.png")
        print(f"   [DEBUG] 目标文件名: '{target_filename}'")

        # 打印生成的代码前100个字符用于调试
        print(f"   [DEBUG] 生成的代码 (前100字符): {state['generated_code'][:100]}...")

        # 执行生成的代码，并将目标文件名传入执行环境
        local_vars["target_filename"] = target_filename

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

        # 执行代码
        print(f"   [DEBUG] 开始执行生成的代码...")
        exec(state["generated_code"], globals(), local_vars)
        print(f"   [DEBUG] 代码执行完成")

        # 等待文件写入
        time.sleep(0.5)

        # 记录执行后的文件列表（使用绝对路径）
        files_after = set(glob.glob(os.path.join(images_dir, "plot_*.png")))
        print(f"   [DEBUG] 执行后存在的 plot 文件: {files_after}")

        # 找出新创建的文件
        new_files = files_after - files_before
        print(f"   [DEBUG] 新创建的文件: {new_files}")

        # 检查是否生成了目标文件
        if os.path.exists(target_filename):
            file_size = os.path.getsize(target_filename)
            print(f"   [DEBUG] ✓ 找到目标文件: {target_filename} (大小: {file_size} 字节)")
            return {"image_path": target_filename}

        # 如果没有生成目标文件，查找最新生成的文件（使用绝对路径）
        plot_files = glob.glob(os.path.join(images_dir, "plot_*.png"))
        print(f"   [DEBUG] 当前目录下所有 plot_*.png 文件: {plot_files}")

        if not plot_files:
            print(f"   [DEBUG] ✗ 未找到任何 plot_*.png 文件")
            return {"error": "图片生成失败，未找到生成的图片文件"}

        # 按修改时间排序，获取最新生成的文件
        plot_files.sort(key=os.path.getmtime, reverse=True)
        latest_plot = plot_files[0]
        print(f"   [DEBUG] 最新的 plot 文件: {latest_plot}")

        # 如果生成的文件名不是目标文件名，重命名它
        if latest_plot != target_filename:
            print(f"   [DEBUG] 重命名文件: {latest_plot} -> {target_filename}")
            os.rename(latest_plot, target_filename)
            latest_plot = target_filename

        file_size = os.path.getsize(latest_plot)
        print(f"   [DEBUG] ✓ 最终使用的文件: {latest_plot} (大小: {file_size} 字节)")
        return {"image_path": latest_plot}
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
            "error": ""
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

if __name__ == "__main__":
    main()
