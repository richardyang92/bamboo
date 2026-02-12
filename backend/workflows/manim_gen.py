import os
import sys
import threading
import subprocess
from typing import TypedDict
from langgraph.graph import StateGraph, END
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# 单线程锁，防止并发执行 Manim 渲染
manim_lock = threading.Lock()

class ManimState(TypedDict):
    user_prompt: str
    refined_prompt: str
    generated_code: str
    video_path: str
    video_size: int
    render_quality: str
    error: str

def refine_prompt(state: ManimState) -> ManimState:
    """使用AI润色用户的动画需求，使其更适合生成高质量的 Manim 动画"""
    print("1. 正在润色动画需求...")
    user_prompt = state["user_prompt"]

    try:

        enhanced_prompt = f"""{user_prompt}

## Manim 动画写作要求

### 基本要求
1. 使用 Manim 库创建专业动画
2. 代码结构清晰，易于理解
3. 动画流畅，时长适中（3-10秒）
4. 使用清晰的中文标注
5. 场景布局合理，元素居中
6. **所有元素必须保持足够间距，绝对不能重叠**

### 动画质量要求
1. 动画流畅度：使用适当的动画时长（run_time 参数）
2. 视觉清晰度：使用合适的字体大小和颜色
3. 过渡效果：使用 FadeIn/FadeOut/Transform 等标准过渡
4. 停顿控制：合理使用 self.wait() 控制节奏
5. 多元素协调：使用 AnimationGroup 控制多个对象的动画
6. **布局清晰：确保所有元素之间有足够间距，避免任何重叠或遮挡**

### 代码规范
1. 使用 `from manim import *` 导入
2. 创建 Scene 子类：`class AnimationScene(Scene):`
3. 实现 `construct(self)` 方法
4. 使用 `self.play()` 播放动画
5. 使用 `self.wait()` 添加停顿
6. 视频输出名使用变量 `target_filename`（不带扩展名）

### 渲染质量说明
- 低质量 (-ql): 480p, 15fps, 文件小，预览用
- 中等 (-qm): 720p, 30fps, 平衡质量
- 高质量 (-qh): 1080p, 60fps, 最佳质量
- 4K (-qk): 2160p, 60fps, 最高质量

### 常用动画对象
- **文本**: Text(), MathTex()
- **基本图形**: Circle(), Square(), Rectangle(), Triangle()
- **线条和箭头**: Line(), Arrow(), DashedLine()
- **组合对象**: VGroup(), VDict()
- **3D对象**: ThreeDScene, Cube(), Sphere()
- **表格**: IntegerTable(), MathTable()

### 重要参数限制
- **Table/Cell 边框宽度**: 使用 `stroke_width` 参数，不要使用 `linewidth`
- 错误示例: `Table(..., cell_config={'linewidth': 2})` ❌
- 正确示例: `Table(..., cell_config={'stroke_width': 2})` ✅

### 性能优化要求（关键！）
1. **限制self.play()调用**: 整个场景的 `self.play()` 调用次数应控制在 10-15 次以内，包括所有元素的创建、变换和淡出
2. **限制3D对象数量**: 3D场景中对象总数不超过30个
3. **绝对禁止UpdateFromAlphaFunc**: 对于任何涉及场可视化（电场、磁场、向量场）的3D动画，**绝对禁止使用 UpdateFromAlphaFunc**！这会导致每帧重新计算所有箭头，渲染时间可能超过10分钟
4. **推荐动画方式**: 对于振动/变化的场，只显示2-3个关键状态，不要用循环创建太多动画帧
5. **简化可视化**: 电场线、磁场线等使用少量箭头（<8个）表示即可
6. **采样点限制**: 任何场可视化，采样点不超过8个
7. **避免复杂计算**: 动画中避免复杂的数学计算循环
8. **优先静态展示**: 复杂3D场景应静态展示，然后整体旋转相机

### 常用动画方法
- **创建动画**: Create(), DrawBorderThenFill()
- **出现消失**: FadeIn(), FadeOut(), Write()
- **变换**: Transform(), ReplacementTransform()
- **移动**: MoveTo(), Shift(), Animate()
- **缩放**: Scale(), Animate().scale()
- **旋转**: Rotate(), Animate().rotate()
- **组合动画**: AnimationGroup(), Succession(), LaggedStart()
- **等待**: self.wait(1), self.wait(2)

### 高级特性
1. 使用 TexMobject 创建数学公式：`MathTex("x^2 + y^2 = r^2")`
2. 使用 BackgroundRectangle 添加背景：`AddBackgroundRectangle()`
3. 使用 SurroundingRectangle 添加边框：`SurroundingRectangle()`
4. 使用 code_mobject 显示代码：`Code()`
5. 使用 Table 创建表格：`IntegerTable()`, `MathTable()`

### 3D 场景要求
1. 继承 ThreeDScene: `class AnimationScene(ThreeDScene):`
2. 使用 `self.set_camera_orientation()` 设置相机角度
3. 使用 `self.move_camera()` 移动相机 - **直接调用，不要放在 self.play() 中**
4. 3D 对象使用 `ThreeDAxes()`, `Sphere()`, `Cube()` 等
5. **重要**: 相机方法返回 None，不能放在 self.play() 中使用

### 3D场景对象使用规则（关键！防止 IndexError）
- **ThreeDScene 必须使用 3D 专用对象**:
  - 线条: `Line3D(start, end, color, thickness)` - **绝对禁止使用 `DashedLine`, `Line`**
  - 箭头: `Arrow3D(start, end, color, thickness)` - **绝对禁止使用 `Arrow`**
  - 几何体: `Sphere()`, `Cube()`, `Dot3D()`
- **原因**: 2D对象（DashedLine等）在3D场景中会导致 IndexError "too many indices for array"

### 3D 相机方法正确用法（关键！）
```python
# ✓ 正确 - 直接调用
self.move_camera(phi=60*DEGREES, theta=45*DEGREES, run_time=2)

# ✗ 错误 - 不要放在 self.play() 中
# self.play(self.move_camera(phi=60*DEGREES, theta=45*DEGREES))
"""

        return {"refined_prompt": enhanced_prompt}
    except Exception as e:
        error_msg = f"润色提示词失败: {str(e)}"
        print(f"❌ {error_msg}")
        return {"refined_prompt": user_prompt}

def get_manim_system_prompt() -> str:
    """获取 Manim 代码生成的系统提示词"""
    return r"""你是一个专业的 Manim 动画专家，擅长创建高质量的教学动画、数学可视化和物理模拟。

## 代码规范（必须严格遵守）

### 1. 基本结构
```python
from manim import *

class AnimationScene(Scene):  # 对于3D场景使用 ThreeDScene
    def construct(self):
        # 动画内容
        self.play(Create(circle))
        self.wait(2)
```

### 2. 导入规范
- 必须使用: `from manim import *`
- 可以导入: numpy as np, math
- 视频输出路径: 使用变量 `target_filename`（不带扩展名）

### 3. Scene 类选择
- 2D 动画: 继承 `Scene`
- 3D 动画: 继承 `ThreeDScene`
- 带文字: 继承 `MovingCameraScene` (需要相机移动)

### 4. 动画播放规范
- 使用 `self.play(Animation(mobject, run_time=1))` 控制时长
- 使用 `self.wait(seconds)` 添加停顿
- 多个对象同时动画: `self.play(Animation(mobj_a), Animation(mobj_b), run_time=1)`
- 连续播放: `self.play(Animation1(), Animation2(), Animation3())`
- 分组动画: `self.play(AnimationGroup(*animations))`

### 5. 常用对象创建
- 圆形: `Circle(radius=1, color=BLUE, fill_opacity=0.5)`
- 正方形: `Square(side_length=2, color=RED)`
- 文本: `Text("Hello", font_size=48, color=WHITE)`
- 数学公式: `MathTex("x^2", font_size=72, color=YELLOW)`
- 2D箭头: `Arrow(LEFT*2, RIGHT*2, buff=0.2, color=GREEN)`  # 仅用于 Scene（2D）
- 3D箭头: `Arrow3D(start=LEFT*2, end=RIGHT*2, color=GREEN, thickness=0.02)`  # 用于 ThreeDScene
- 2D线条: `Line(LEFT*2, RIGHT*2, stroke_width=4)`  # 仅用于 Scene（2D）
- 3D线条: `Line3D(start=LEFT*2, end=RIGHT*2, color=WHITE, thickness=0.02)`  # 用于 ThreeDScene

**🚫 重要：2D与3D对象分离**
- **Scene（2D场景）**: 使用 `Arrow`, `Line`, `DashedLine`, `Circle`, `Square` 等2D对象
- **ThreeDScene（3D场景）**: 使用 `Arrow3D`, `Line3D`, `Sphere`, `Cube` 等3D对象
- **绝对禁止**: 在 ThreeDScene 中使用 `DashedLine`, `Line`, `Arrow` 等2D对象！这会导致 IndexError
- **3D场景线条**: 使用 `Line3D` 代替 `DashedLine` 或 `Line`

**Arrow3D 重要限制**：
- 不支持 `tip_length` 参数！使用默认箭头大小
- 只支持: `start`, `end`, `color`, `thickness` 参数
- 示例: `Arrow3D(start=point1, end=point2, color=GREEN, thickness=0.02)`

### 6. 颜色常量
- BLACK, WHITE, BLUE, RED, GREEN, YELLOW, PURPLE, ORANGE, PINK
- 也可以使用十六进制: `color="#FF5733"`

### 7. 定位和布局（防止元素重叠）
- 坐标系: 中心点为 ORIGIN=(0,0,0)
- 方向常量: LEFT, RIGHT, UP, DOWN, UL, UR, DL, DR
- 相对定位: `circle.shift(RIGHT*2)`, `text.next_to(circle, RIGHT, buff=1.0)`
- 对齐: `text.align_to(circle, UP)`

#### 重要：防止元素重叠的布局策略
**间距控制（buff参数）:**
- `next_to()` 使用 `buff=0.5~1.5` 保持元素间距，默认0.25太小
- 示例: `text.next_to(circle, RIGHT, buff=1.0)`  # 在circle右侧1单位处放置text
- 多个元素排布时，每个都指定明确的buff值

**布局分区策略（推荐）:**
- 上半区: `UP*2~3` 用于标题/主要元素
- 下半区: `DOWN*2~3` 用于底部元素
- 左右分栏: `LEFT*3~4` 和 `RIGHT*3~4` 分隔内容
- 中心区: `ORIGIN` 或小范围偏移用于核心元素

**避免重叠的规则:**
1. 所有 `next_to()` 调用必须指定 `buff>=0.5`
2. 多个同级元素使用 VGroup+arrange() 自动布局
   ```python
   # ✓ 正确：自动排列，避免重叠
   items = VGroup(text1, text2, text3)
   items.arrange(DOWN, aligned_edge=LEFT, buff=0.8)
   ```
3. 使用 `shift()` 为元素分组预留空间
   ```python
   left_group = VGroup(item1, item2).arrange(DOWN, buff=0.5)
   left_group.shift(LEFT*3)
   right_group = VGroup(item3, item4).arrange(DOWN, buff=0.5)
   right_group.shift(RIGHT*3)
   ```
4. 绝对定位时确保坐标不冲突（上下至少间隔1.5单位，左右至少间隔2单位）

**文本和图形的最小安全距离:**
- Text/MathTex 与其他对象: `buff >= 0.8`
- 图形之间: `buff >= 0.5` 或坐标差 >= 1.5
- 使用 `BackgroundRectangle` 为文本添加背景，避免与线条重叠

### 8. 动画时长控制
- 快速动画: `run_time=0.5`
- 中速动画: `run_time=1` (默认)
- 慢速动画: `run_time=2`
- 渐入渐出: `FadeIn(mobject, run_time=1)`

### 9. 组合动画示例
```python
# 并行动画
self.play(
    FadeIn(circle),
    FadeIn(square),
    run_time=1
)

# 连续动画
self.play(Create(circle))
self.play(Transform(circle, square))
self.play(FadeOut(square))

# 动画组
animations = AnimationGroup(
    Create(circle),
    Write(text),
    lag_ratio=0.5
)
self.play(animations, run_time=2)

# 顺序动画
self.play(
    Succession(
        Create(circle),
        Create(square),
        lag_ratio=0.3
    )
)
```

### 10. 3D 场景示例
```python
from manim import *

class AnimationScene(ThreeDScene):
    def construct(self):
        cube = Cube()
        self.play(Create(cube))

        # 相机移动（使用 self.move_camera，不是 self.camera.animate）
        self.move_camera(phi=60*DEGREES, theta=45*DEGREES, distance=6)

        # 持续旋转相机
        self.begin_ambient_camera_rotation(rate=0.2)
        self.wait(3)
        self.stop_ambient_camera_rotation()

        self.wait(2)
```

### 10.1 ThreeDScene 相机动画方法（非常重要！）
对于 3D 场景，必须使用以下相机动画方法：

#### 相机移动（直接调用，不要放在 self.play() 中！）
```python
# ✓ 正确：直接调用 self.move_camera()
self.move_camera(phi=60*DEGREES, theta=45*DEGREES, distance=6, run_time=2)
self.wait(1)

# ✗ 错误：不要把 move_camera 放在 self.play() 中
# self.play(self.move_camera(...))  # 这会报错！move_camera 返回 None
```

#### 自动相机旋转（直接调用）
```python
# ✓ 正确：直接调用
self.begin_ambient_camera_rotation(rate=0.2)
self.wait(3)
self.stop_ambient_camera_rotation()

# ✗ 错误：不要放在 self.play() 中
# self.play(self.begin_ambient_camera_rotation(...))
```

#### 关键规则总结
- ✓ **正确**: `self.move_camera(phi=60*DEGREES, theta=45*DEGREES, distance=6, run_time=2)` - **直接调用**
- ✓ **正确**: `self.begin_ambient_camera_rotation(rate=0.2)` - **直接调用**
- ✓ **正确**: `self.stop_ambient_camera_rotation()` - **直接调用**
- ✗ **错误**: `self.play(self.move_camera(...))` - **不要在 self.play() 中调用相机方法！**
- ✗ **错误**: `self.camera.animate.set_theta()` - ThreeDCamera 没有 animate 属性
- ✗ **错误**: `self.camera.animate` - 不适用于 ThreeDCamera

**原因**: `self.move_camera()`, `self.begin_ambient_camera_rotation()`, `self.stop_ambient_camera_rotation()` 这些方法直接操作场景，不返回动画对象。它们必须作为独立语句调用，不能放在 `self.play()` 中。

### 11. 数学公式动画
```python
formula = MathTex(r"x^2 + y^2 = r^2")
self.play(Write(formula, run_time=2))
self.wait(1)

# 高亮部分
part = MathTex(r"x^2")
part.set_color(YELLOW)
self.play(ReplacementTransform(formula, part))
```

### 12. 数据可视化动画
```python
# 柱状图动画
bars = [Rectangle(...) for _ in range(5)]
for bar in bars:
    self.play(FadeIn(bar), run_time=0.3)
```

### 13. 错误预防（最重要！）
✓ **括号配对**: 确保所有 `()` `[]` `{}` 正确配对
✓ **引号配对**: 确保所有 `'` `"` 正确配对
✓ **函数完整**: 每个 `self.play()` 必须以 `)` 结尾
✓ **变量定义**: 所有变量在使用前必须定义
✓ **场景完整**: `construct()` 必须有完整的动画序列
✓ **输出文件名**: 必须使用 `target_filename` 变量
✓ **3D相机动画**: `self.move_camera()` 和 `self.begin_ambient_camera_rotation()` 必须直接调用，**不能放在 `self.play()` 中**！
✓ **3D相机方法**: 绝对不能使用 `self.camera.animate.*()` - ThreeDCamera 没有 animate 属性
✓ **Arrow3D参数**: `Arrow3D` 不支持 `tip_length` 参数！只使用 `start`, `end`, `color`, `thickness`
✓ **性能限制**: 3D对象总数 <30个，场可视化采样点 <10个
✓ **绝对禁止UpdateFromAlphaFunc**: 对于任何场可视化（电场、磁场），**绝对禁止使用 UpdateFromAlphaFunc 更新箭头**！使用静态场+相机旋转代替
✓ **限制self.play()调用**: 整个场景的 `self.play()` 调用次数应控制在 10-15 次以内，避免用循环创建太多动画帧
✓ **元素无重叠**: 所有 `next_to()` 必须指定 `buff>=0.5`，或使用 `VGroup.arrange()` 自动布局
✓ **2D/3D对象分离**: ThreeDScene 中必须使用 `Line3D`, `Arrow3D` 等3D对象，**绝对禁止使用 `DashedLine`, `Line`, `Arrow` 等2D对象**
✓ **Table/Cell样式限制**: Table 和 Cell 类不支持 `linewidth` 参数！创建表格时不要传递 `linewidth` 给 Cell。如需设置边框宽度，使用 `stroke_width` 参数或创建后使用 `.set_stroke()` 方法

### 14. 质量检查清单
- [ ] 代码语法正确（所有括号、引号配对）
- [ ] 所有变量已定义
- [ ] 动画时长合理（3-10秒）
- [ ] 文字清晰可读
- [ ] 元素居中，布局合理
- [ ] 使用 target_filename 输出
- [ ] 没有未使用的导入
- [ ] 没有死代码
- [ ] **如果是 ThreeDScene，相机方法（move_camera, begin_ambient_camera_rotation）必须直接调用，不能放在 self.play() 中**
- [ ] **Arrow3D 只使用有效参数 (start, end, color, thickness)，不使用 tip_length**
- [ ] **所有元素之间有足够间距，无重叠现象** - 每个 next_to() 指定了 buff>=0.5，或使用了 VGroup.arrange()
- [ ] **如果是 ThreeDScene，必须使用3D对象（Line3D, Arrow3D），禁止使用2D对象（DashedLine, Line, Arrow）**
- [ ] **场可视化不使用 UpdateFromAlphaFunc** - 使用静态场+相机旋转，绝对禁止每帧更新箭头方向

## 输出要求
- 只返回 Python 代码
- 不要任何解释或说明
- 确保代码可以直接执行
- 使用 from manim import * 导入

请直接输出可执行的 Manim Python 代码！"""

def generate_code(state: ManimState, stream_callback=None) -> ManimState:
    """生成 Manim Python 代码"""
    print("2. 正在生成 Manim 动画代码...")

    try:
        api_key = os.getenv("DEEPSEEK_API_KEY")

        if not api_key:
            return {"error": "未设置 DEEPSEEK_API_KEY，请在 .env 文件中配置"}

        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )

        user_prompt = state["refined_prompt"]
        stream = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": get_manim_system_prompt()
                },
                {
                    "role": "user",
                    "content": f"""请根据以下需求生成 Manim 动画代码：

{user_prompt}

【⚠️ 重要提醒】生成代码时请务必：
1. 确保所有括号 () 都正确配对
2. 确保所有引号 都正确配对
3. 特别检查每个函数调用（尤其是 self.play）最后都有 )
4. 所有变量在使用前必须定义
5. construct() 方法必须有完整的动画序列
6. 使用 target_filename 作为输出文件名变量
7. **如果使用 ThreeDScene，相机方法（self.move_camera, self.begin_ambient_camera_rotation）必须直接调用，绝对不能放在 self.play() 中！**
   - ✓ 正确: `self.move_camera(phi=60*DEGREES, theta=45*DEGREES, run_time=2)`
   - ✗ 错误: `self.play(self.move_camera(phi=60*DEGREES, theta=45*DEGREES))`

【🎨 布局与防重叠要求】
8. **所有元素之间必须保持足够间距，绝对不能重叠！**
   - 使用 next_to() 时必须指定 buff>=0.5（例如：next_to(obj, RIGHT, buff=1.0)）
   - 对于多个相关元素，使用 VGroup.arrange() 自动布局（例如：items.arrange(DOWN, buff=0.8)）
   - 不同区域元素使用明确的 shift() 分隔（例如：left_group.shift(LEFT*3)）
   - 文本和图形之间至少保持 0.8 单位距离
   - 避免多个元素堆积在屏幕中央，合理分区布局

【⚡ 性能要求】
9. **确保动画能在合理时间内渲染完成！**
   - 3D场景总对象数不超过30个（包括箭头、球体、线等）
   - 电场线、磁场线等可视化使用<10个箭头表示即可
   - **绝对禁止使用 UpdateFromAlphaFunc 实时更新场可视化！这会导致渲染时间超过10分钟！**
   - **场可视化的正确做法**: 静态显示场分布，然后整体移动/旋转场景，不要每帧更新箭头方向
   - 场可视化采样点总数不超过10个（不要用 5x5x5=125个点）
   - 复杂3D场景应静态展示后整体旋转，不要每帧重新计算

【🎬 3D 场景动画推荐模式】
对于电场/磁场等物理可视化，使用以下模式：
```python
# ✓ 正确 - 静态场 + 相机旋转（推荐！）
field_arrows = VGroup(*[Arrow3D(...) for _ in range(6)])  # 仅6个箭头
self.play(Create(field_arrows))
self.begin_ambient_camera_rotation(rate=0.1)  # 旋转相机而不是更新箭头
self.wait(2)
self.stop_ambient_camera_rotation()

# ✓ 可接受 - 仅显示2-3个关键状态
# 对于振动系统，只显示起始状态和1-2个位移状态，不要做平滑动画
self.play(dipole.animate.shift(UP*0.5), run_time=1)  # 一个位移
self.play(dipole.animate.shift(DOWN*1.0), run_time=1)  # 第二个位移

# ✗ 错误 - 实时更新所有箭头（极慢！）
# UpdateFromAlphaFunc 更新20个箭头会需要10+分钟渲染
self.play(UpdateFromAlphaFunc(field_group, update_field))  # 不要这样做！

# ✗ 错误 - 用循环创建太多动画帧
for i in range(10):  # 这会创建10个self.play()调用，渲染很慢
    self.play(obj.animate.move_to(new_pos))
```

**重要**: 整个场景的 `self.play()` 调用次数应控制在 10-15 次以内，包括所有元素的创建、变换和淡出。

【🚫 Arrow3D 参数限制】
10. **Arrow3D 类不支持 tip_length 参数！**
   - Arrow3D 只支持: start, end, color, thickness
   - 错误示例: `Arrow3D(..., tip_length=0.1)`  # 这会导致 TypeError
   - 正确示例: `Arrow3D(start=point1, end=point2, color=GREEN, thickness=0.02)`

【🚫 2D/3D 对象混用限制】
11. **ThreeDScene 中绝对禁止使用 2D 对象！**
   - ThreeDScene 必须使用: `Line3D`, `Arrow3D`, `Sphere`, `Cube`, `ThreeDAxes` 等
   - ThreeDScene 禁止使用: `DashedLine`, `Line`, `Arrow`, `Circle`, `Square` 等 2D 对象
   - 错误示例（ThreeDScene 中使用）: `DashedLine(start=[-2,0,0], end=[2,0,0])`  # 会导致 IndexError
   - 正确示例: `Line3D(start=[-2,0,0], end=[2,0,0], color=GRAY, thickness=0.02)`
   - 如果使用继承自 ThreeDScene，所有线条和箭头必须使用3D版本

请直接输出可执行的 Python 代码，不要包含任何解释。"""
                }
            ],
            temperature=0.3,
            max_tokens=6000,
            stream=True
        )

        generated_code = ""
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                generated_code += content
                if stream_callback:
                    stream_callback(content)

        generated_code = generated_code.strip()

        if generated_code.startswith('```python'):
            generated_code = generated_code[10:-3].strip()
        elif generated_code.startswith('```'):
            generated_code = generated_code[3:-3].strip()

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
            print(f"⚠️ {check_msg}，尝试修复...")
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
                is_complete, check_msg = check_code_completeness(generated_code)

        print(f"✅ Manim 代码生成完成")
        return {"generated_code": generated_code}
    except Exception as e:
        import traceback
        error_msg = f"生成代码失败: {str(e)}"

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

def execute_code(state: ManimState) -> ManimState:
    """执行生成的 Manim 代码，渲染视频"""
    print("3. 正在渲染动画视频（这可能需要较长时间）...")

    try:
        import re
        import glob
        import time
        from datetime import datetime
        from config import Config

        videos_dir = Config.VIDEOS_DIR

        if not os.path.exists(videos_dir):
            os.makedirs(videos_dir)

        user_prompt = state["user_prompt"]
        # 生成时间戳（在关键词提取之前，因为后面的代码需要用到）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 提取关键词：保留字母、数字和中文，但用于文件名时转换为拼音或简化
        keywords = re.sub(r'[^\w\u4e00-\u9fa5]+', '_', user_prompt)
        keywords = keywords[:15].strip('_')

        # 为了避免中文文件名导致问题，创建一个仅ASCII的安全文件名
        # 使用时间戳 + 短哈希确保唯一性
        import hashlib
        prompt_hash = hashlib.md5(keywords.encode('utf-8')).hexdigest()[:8]
        safe_filename = f"manim_{timestamp}_{prompt_hash}"

        if not keywords:
            keywords = "animation"
        target_filename = os.path.join(videos_dir, f"{safe_filename}.mp4")

        quality = state.get("render_quality", "medium")

        quality_flags = {
            'low': '-ql',
            'medium': '-qm',
            'high': '-qh',
            '4k': '-qk'
        }

        quality_flag = quality_flags.get(quality, '-qm')

        generated_code = state["generated_code"]

        # 提取 Scene 类名
        scene_class_match = re.search(r'class\s+(\w+)\s*\(\s*Scene\s*\)|class\s+(\w+)\s*\(\s*ThreeDScene\s*\)|class\s+(\w+)\s*\(\s*MovingCameraScene\s*\)', generated_code)
        if scene_class_match:
            scene_class_name = scene_class_match.group(1) or scene_class_match.group(2) or scene_class_match.group(3)
        else:
            scene_class_name = "AnimationScene"

        code_filename = os.path.join(videos_dir, f"scene_{timestamp}.py")

        with open(code_filename, 'w', encoding='utf-8') as f:
            f.write(generated_code)

        try:
            compile(generated_code, '<string>', 'exec')
        except SyntaxError as se:
            error_msg = f"生成的代码存在语法错误（第{se.lineno}行）: {se.msg}"
            print(f"✗ {error_msg}")
            return {"error": error_msg}

        print(f"🎬 开始渲染动画（可能需要 30 秒到 5 分钟）...")

        with manim_lock:
            # 清理缓存以避免潜在问题
            cache_dir = os.path.join(videos_dir, "media", "cache")
            if os.path.exists(cache_dir):
                import shutil
                try:
                    shutil.rmtree(cache_dir)
                except Exception:
                    pass

            # 记录所有现有文件的修改时间，用于检测新文件
            files_before_mtime = {}
            for f in glob.glob(os.path.join(videos_dir, "media/videos/**/*.mp4"), recursive=True):
                files_before_mtime[f] = os.path.getmtime(f)

            # 对于 manim -o 参数，使用不带扩展名的完整路径
            output_path_no_ext = os.path.splitext(target_filename)[0]

            cmd = [
                "manim",
                quality_flag,
                "-o", output_path_no_ext,
                code_filename,
                scene_class_name
            ]

            # 准备环境变量，确保 LaTeX 可用
            import shutil
            latex_path = shutil.which("latex")
            env = os.environ.copy()
            if latex_path and "/Library/TeX/texbin" not in env.get("PATH", ""):
                tex_bin = os.path.dirname(latex_path)
                env["PATH"] = f"{tex_bin}:{env.get('PATH', '')}"

            # 使用 communicate 直接获取所有输出，避免死锁
            # 设置超时：300秒（5分钟）- 复杂3D场景可能需要较长时间
            # 如果超时，可能是 Manim 死锁或 LaTeX 卡住
            process = subprocess.Popen(
                cmd,
                cwd=videos_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,  # 分别捕获 stdout 和 stderr
                text=True,
                env=env  # 传递修改后的环境变量
            )

            # 等待进程完成并获取所有输出，带超时保护
            try:
                stdout_data, stderr_data = process.communicate(timeout=300)
                returncode = process.returncode
            except subprocess.TimeoutExpired:
                process.kill()
                stdout_data, stderr_data = process.communicate()
                returncode = -1  # 自定义超时返回码

                error_msg = "Manim 渲染超时（>300秒），可能是死锁或 LaTeX 卡住"
                print(f"⏱️ {error_msg}")
                print(f"   已终止进程，尝试使用已生成的部分视频文件...")

                # 即使超时，也尝试找已生成的视频
                import time as time_module
                time_module.sleep(1)  # 给文件系统一点时间

            # 打印 stderr 错误输出（如果有）
            if stderr_data:
                # 如果返回码非0，打印完整stderr用于调试
                if returncode != 0:
                    for line in stderr_data.split('\n'):
                        if line.strip():
                            print(f"  {line}")
                else:
                    # 正常情况下只打印包含关键字的行
                    for line in stderr_data.split('\n'):
                        if line.strip() and ("ERROR" in line or "CRITICAL" in line or "Exception" in line or "Traceback" in line):
                            print(f"  {line.strip()}")

            if returncode != 0 and stdout_data:
                # 打印最后 50 行作为错误上下文
                error_lines = stdout_data.split('\n')[-50:]
                for line in error_lines:
                    print(f"  {line}")
                # 注意：即使返回码非0，也可能视频已生成，继续尝试查找文件

            time.sleep(2)

            # 查找所有新生成的 MP4 文件（使用修改时间判断）
            # 首先使用最可靠的方法：查找最新的 scene 目录
            scene_dirs = glob.glob(os.path.join(videos_dir, "media/videos/scene_*"), recursive=False)

            # 首先检查输出目标位置是否已存在（通过 -o 参数指定的文件）
            # Manim 应该直接输出到这里
            if os.path.exists(target_filename):
                file_size = os.path.getsize(target_filename)
                # 只有文件大小大于 1KB 才认为是有效的（避免空文件）
                if file_size > 1024:
                    print(f"✅ 视频渲染成功！")
                    return {"video_path": target_filename}

            if scene_dirs:
                # 按修改时间排序，选择最新的目录
                scene_dirs.sort(key=os.path.getmtime, reverse=True)
                latest_scene_dir = scene_dirs[0]

                # 在该目录中查找所有 .mp4 文件
                scene_videos = glob.glob(os.path.join(latest_scene_dir, "**/*.mp4"), recursive=True)

                # 过滤掉 partial_movie_files 目录中的文件
                final_videos = [f for f in scene_videos if "partial_movie_files" not in f]

                if final_videos:
                    latest_video = final_videos[0]

                    # 移动视频到目标位置
                    final_video_path = target_filename
                    import shutil
                    shutil.move(latest_video, final_video_path)

                    print(f"✅ 视频渲染成功！")
                    return {"video_path": final_video_path}

            # 如果上面的方法失败了，回退到原来的修改时间检测方法
            all_files_after = glob.glob(os.path.join(videos_dir, "media/videos/**/*.mp4"), recursive=True)

            new_files = []
            current_time = time.time()

            # 使用更宽松的时间窗口（600秒 = 10分钟）
            time_window = 600

            for f in all_files_after:
                # 过滤掉 partial_movie_files 目录中的文件（这些是中间文件，不是最终视频）
                if "partial_movie_files" in f:
                    continue

                mtime = os.path.getmtime(f)
                time_diff = current_time - mtime

                is_new = f not in files_before_mtime
                is_recent = time_diff < time_window

                if is_new and is_recent:
                    new_files.append(f)

            # 如果找到新文件，选择最新的一个
            if new_files:
                # 按修改时间排序，选择最新的
                new_files.sort(key=os.path.getmtime, reverse=True)
                new_video = new_files[0]

                # 移动视频到目标位置
                final_video_path = target_filename
                import shutil
                shutil.move(new_video, final_video_path)

                print(f"✅ 视频渲染成功！")
                return {"video_path": final_video_path}

            if os.path.exists(target_filename):
                print(f"✅ 视频渲染成功！")
                return {"video_path": target_filename}

            # 如果返回码非 0 且没有找到视频，返回错误
            if returncode != 0:
                error_msg = f"Manim 渲染失败（返回码 {returncode}）且未找到视频文件"
                print(f"✗ {error_msg}")
                return {"error": error_msg}

            # 最后的备用方案：查找最新的 scene 目录中的视频文件
            scene_dirs = glob.glob(os.path.join(videos_dir, "media/videos/scene_*"), recursive=False)

            if scene_dirs:
                # 按修改时间排序，选择最新的目录
                scene_dirs.sort(key=os.path.getmtime, reverse=True)
                latest_scene_dir = scene_dirs[0]

                # 在该目录中查找所有 .mp4 文件
                scene_videos = glob.glob(os.path.join(latest_scene_dir, "**/*.mp4"), recursive=True)

                # 首先检查输出目标位置是否已存在（通过 -o 参数指定的文件）
                # Manim 应该直接输出到这里
                if os.path.exists(target_filename):
                    file_size = os.path.getsize(target_filename)
                    # 只有文件大小大于 1KB 才认为是有效的（避免空文件）
                    if file_size > 1024:
                        print(f"✅ 视频渲染成功！")
                        return {"video_path": target_filename}

                # 过滤掉 partial_movie_files 目录中的文件
                final_videos = [f for f in scene_videos if "partial_movie_files" not in f]

                if final_videos:
                    latest_video = final_videos[0]

                    # 移动视频到目标位置
                    final_video_path = target_filename
                    import shutil
                    shutil.move(latest_video, final_video_path)

                    print(f"✅ 视频渲染成功！")
                    return {"video_path": final_video_path}

            print(f"✗ 视频生成失败，没有找到新文件")
            return {"error": "视频生成失败，渲染后未找到视频文件"}

    except Exception as e:
        import traceback
        error_msg = f"执行代码失败: {str(e)}"
        print(f"✗ {error_msg}")
        traceback.print_exc()
        return {"error": error_msg}

def save_video(state: ManimState) -> ManimState:
    """验证并保存视频信息"""
    print("4. 正在验证视频保存...")

    if state.get("error"):
        return state

    try:
        video_path = state["video_path"]

        if os.path.exists(video_path):
            size = os.path.getsize(video_path)
            duration_mb = size / (1024 * 1024)
            print(f"视频大小: {duration_mb:.2f} MB")
            return {"video_size": size}
        else:
            return {"error": "视频保存失败"}
    except Exception as e:
        import traceback
        error_msg = f"验证视频失败: {str(e)}"
        print(f"✗ {error_msg}")
        traceback.print_exc()
        return {"error": error_msg}

def create_graph():
    """创建并编译工作流图"""
    workflow = StateGraph(ManimState)

    workflow.add_node("refine_prompt", refine_prompt)
    workflow.add_node("generate_code", generate_code)
    workflow.add_node("execute_code", execute_code)
    workflow.add_node("save_video", save_video)

    workflow.set_entry_point("refine_prompt")

    workflow.add_edge("refine_prompt", "generate_code")
    workflow.add_edge("generate_code", "execute_code")
    workflow.add_edge("execute_code", "save_video")
    workflow.add_edge("save_video", END)

    return workflow.compile()

def generate_single_animation(description: str, quality: str = "medium") -> dict:
    """
    生成单个动画视频(供外部调用)

    参数:
        description: 动画描述
        quality: 渲染质量 (low/medium/high/4k)

    返回:
        dict: {
            'success': bool,
            'video_path': str,
            'video_size': int,
            'relative_path': str,
            'generated_code': str,
            'error': str
        }
    """
    try:
        graph = create_graph()

        initial_state = {
            "user_prompt": description,
            "refined_prompt": "",
            "generated_code": "",
            "video_path": "",
            "video_size": 0,
            "render_quality": quality,
            "error": ""
        }

        result = graph.invoke(initial_state)

        if result.get("error"):
            print(f"❌ 生成失败: {result['error']}")
            return {
                'success': False,
                'error': result['error']
            }

        video_path = result['video_path']
        video_size = result['video_size']

        filename = os.path.basename(video_path)
        relative_path = f"../videos/{filename}"

        print(f"✅ 生成成功:")
        print(f"  - 完整路径: {video_path}")
        print(f"  - 相对路径: {relative_path}")
        print(f"  - 文件大小: {video_size} 字节")

        return {
            'success': True,
            'video_path': video_path,
            'video_size': video_size,
            'relative_path': relative_path,
            'generated_code': result.get('generated_code', ''),
            'error': None
        }

    except Exception as e:
        import traceback
        error_msg = f"工作流异常: {str(e)}"
        print(f"❌ {error_msg}")
        traceback.print_exc()
        return {
            'success': False,
            'error': error_msg
        }

def main():
    """主函数, 处理用户输入并运行工作流"""
    if len(sys.argv) > 1:
        user_prompt = ' '.join(sys.argv[1:])
        # 如果第二个参数是质量选项，则从命令行参数中提取
        if len(sys.argv) > 2 and sys.argv[2] in ['low', 'medium', 'high', '4k']:
            quality = sys.argv[2]
            # 从 user_prompt 中移除质量参数
            parts = user_prompt.split()
            if parts[-1] == quality:
                user_prompt = ' '.join(parts[:-1])
        else:
            quality = "medium"
    else:
        user_prompt = input("请输入你的动画需求：")
        quality = input("请选择渲染质量 (low/medium/high/4k) [默认: medium]: ").strip() or "medium"

    print(f"\n{'='*60}")
    print(f"🎬 Manim 动画生成智能体")
    print(f"{'='*60}\n")

    try:
        graph = create_graph()

        result = graph.invoke({
            "user_prompt": user_prompt,
            "refined_prompt": "",
            "generated_code": "",
            "video_path": "",
            "video_size": 0,
            "render_quality": quality,
            "error": ""
        })

        print(f"\n{'='*60}")
        if result.get("error"):
            print(f"❌ 错误: {result['error']}")
            print(f"{'='*60}\n")
            sys.exit(1)
        else:
            print(f"✅ 动画生成成功！")
            print(f"📁 保存路径: {result['video_path']}")
            print(f"📏 文件大小: {result['video_size'] / (1024*1024):.2f} MB")
            print(f"🎥 渲染质量: {result.get('render_quality', 'medium')}")
            print(f"{'='*60}\n")

            abs_path = os.path.abspath(result['video_path'])
            print(f"📍 视频绝对路径: {abs_path}\n")

    except Exception as e:
        print(f"❌ 工作流运行失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
