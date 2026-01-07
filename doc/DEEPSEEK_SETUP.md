# DeepSeek API 配置指南

## 如何获取 DeepSeek API Key

1. **访问 DeepSeek 平台**
   前往 [https://platform.deepseek.com/](https://platform.deepseek.com/)

2. **注册/登录账户**
   - 如果还没有账户，点击注册创建新账户
   - 使用手机号或邮箱登录

3. **获取 API Key**
   - 登录后进入控制台
   - 找到 "API Keys" 或 "密钥管理" 页面
   - 点击 "创建新的 API Key"
   - 复制生成的 API Key

4. **配置项目**
   - 打开项目根目录下的 `.env` 文件
   - 将 `DEEPSEEK_API_KEY=your_deepseek_api_key_here` 替换为：
     ```
     DEEPSEEK_API_KEY=你的实际API密钥
     ```
   - 保存文件

5. **重启服务器**
   - 按 Ctrl+C 停止当前运行的服务器
   - 重新运行：`python app.py`

## DeepSeek API 优势

- ✅ **性价比高**：DeepSeek 提供极具竞争力的价格
- ✅ **免费额度**：新用户通常有免费试用额度
- ✅ **代码能力强**：特别擅长代码生成和理解
- ✅ **兼容 OpenAI API**：使用标准的 OpenAI 接口，集成简单

## 价格参考

当前 DeepSeek 的定价（具体以官网为准）：
- DeepSeek-Chat: ¥1 / 百万 tokens（输入）
- 非常适合代码生成场景

## 测试配置

配置完成后，访问 http://localhost:5001
在输入框中输入绘图需求，例如：
- 绘制一个正弦波图形
- 生成柱状图显示销售数据
- 创建散点图展示相关性分析

如果配置正确，你应该能看到成功生成的图表！
