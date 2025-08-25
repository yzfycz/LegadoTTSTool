# LegadoTTSTool - 项目开发文档

## 项目概述

### 项目简介
LegadoTTSTool 是一个专为盲人用户设计的语音合成角色管理工具，主要用于从各种TTS（文本转语音）API获取语音角色信息，并导出为阅读软件（Legado）可导入的JSON格式。

### 技术栈
- **编程语言**: Python 3.8+
- **GUI框架**: wxPython
- **网络请求**: requests, gradio_client
- **配置文件**: JSON
- **无障碍支持**: wxPython原生无障碍API

### 核心特性
- 完全支持键盘操作，100%无死角操作体验
- 支持多种TTS提供商管理
- 动态界面生成，根据不同提供商显示不同配置选项
- 局域网自动搜索TTS服务器
- 实时语音试听功能
- 批量角色导出功能

### 开发目标
1. **无障碍优先**: 所有功能都必须支持键盘操作和屏幕阅读器
2. **简单易用**: 界面简洁，操作流程清晰
3. **稳定可靠**: 网络请求和错误处理完善
4. **可扩展性**: 支持多种TTS服务提供商

### 目标用户
- 盲人用户或依赖屏幕阅读器的用户
- 需要管理TTS语音角色的用户
- 使用Legado阅读软件的用户

## 技术架构设计

### 系统架构图
```
┌─────────────────────────────────────────────────────────────┐
│                        用户界面层                           │
├─────────────────────────────────────────────────────────────┤
│  主界面  │  提供商管理  │  配置界面  │  导出界面              │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                        业务逻辑层                           │
├─────────────────────────────────────────────────────────────┤
│ ProviderManager │ TTSClient │ NetworkScanner │ JSONExporter │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                        数据存储层                           │
├─────────────────────────────────────────────────────────────┤
│   providers.json   │   settings.json   │   导出文件         │
└─────────────────────────────────────────────────────────────┘
```

### 分层架构
The project follows a clean 3-layer architecture:

1. **UI Layer** (`ui/`): wxPython-based interface with accessibility features
   - `main_frame.py`: Main application window and event coordination
   - `provider_dialog.py`: Provider management interface
   - `config_dialog.py`: Dynamic configuration form generation

2. **Business Logic Layer** (`core/`): Modular core components
   - `provider_manager.py`: CRUD operations for TTS providers
   - `tts_client.py`: TTS service communication and API handling
   - `network_scanner.py`: LAN discovery and server verification
   - `json_exporter.py`: Legado-compatible JSON export generation

3. **Data Storage Layer** (`config/`): JSON-based configuration
   - `providers.json`: Provider configurations with auto-creation
   - Settings and export files

### 事件驱动线程模型
- All network operations run in background threads using `threading.Thread`
- Custom wxPython events (`RoleUpdateEvent`, `ProviderUpdateEvent`) for thread-safe UI updates
- Progress indicators and status feedback via event posting

## 项目结构

```
LegadoTTSTool/
├── main.py                 # 主程序入口
├── config/                 # 配置文件目录
│   ├── providers.json      # 提供商配置
│   └── settings.json       # 程序设置
├── ui/                     # 界面模块
│   ├── main_frame.py       # 主界面
│   ├── provider_dialog.py  # 提供商管理对话框
│   └── config_dialog.py    # 提供商配置对话框
├── core/                   # 核心功能模块
│   ├── provider_manager.py # 提供商管理器
│   ├── network_scanner.py  # 网络扫描器
│   ├── tts_client.py       # TTS 客户端
│   └── json_exporter.py    # JSON 导出器
├── utils/                  # 工具模块
│   ├── accessibility.py    # 无障碍工具
│   └── file_utils.py       # 文件操作工具
├── requirements.txt        # Python 依赖
└── README.md              # 项目说明文档
```

## 核心组件

### ProviderManager
- Sophisticated CRUD system with UUID generation using `uuid.uuid4()`
- Flexible name matching for provider selection
- Automatic configuration validation and timestamp management
- Handles provider state (enabled/disabled) and usage tracking

### TTSClient
- Handles complex Gradio API interactions for index TTS services
- Implements Unicode encoding fixes via stdout redirection
- Supports voice role retrieval and real-time text-to-speech synthesis
- Comprehensive error handling for network and API failures

### NetworkScanner
- Multi-threaded LAN discovery scanning common IP ranges
- Verifies TTS servers via Gradio API endpoint testing
- Supports both index TTS and other service type detection
- Concurrent scanning with result aggregation

### JSONExporter
- Generates Legado-compatible JSON exports with proper structure
- Creates unique timestamp-based IDs with collision avoidance
- Supports batch export with configurable parameters (speed, volume)
- Includes proper content type and concurrent rate settings

## 用户界面设计

### 主界面布局
```
┌─────────────────────────────────────────────────────────────┐
│ 语音合成角色导出工具                                          │
├─────────────────────────────────────────────────────────────┤
│ [方案选择组合框 ▼] [刷新按钮]                               │
│                                                             │
│ 语音角色：                                                  │
│ ☑ 忧伤女声.pt                                               │
│ ☐ jok老师.pt                                                │
│ ☑ 温柔的小女生.pt                                           │
│ ...                                                        │
│                                                             │
│ 语音试听文本:                                              │
│ [这是一段默认的试听文本，用户可以编辑这个文本来...]          │
│                                                             │
│ 语速: [1.0]  音量: [1.0]                                   │
│                                                             │
│ [全选] [反选] [导出为JSON]                                 │
├─────────────────────────────────────────────────────────────┤
│ 操作(C) │ 帮助(H) │ 关于(A) │ 退出(E)                        │
└─────────────────────────────────────────────────────────────┘
```

### 控件说明

#### 方案选择组合框
- **功能**: 选择已配置的TTS提供商
- **显示格式**: `自定义名称 - 提供商类型`
- **快捷键**: Alt+S

#### 角色列表
- **类型**: CheckListBox（复选框列表）
- **状态显示**: 获取时显示"正在获取音色..."
- **过滤功能**: 自动过滤"使用参考音频"

#### 参数控制
- **语速**: 文本框输入，范围 0.5-2.0，支持回车确认
- **音量**: 文本框输入，范围 0.5-2.0，支持回车确认
- **验证**: 自动验证输入范围，无效时恢复默认值

## 无障碍设计

### 键盘导航
- **Tab 键**: 正向导航
- **Shift+Tab**: 反向导航
- **空格键**: 选中/取消选中
- **回车键**: 确认/试听
- **Esc 键**: 取消/关闭

### 全局快捷键
- **Alt+C**: 打开操作菜单
- **Alt+S**: 聚焦方案选择
- **Alt+R**: 刷新角色列表
- **Alt+A**: 全选角色
- **Alt+D**: 反选角色
- **Alt+E**: 导出JSON

### 屏幕阅读器支持
- **完整标签**: 所有控件都有清晰的无障碍名称
- **状态提示**: 操作状态实时反馈
- **焦点管理**: 清晰的焦点指示和逻辑顺序

## 关键实现模式

### 无障碍实现
- **100% 键盘导航**: All controls support Tab/Shift+Tab navigation
- **屏幕阅读器支持**: Complete labeling and custom accessibility utilities
- **焦点管理**: Logical focus order and visual indicators
- **状态反馈**: Real-time status updates for all operations

### Unicode 处理
The TTSClient implements a unique solution for gradio_client encoding issues:
```python
# Redirect stdout to avoid Unicode encoding problems
old_stdout = sys.stdout
sys.stdout = io.StringIO()
try:
    # Gradio API calls
    result = client.predict(api_name="/change_choices")
finally:
    sys.stdout = old_stdout
```

### 动态UI生成
Configuration interfaces adapt based on provider type:
- Different form fields for different TTS services
- Real-time validation of user input
- Automatic field population and state management

## 数据结构设计

### 提供商配置结构
```json
{
  "providers": [
    {
      "id": "uuid-string",
      "type": "index_tts",
      "custom_name": "我的TTS",
      "enabled": true,
      "server_address": "127.0.0.1",
      "web_port": 7860,
      "synth_port": 9880,
      "preview_text": "试听文本",
      "created_time": "2024-01-01T00:00:00Z",
      "last_used": null
    }
  ],
  "version": "1.0.0",
  "last_updated": "2024-01-01T00:00:00Z"
}
```

### 导出数据结构
```json
[
  {
    "concurrentRate": "0",
    "contentType": "audio/wav",
    "enabledCookieJar": false,
    "id": 1640995200000,
    "lastUpdateTime": 1640995200000,
    "name": "角色名_提供商名",
    "url": "http://server:port/?text={{speakText}}&speaker=role&speed=1.0&volume=1.0"
  }
]
```

### ID 生成策略
```python
def generate_unique_id(existing_ids=None):
    """生成唯一的正数时间戳ID"""
    timestamp = int(time.time() * 1000)
    
    # 确保唯一性
    if existing_ids:
        while timestamp in existing_ids:
            timestamp += 1
    
    return timestamp
```

## 配置管理

### 自动创建
The application automatically creates `config/providers.json` on first run with a default index TTS provider configuration.

### 首次运行配置
```json
{
  "providers": [
    {
      "id": "56bacf8b-82cc-4aa0-9999-9ad1114b435d",
      "type": "index_tts",
      "custom_name": "我的",
      "enabled": true,
      "server_address": "127.0.0.1",
      "web_port": 7860,
      "synth_port": 9880,
      "preview_text": "这是一段默认的试听文本，用于测试语音合成效果。"
    }
  ],
  "version": "1.0.0",
  "last_updated": "2024-01-01T00:00:00Z"
}
```

## 错误处理机制

### 网络操作
- All network requests include timeout handling
- Comprehensive exception handling for connection failures
- User-friendly error messages via status events
- Retry mechanisms for critical operations

### 线程安全
- Custom wxPython events ensure thread-safe UI updates
- Proper resource cleanup in `finally` blocks
- Prevention of multiple concurrent operations on same resources

### 用户友好提示
- 网络连接失败：检查服务器配置和网络连接
- API 调用失败：验证服务器状态和端口配置
- 数据解析失败：检查 API 兼容性

### 程序退出处理
```python
def OnExit(self):
    """应用程序退出时的清理工作"""
    try:
        # 清理资源
        if hasattr(self, 'provider_manager'):
            self.provider_manager = None
        if hasattr(self, 'frame'):
            self.frame = None
    except Exception as e:
        print(f"退出清理失败: {e}")
    
    return super().OnExit()
```

## 开发指南

### 代码规范
- **命名规范**: 使用有意义的英文变量名和函数名
- **注释规范**: 关键功能必须有中文注释
- **异常处理**: 所有可能失败的操作都必须有异常处理
- **无障碍**: 所有新增功能都必须支持无障碍操作

### 调试技巧
```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 捕获异常并记录
try:
    # 可能失败的代码
except Exception as e:
    logging.error(f"操作失败: {e}")
    import traceback
    traceback.print_exc()
```

### 测试方法
1. **单元测试**: 测试各个模块的核心功能
2. **集成测试**: 测试模块间的协作
3. **无障碍测试**: 使用屏幕阅读器验证操作流程
4. **用户测试**: 邀请目标用户进行实际使用测试

## 安装和部署

### 环境要求
- Python 3.8+
- Windows 10/11
- 支持的TTS服务（index TTS）
- Screen reader support (NVDA, JAWS recommended)

### 依赖库
```
wxPython==4.2.1
requests==2.31.0
gradio_client==0.8.1
pygame==2.5.2
uuid==1.30
```

### 安装步骤
1. **克隆仓库**
   ```bash
   git clone https://github.com/yzfycz/LegadoTTSTool.git
   cd LegadoTTSTool
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **运行程序**
   ```bash
   python main.py
   ```

### 开发命令
```bash
# Production entry
python main.py

# Development launcher (with dependency checking)
python run.py
```

## 常见问题解决

### 1. 程序启动失败
**问题**: Python模块导入错误
**解决**: 
```bash
pip install -r requirements.txt
```

### 2. 网络连接失败
**问题**: 无法连接到TTS服务器
**解决**:
- 检查服务器地址和端口
- 确认TTS服务正在运行
- 验证网络连通性

### 3. 角色获取失败
**问题**: API返回格式错误
**解决**:
- 确认使用的是index TTS服务
- 检查Gradio API版本兼容性
- 查看服务器日志

### 4. 无障碍功能异常
**问题**: 屏幕阅读器无法正确读取控件
**解决**:
- 确认使用支持的屏幕阅读器（NVDA、JAWS）
- 检查wxPython版本兼容性
- 重启屏幕阅读器

### 5. 程序退出崩溃
**问题**: 退出时出现RecursionError
**解决**:
- 使用最新版本的程序
- 检查是否有其他程序占用端口
- 确认系统资源充足

## 版本历史

### v1.0.0 (2024-08-24)
- **初始版本发布**
- **基础功能**: 提供商管理、角色获取、JSON导出
- **无障碍支持**: 完整的键盘导航和屏幕阅读器支持
- **网络功能**: 局域网扫描和服务器验证

### 修复版本 (2024-08-25)
- **修复API调用问题**: 解决Gradio客户端编码问题
- **修复界面更新**: 提供商修改后立即生效
- **修复退出错误**: 解决程序退出时的递归错误
- **优化用户体验**: 状态显示和智能过滤

## 贡献指南

### 开发环境设置
1. Fork本仓库
2. 创建特性分支: `git checkout -b feature/新功能`
3. 提交更改: `git commit -m '添加新功能'`
4. 推送到分支: `git push origin feature/新功能`
5. 打开Pull Request

### 代码审查要点
- 无障碍功能完整性
- 错误处理机制
- 代码风格一致性
- 中文注释完整性

## 许可证

本项目采用MIT许可证 - 详见LICENSE文件。

## 联系方式

- **GitHub Issues**: [提交问题](https://github.com/yzfycz/LegadoTTSTool/issues)
- **Email**: yzfycz@example.com

## 致谢

- index TTS服务提供商
- wxPython GUI框架
- Legado阅读软件
- 所有贡献者和测试用户

---

**最后更新**: 2024-08-25  
**版本**: 1.0.0  
**维护者**: yzfycz

---

## Claude Code 指导

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

### 重要提醒
- 代码部分用英文，其他用中文提示
- 除非绝对必要，否则不要创建文件
- 优先编辑现有文件而不是创建新文件
- 不要主动创建文档文件（*.md），除非用户明确要求

### 常见问题和解决方案

#### Unicode 编码问题
The TTSClient includes specific handling for gradio_client Unicode issues via stdout redirection.

#### 线程UI更新
Use custom wxPython events and `wx.PostEvent()` for thread-safe UI updates from background threads.

#### 提供商配置更改
Provider modifications immediately update the UI via event system - no application restart required.

#### 程序退出清理
The application includes proper resource cleanup to prevent RecursionError on exit.