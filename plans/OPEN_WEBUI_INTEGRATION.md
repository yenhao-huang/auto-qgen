# Open WebUI 集成指南

本文档说明如何将 Excel 数据增强服务集成到 Open WebUI。

## 概述

通过 Open WebUI Pipeline,您可以在 Open WebUI 界面中直接上传 Excel 文件并进行数据增强处理,无需手动调用 API。

## 前置要求

1. **已安装 Open WebUI**
   - 官方文档: https://docs.openwebui.com/
   - 安装命令: `pip install open-webui`

2. **FastAPI 服务正在运行**
   - 确保本地 FastAPI 服务已启动: `python app.py`
   - 默认地址: http://localhost:8000

3. **Python 依赖**
   ```bash
   pip install requests pydantic
   ```

## 安装步骤

### 方法 1: 通过 Open WebUI 管理界面安装 (推荐)

1. **访问 Open WebUI 管理界面**
   - 打开浏览器访问: http://localhost:8080 (或您的 Open WebUI 地址)
   - 登录管理员账户
   - 開啟: `open-webui serve`

2. **进入 Pipelines 管理**
   - 点击右上角的设置图标
   - 选择 "Admin Panel" (管理面板)
   - 点击左侧菜单的 "Pipelines"

3. **添加新 Pipeline**
   - 点击 "+" 或 "Add Pipeline" 按钮
   - 将 `open_webui_pipeline.py` 的内容复制粘贴到编辑器中
   - 点击 "Save" 保存

4. **配置 Pipeline**
   - 找到刚添加的 "Excel Data Augmenter" Pipeline
   - 点击设置图标进行配置
   - 配置以下参数:

   **API 服务配置:**
   - `API_BASE_URL`: FastAPI 服务地址 (默认: http://localhost:8000)

   **Parser LLM 配置:**
   - `PARSER_URL`: Parser LLM 服务 URL
   - `PARSER_MODEL`: 模型名称 (如: z-ai/glm-4.5-air:free)
   - `PARSER_API_KEY`: API Key
   - `PARSER_USE_OPENROUTER`: 是否使用 OpenRouter
   - `PARSER_MAX_RETRIES`: 最大重试次数

   **Augmenter LLM 配置:**
   - `AUGMENTER_URL`: Augmenter LLM 服务 URL
   - `AUGMENTER_MODEL`: 模型名称 (如: openai/gpt-oss-20b:free)
   - `AUGMENTER_API_KEY`: API Key
   - `AUGMENTER_USE_OPENROUTER`: 是否使用 OpenRouter
   - `AUGMENTER_MAX_RETRIES`: 最大重试次数
   - `AUGMENTER_PROMPT_NAME`: Prompt 名称 (默认: default)

   **其他配置:**
   - `SKIP_PARSER`: 是否跳过 Parser 步骤
   - `ENABLE_DEBUG`: 是否启用调试模式

5. **启用 Pipeline**
   - 确保 Pipeline 状态为 "Enabled" (启用)

### 方法 2: 通过文件系统安装

1. **找到 Open WebUI 的 pipelines 目录**
   ```bash
   # 通常在以下位置之一:
   ~/.open-webui/pipelines/
   # 或
   ./open-webui/pipelines/
   ```

2. **复制 Pipeline 文件**
   ```bash
   cp open_webui_pipeline.py ~/.open-webui/pipelines/
   ```

3. **重启 Open WebUI**
   ```bash
   # 停止当前服务 (Ctrl+C)
   # 然后重新启动
   open-webui serve
   ```

## 使用方法

### 1. 启动服务

确保 FastAPI 服务正在运行:

```bash
cd c:\Users\Administrator\Desktop\llm_for_evaluator-main\augmenter
python app.py
```

### 2. 在 Open WebUI 中使用

1. **打开聊天界面**
   - 访问 Open WebUI: http://localhost:3000

2. **选择 Pipeline**
   - 在模型选择下拉菜单中,找到 "Excel Data Augmenter"
   - 点击选择该 Pipeline

3. **上传 Excel 文件**
   - 点击消息输入框旁边的附件图标 📎
   - 选择您的 Excel 文件 (.xlsx 或 .xls)
   - 发送消息

4. **等待处理**
   - Pipeline 会自动调用 FastAPI 服务处理文件
   - 处理完成后会显示结果摘要和下载链接

### 3. 查看结果

处理成功后,您会看到类似以下的响应:

```
### 数据增强完成 ✅

**文件名**: 表12-1.xlsx
**处理状态**: 成功
**总记录数**: 100

#### 输出文件:
- **解析数据**: `results/api_20250115_143022/parsed_data.json`
- **增强查询**: `results/api_20250115_143022/augmented_queries.json`

您可以通过以下命令下载结果文件:
...
```

## 高级配置

### 环境变量配置

您可以通过环境变量覆盖 Pipeline 的默认配置:

```bash
# .env 文件
OPENWEBUI_PIPELINE_API_BASE_URL=http://localhost:8000
OPENWEBUI_PIPELINE_PARSER_API_KEY=your_parser_api_key
OPENWEBUI_PIPELINE_AUGMENTER_API_KEY=your_augmenter_api_key
```

### 修改 Pipeline 代码

如果需要自定义 Pipeline 行为,可以编辑 `open_webui_pipeline.py`:

```python
class Pipeline:
    def __init__(self):
        self.type = "manifold"
        self.id = "excel_data_augmenter"
        self.name = "Excel Data Augmenter"
        # 添加自定义初始化逻辑
```

### 调试模式

启用调试模式以查看详细日志:

1. 在 Pipeline 配置中设置 `ENABLE_DEBUG = True`
2. 查看 Open WebUI 服务器日志
3. 查看 FastAPI 服务器日志

## 故障排除

### 问题 1: Pipeline 未显示

**解决方案:**
- 检查 Pipeline 文件是否正确保存
- 重启 Open WebUI 服务
- 检查浏览器控制台是否有错误

### 问题 2: 调用 API 失败

**解决方案:**
- 确认 FastAPI 服务正在运行: `curl http://localhost:8000/api/v1/health`
- 检查 `API_BASE_URL` 配置是否正确
- 查看 FastAPI 服务日志

### 问题 3: 文件上传失败

**解决方案:**
- 确认文件格式为 .xlsx 或 .xls
- 检查文件大小是否超过限制
- 确认文件路径权限正确

### 问题 4: API Key 错误

**解决方案:**
- 检查 `PARSER_API_KEY` 和 `AUGMENTER_API_KEY` 配置
- 确认 API Key 有效且未过期
- 检查服务 URL 是否正确

## API 参考

### FastAPI 服务端点

1. **数据增强 API**
   - 端点: `POST /api/v1/data_augment`
   - 参数: Excel 文件 + LLM 配置
   - 返回: 处理结果和输出路径

2. **下载结果**
   - 端点: `GET /api/v1/download/{file_type}/{timestamp}`
   - 参数: file_type (parsed/augmented), timestamp
   - 返回: JSON 文件

3. **健康检查**
   - 端点: `GET /api/v1/health`
   - 返回: 服务状态

## 安全建议

1. **API Key 管理**
   - 不要在代码中硬编码 API Key
   - 使用环境变量或配置文件存储敏感信息
   - 定期轮换 API Key

2. **访问控制**
   - 限制 FastAPI 服务的访问 IP
   - 使用防火墙规则保护服务端口
   - 考虑添加 API 认证

3. **文件安全**
   - 验证上传文件类型和大小
   - 定期清理临时文件
   - 设置适当的文件权限

## 性能优化

1. **并发处理**
   - FastAPI 支持异步处理
   - 可以同时处理多个请求

2. **缓存策略**
   - 对相同文件的重复请求可以启用缓存
   - 设置合理的缓存过期时间

3. **资源限制**
   - 设置最大文件大小限制
   - 限制并发请求数量
   - 配置超时时间

## 相关资源

- **Open WebUI 官方文档**: https://docs.openwebui.com/
- **FastAPI 文档**: https://fastapi.tiangolo.com/
- **Pipeline 开发指南**: https://docs.openwebui.com/pipelines/

## 支持

如遇到问题,请:
1. 检查日志输出
2. 查看本文档的故障排除部分
3. 提交 Issue 到项目仓库

---

**版本**: 1.0.0
**更新日期**: 2025-01-15
