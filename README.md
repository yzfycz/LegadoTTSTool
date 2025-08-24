# LegadoTTSTool

一个专为盲人用户设计的语音合成角色管理工具，用于从各种TTS API获取语音角色信息，并导出为阅读软件（Legado）可导入的JSON格式。

## ✨ 特性

- 🎯 **完全无障碍**: 100%支持键盘操作，专为盲人用户优化
- 🔧 **提供商管理**: 支持多种TTS提供商的配置和管理
- 🌐 **局域网搜索**: 自动发现局域网内的index TTS服务器
- 🎵 **实时试听**: 支持角色试听和参数调节
- 📤 **批量导出**: 一键导出为Legado兼容的JSON格式
- ⚙️ **动态界面**: 根据不同提供商动态生成配置界面

## 🚀 快速开始

### 安装要求

- Python 3.8+
- Windows 10/11
- 支持的TTS服务（如index TTS）

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
   
   或者使用测试启动脚本：
   ```bash
   python run.py
   ```

### 依赖库

- wxPython - GUI框架
- requests - 网络请求
- gradio_client - Gradio API客户端

## 📖 使用说明

### 主界面操作

- **Alt+C**: 打开操作菜单
- **Alt+S**: 聚焦方案选择
- **Alt+R**: 刷新角色列表
- **空格键**: 选中/取消选中角色
- **回车键**: 试听选中角色
- **Alt+A**: 全选角色
- **Alt+D**: 反选角色
- **Alt+E**: 导出JSON

### 提供商配置

1. 按 `Alt+C` 打开操作菜单
2. 选择"提供商管理"
3. 点击"新建"配置新的TTS提供商
4. 支持局域网自动搜索服务器

### 导出格式

程序会生成Legado阅读软件兼容的JSON格式，包含以下字段：
- `name`: 角色名称
- `url`: TTS服务地址
- `contentType`: 音频格式
- `concurrentRate`: 并发率

## 🏗️ 项目结构

```
LegadoTTSTool/
├── main.py                 # 主程序入口
├── run.py                  # 测试启动脚本
├── config/                 # 配置文件目录
│   └── providers.json      # 提供商配置
├── ui/                     # 界面模块
│   ├── main_frame.py       # 主界面
│   ├── provider_dialog.py  # 提供商管理对话框
│   └── config_dialog.py    # 提供商配置对话框
├── core/                   # 核心功能模块
│   ├── provider_manager.py # 提供商管理器
│   ├── network_scanner.py  # 网络扫描器
│   ├── tts_client.py       # TTS客户端
│   └── json_exporter.py    # JSON导出器
├── utils/                  # 工具模块
│   ├── accessibility.py    # 无障碍工具
│   └── file_utils.py       # 文件操作工具
├── requirements.txt        # Python依赖
├── .gitignore             # Git忽略文件
└── README.md              # 项目说明文档
```

## 📊 开发状态

### ✅ 已完成功能

- **核心架构**
  - 模块化代码结构
  - 完整的异常处理
  - 配置文件管理
  
- **用户界面**
  - 主界面框架
  - 提供商管理对话框
  - 动态配置界面
  - 菜单系统
  
- **功能模块**
  - 提供商管理器
  - 网络扫描器
  - TTS客户端
  - JSON导出器
  
- **无障碍支持**
  - 键盘导航
  - 屏幕阅读器支持
  - 高对比度模式
  
- **index TTS支持**
  - 角色列表获取
  - 语音试听
  - 局域网搜索
  
### 🔄 正在开发

- **界面完善**
  - 焦点管理优化
  - 控件标签完善
  - 错误处理优化
  
- **功能测试**
  - 单元测试
  - 集成测试
  - 无障碍测试
  
- **文档完善**
  - 用户手册
  - 开发文档
  - API文档

## 🎯 支持的TTS提供商

### index TTS
- 自动局域网发现
- 支持角色列表获取
- 实时语音试听
- 批量角色导出

### 计划支持
- [ ] 微软Azure TTS
- [ ] 谷歌TTS
- [ ] 百度TTS
- [ ] 阿里云TTS

## 🔧 配置说明

### 提供商配置示例

```json
{
  "providers": [
    {
      "id": "provider_001",
      "type": "index_tts",
      "custom_name": "我的TTS",
      "server_address": "192.168.1.100",
      "web_port": 7860,
      "synth_port": 9880,
      "enabled": true
    }
  ]
}
```

### 导出JSON格式

```json
[
  {
    "concurrentRate": "0",
    "contentType": "audio/wav",
    "enabledCookieJar": false,
    "id": -100,
    "lastUpdateTime": 1640995200000,
    "name": "忧伤女声.pt_我的TTS - index TTS",
    "url": "http://192.168.1.100:9880/?text={{speakText}}&speaker=忧伤女声.pt&speed=1.0&volume=1.0"
  }
]
```

## 🌐 局域网搜索

程序支持自动搜索局域网内的index TTS服务器：

- **扫描端口**: 7860 (Web接口), 9880 (合成接口)
- **扫描范围**: 192.168.1.1-254, 192.168.0.1-254, 10.0.0.1-254
- **验证方式**: 调用Gradio API确认服务类型

## ♿ 无障碍特性

### 键盘导航

- **Tab键**: 正向导航
- **Shift+Tab**: 反向导航
- **空格键**: 选中/取消选中
- **回车键**: 确认/试听
- **Esc键**: 取消/关闭

### 屏幕阅读器支持

- 完整的控件标签
- 状态变化提示
- 操作结果反馈

## 📝 开发计划

- [x] 项目架构设计
- [x] 详细文档编写
- [ ] 基础界面开发
- [ ] 提供商管理功能
- [ ] 网络功能实现
- [ ] 角色管理功能
- [ ] 导出功能实现
- [ ] 无障碍优化
- [ ] 测试和发布

## 🤝 贡献

欢迎提交Issue和Pull Request！

### 开发环境设置

1. Fork本仓库
2. 创建特性分支: `git checkout -b feature/AmazingFeature`
3. 提交更改: `git commit -m 'Add some AmazingFeature'`
4. 推送到分支: `git push origin feature/AmazingFeature`
5. 打开Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- index TTS服务提供商
- wxPython GUI框架
- Legado阅读软件

## 📞 联系方式

- **GitHub Issues**: [提交问题](https://github.com/yourusername/LegadoTTSTool/issues)
- **Email**: your-email@example.com

## 🔗 相关链接

- [Legado阅读软件](https://github.com/gedoor/legado)
- [index TTS项目](https://github.com/index-tts)
- [wxPython官方文档](https://docs.wxpython.org/)

---

⭐ 如果这个项目对您有帮助，请考虑给个星标！