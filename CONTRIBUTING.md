# 贡献指南

感谢您对 LegadoTTSTool 的关注！我们欢迎任何形式的贡献。

## 🤝 如何贡献

### 报告问题

如果您发现了bug或有功能建议，请通过 [GitHub Issues](https://github.com/yourusername/LegadoTTSTool/issues) 提交。

在提交Issue时，请包含：
- 清晰的标题
- 详细的问题描述
- 复现步骤
- 期望行为
- 实际行为
- 运行环境信息

### 代码贡献

#### 开发环境设置

1. **Fork本仓库**
   ```bash
   # 克隆您的fork
   git clone https://github.com/yourusername/LegadoTTSTool.git
   cd LegadoTTSTool
   ```

2. **设置上游仓库**
   ```bash
   git remote add upstream https://github.com/yourusername/LegadoTTSTool.git
   ```

3. **创建虚拟环境**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 或
   venv\Scripts\activate  # Windows
   ```

4. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

#### 开发流程

1. **创建特性分支**
   ```bash
   git checkout -b feature/amazing-feature
   ```

2. **进行开发**
   - 遵循项目的代码风格
   - 添加必要的注释
   - 确保代码通过测试

3. **提交更改**
   ```bash
   git add .
   git commit -m "feat: add amazing feature"
   ```

4. **推送到分支**
   ```bash
   git push origin feature/amazing-feature
   ```

5. **创建Pull Request**
   - 清晰的标题和描述
   - 关联相关的Issue
   - 确保CI检查通过

#### 代码规范

- **Python代码**: 遵循PEP 8规范
- **注释**: 使用中文注释，保持清晰易懂
- **函数**: 添加docstring说明
- **变量**: 使用有意义的变量名

#### 提交信息规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

类型包括：
- `feat`: 新功能
- `fix`: 修复
- `docs`: 文档更改
- `style`: 代码格式化
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建或辅助工具变动

示例：
```
feat: add provider management dialog
fix: resolve network scanning timeout issue
docs: update README with installation guide
```

## 🐛 Bug修复

### 报告Bug

- 使用GitHub Issues模板
- 提供详细的复现步骤
- 包含错误日志和截图
- 说明运行环境

### 修复Bug

1. 在Issue中确认您要修复的bug
2. 创建专门的修复分支
3. 编写测试用例
4. 提交修复代码
5. 在PR中关联原Issue

## ✨ 功能请求

### 请求新功能

- 使用GitHub Issues的"Feature request"模板
- 详细描述功能需求
- 说明使用场景
- 提供可能的实现方案

### 实现新功能

1. 在Issue中讨论功能设计
2. 等待维护者确认
3. 创建实现分支
4. 编写完整的功能代码
5. 添加相应的测试
6. 更新相关文档

## 📝 文档贡献

文档改进也是重要的贡献形式：

- 修正拼写错误
- 改进文档结构
- 添加使用示例
- 翻译文档内容

## 🎨 设计贡献

欢迎提供以下设计贡献：

- 界面设计建议
- 用户体验改进
- 无障碍优化建议
- 图标和视觉资源

## 🧪 测试贡献

测试是保证质量的关键：

- 编写单元测试
- 添加集成测试
- 进行无障碍测试
- 报告测试相关问题

## 📋 代码审查

所有代码提交都会经过审查，请确保：

- 代码符合项目规范
- 功能测试通过
- 文档已更新
- 没有引入新的问题

## 🌍 社区准则

### 行为准则

- 保持友好和尊重
- 专注于技术讨论
- 欢迎新手参与
- 接受建设性批评

### 沟通方式

- GitHub Issues: 技术问题和功能请求
- Pull Requests: 代码贡献
- Discussions: 一般讨论

## 🏆 贡献者认可

所有贡献者都会在以下地方获得认可：

- [贡献者列表](CONTRIBUTORS.md)
- GitHub的贡献者图表
- Release notes中的致谢

## 📞 获取帮助

如果您在贡献过程中需要帮助：

- 查看项目文档
- 搜索现有的Issues
- 在Discussions中提问
- 联系项目维护者

## 🔗 相关链接

- [项目主页](https://github.com/yourusername/LegadoTTSTool)
- [问题追踪](https://github.com/yourusername/LegadoTTSTool/issues)
- [讨论区](https://github.com/yourusername/LegadoTTSTool/discussions)
- [Wiki文档](https://github.com/yourusername/LegadoTTSTool/wiki)

---

感谢您的贡献！🎉