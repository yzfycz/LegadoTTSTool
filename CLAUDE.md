# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LegadoTTSTool is a specialized accessibility-first TTS (Text-to-Speech) voice role management tool designed specifically for blind users. It enables users to discover TTS servers on their local network, manage voice roles, and export them in JSON format compatible with the Legado reading software.

### Features
- 🎯 **完全无障碍**: 100%支持键盘操作，专为盲人用户优化
- 🔧 **提供商管理**: 支持多种TTS提供商的配置和管理
- 🌐 **智能局域网搜索**: 自动发现局域网内的index TTS服务器，支持多服务器选择
- 🎵 **实时试听**: 支持角色试听和参数调节
- 📤 **批量导出**: 一键导出为Legado兼容的JSON格式
- ⚙️ **动态界面**: 根据不同提供商动态生成配置界面
- ⌨️ **高效键盘导航**: 光标式操作，回车确认，类似方案管理列表体验

## Development Commands

### Running the Application
```bash
# Production entry
python main.py

# Development launcher (with dependency checking)
python run.py
```

### Installation
```bash
pip install -r requirements.txt
```

## Architecture Overview

### Layered Architecture
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

### Event-Driven Threading Model
- All network operations run in background threads using `threading.Thread`
- Custom wxPython events (`RoleUpdateEvent`, `ProviderUpdateEvent`) for thread-safe UI updates
- Progress indicators and status feedback via event posting

## Core Components

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
- Supports HTTP/HTTPS URLs and optional port configuration
- Includes timeout control for preview operations

### NetworkScanner
- Intelligent LAN discovery that detects local network segment
- Verifies TTS servers via Gradio API endpoint testing
- Supports both index TTS and other service type detection
- Concurrent scanning with result aggregation
- Automatically detects local IP and scans only the local network segment

### JSONExporter
- Generates Legado-compatible JSON exports with proper structure
- Creates unique timestamp-based IDs with collision avoidance
- Supports batch export with configurable parameters (speed, volume)
- Includes proper content type and concurrent rate settings
- Outputs URLs without encoding for direct use

## Key Implementation Patterns

### Accessibility Implementation
- **100% Keyboard Navigation**: All controls support Tab/Shift+Tab navigation
- **Screen Reader Support**: Complete labeling and custom accessibility utilities
- **Focus Management**: Logical focus order and visual indicators
- **Status Feedback**: Real-time status updates for all operations
- **Parameter Control Optimization**: TextCtrl + input validation + keyboard control + real-time announcements
  - Range validation: 0.5-2.0 automatic limiting
  - Formatting: One decimal place auto-formatting
  - Keyboard control: Up/down arrows 0.1 step adjustment
  - Accessibility announcements: 200ms debounced real-time feedback

### Unicode Handling
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

### Dynamic UI Generation
Configuration interfaces adapt based on provider type:
- Different form fields for different TTS services
- Real-time validation of user input
- Automatic field population and state management

## Configuration Management

### Provider Configuration Structure
```json
{
  "providers": [
    {
      "id": "uuid-string",
      "type": "index_tts",
      "custom_name": "My TTS",
      "enabled": true,
      "server_address": "127.0.0.1",
      "web_port": 7860,
      "synth_port": 9880,
      "preview_text": "Test text for voice preview",
      "created_time": "2024-01-01T00:00:00Z",
      "last_used": null
    }
  ],
  "version": "1.0.0",
  "last_updated": "2024-01-01T00:00:00Z"
}
```

### Auto-Creation
The application automatically creates `config/providers.json` on first run with a default index TTS provider configuration.

## Error Handling Patterns

### Network Operations
- All network requests include timeout handling
- Comprehensive exception handling for connection failures
- User-friendly error messages via status events
- Retry mechanisms for critical operations

### Threading Safety
- Custom wxPython events ensure thread-safe UI updates
- Proper resource cleanup in `finally` blocks
- Prevention of multiple concurrent operations on same resources

### Program Exit Cleanup
The application includes proper resource cleanup to prevent RecursionError on exit.

## Common Issues and Solutions

### Unicode Encoding Problems
The TTSClient includes specific handling for gradio_client Unicode issues via stdout redirection.

### Threading UI Updates
Use custom wxPython events and `wx.PostEvent()` for thread-safe UI updates from background threads.

### Provider Configuration Changes
Provider modifications immediately update the UI via event system - no application restart required.

### Program Exit Cleanup
The application includes proper resource cleanup to prevent RecursionError on exit.

## Development Guidelines

### Code Style
- Use meaningful English variable names and function names
- Add Chinese comments for key functionality
- Implement comprehensive exception handling
- Follow accessibility-first design principles

### Testing Approach
- Test with actual TTS servers when possible
- Verify accessibility with screen readers (NVDA, JAWS)
- Test network functionality in different LAN configurations
- Validate JSON export format with Legado software

## User Interface Features

### Main Interface Controls
- **Alt+C**: Open operation menu
- **Alt+S**: Focus scheme selection
- **Alt+R**: Refresh role list
- **Space**: Select/deselect roles
- **Enter**: Preview selected role
- **Alt+A**: Select all roles
- **Alt+D**: Deselect roles
- **Alt+E**: Export JSON

### Interface Characteristics
- **Real-time status display**: Shows "正在获取音色" status when refreshing roles
- **Smart filtering**: Automatically filters "使用参考音频" and special options
- **Non-disruptive experience**: Direct result display without popup dialogs
- **Real-time updates**: Provider configuration changes take effect immediately
- **Parameter control optimization**: Speed and volume use text input with keyboard control
- **Smart validation**: Automatic range limiting (0.5-2.0) with one decimal formatting
- **Accessibility announcements**: Screen reader feedback for parameter changes

## Project Structure

```
LegadoTTSTool/
├── main.py                 # Main program entry
├── run.py                  # Test launcher script
├── config/                 # Configuration directory
│   └── providers.json      # Provider configurations
├── ui/                     # UI modules
│   ├── main_frame.py       # Main interface
│   ├── provider_dialog.py  # Provider management dialog
│   └── config_dialog.py    # Provider configuration dialog
├── core/                   # Core functionality modules
│   ├── provider_manager.py # Provider manager
│   ├── network_scanner.py  # Network scanner
│   ├── tts_client.py       # TTS client
│   └── json_exporter.py    # JSON exporter
├── utils/                  # Utility modules
│   ├── accessibility.py    # Accessibility utilities
│   └── file_utils.py       # File operation utilities
├── requirements.txt        # Python dependencies
├── .gitignore             # Git ignore file
└── README.md              # Project documentation
```

## Development Status

### Completed Features
- **Core Architecture**
  - Modular code structure
  - Complete exception handling
  - Configuration file management
  
- **User Interface**
  - Main interface framework
  - Provider management dialog
  - Dynamic configuration interface
  - Menu system
  
- **Functionality Modules**
  - Provider manager
  - Network scanner
  - TTS client
  - JSON exporter
  
- **Accessibility Support**
  - Keyboard navigation
  - Screen reader support
  - High contrast mode
  
- **index TTS Support**
  - Role list retrieval
  - Voice preview
  - LAN search
  
- **User Experience Optimization**
  - Real-time status display
  - Smart filtering
  - Non-disruptive experience
  - Real-time updates
  - Recursion error fix
  - API compatibility fix
  - Parameter control optimization
  - Smart input validation
  - Real-time accessibility announcements

### Planned Features
- **Support more TTS providers**
  - Microsoft Azure TTS
  - Google TTS
  - Baidu TTS
  - Alibaba Cloud TTS
  
- **Interface Improvements**
  - Focus management optimization
  - Control label completion
  - Error handling optimization
  
- **Testing**
  - Unit tests
  - Integration tests
  - Accessibility tests

## Supported TTS Providers

### index TTS
- Automatic LAN discovery
- Role list retrieval support
- Real-time voice preview
- Batch role export

### Planned Support
- [ ] Microsoft Azure TTS
- [ ] Google TTS
- [ ] Baidu TTS
- [ ] Alibaba Cloud TTS

## Dependencies

### Core Dependencies
- `wxPython==4.2.1`: GUI framework with accessibility support
- `requests==2.31.0`: HTTP client for API calls
- `gradio_client==0.8.1`: Gradio API client for TTS services
- `pygame==2.5.2`: Audio playback for voice preview
- `uuid==1.30`: UUID generation for provider IDs

### Platform Requirements
- Python 3.8+
- Windows 10/11 (primary target platform)
- Screen reader support (NVDA, JAWS recommended)

## Changelog

### [1.0.0] - 2024-08-25

#### New Features
- Complete graphical user interface (wxPython)
- Provider management system (CRUD operations)
- LAN TTS server automatic search functionality
- Real-time voice role retrieval and preview functionality
- Batch JSON export functionality (Legado compatible format)
- Dynamic configuration interface generation
- Complete accessibility support (keyboard navigation, screen reader)

#### Optimizations
- Unicode encoding issue fix (Gradio client compatibility)
- Program exit recursion error fix
- Provider configuration changes take effect immediately
- Smart role filtering (automatically filters "使用参考音频")
- Real-time status display (voice retrieval progress)
- Non-disruptive user experience (no popup for successful operations)
- Parameter control optimization (TextCtrl replaces Slider for better accessibility)
- Smart input validation (automatic range limiting and formatting)
- Real-time accessibility announcements (screen reader feedback for parameter changes)
- **Server selection dialog keyboard navigation optimization**: Cursor-based operation with Enter confirmation
- **Multi-server selection interface**: Intelligent LAN discovery with user-friendly server selection dialog
- **wxWidgets dialog stability fix**: Resolved C++ assertion failures in dialog sizer relationships
- **Enhanced keyboard accessibility**: Focus-based navigation similar to provider management list

#### Technical Implementation
- Modular architecture design (UI layer, business logic layer, data storage layer)
- Event-driven threading model
- Comprehensive exception handling mechanism
- Automatic configuration file creation and management
- UUID generation and timestamp management

### [0.2.0] - 2024-08-24

#### New Features
- Project architecture design
- Core module framework setup
- Basic interface prototype
- Configuration file structure design
- Development documentation

#### Technology Stack
- Python 3.8+
- wxPython GUI framework
- requests network library
- gradio_client library
- JSON configuration files

### [0.1.0] - 2024-08-20

#### New Features
- Project concept design
- Requirements analysis
- Technical architecture planning
- Interface design prototype
- Development planning
- GitHub repository creation