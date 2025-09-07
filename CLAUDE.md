# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LegadoTTSTool is a specialized accessibility-first TTS (Text-to-Speech) voice role management tool designed specifically for blind users. It enables users to discover TTS servers on their local network, manage voice roles, and export them in JSON format compatible with the Legado reading software.

### Features
- 🎯 **完全无障碍**: 100%支持键盘操作，专为盲人用户优化
- 🔧 **提供商管理**: 支持多种TTS提供商的配置和管理
- 🌐 **全网段智能搜索**: 自动扫描局域网完整IP段(1-255)，150线程多线程并发加速，支持快速/全扫描双模式
- 🎵 **实时试听**: 支持角色试听和参数调节
- 📤 **批量导出**: 一键导出为Legado兼容的JSON格式
- ⚙️ **动态界面**: 根据不同提供商动态生成配置界面
- ⌨️ **完整键盘快捷键系统**: 所有控件都有唯一的Alt+key快捷键，无冲突设计
- 🚀 **高性能网络扫描**: 实时进度显示，智能IP过滤，并行端口检查，可配置性能参数，Unicode安全输出处理
- 🔊 **智能音效系统**: 上下文音效反馈，试听和搜索时播放提示音效，自动停止机制

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
- Handles complex Gradio API interactions for index-tts services
- Implements Unicode encoding fixes via stdout redirection
- Supports voice role retrieval and real-time text-to-speech synthesis
- Comprehensive error handling for network and API failures
- Supports HTTP/HTTPS URLs and optional port configuration
- Includes timeout control for preview operations

### NetworkScanner
- **Full Network Segment Scanning**: Scans complete IP range (1-255) for comprehensive server discovery
- **High-Performance Multi-threading**: Up to 150 concurrent threads for rapid network scanning
- **Intelligent LAN Discovery**: Automatically detects local network segment and prioritizes local IP
- **Advanced Server Verification**: Verifies TTS servers via Gradio API endpoint testing
- **Dual-Mode Scanning**: Supports both fast mode and full network scanning modes
- **Real-time Progress Tracking**: Shows scanning progress with detailed logging
- **Smart IP Filtering**: Automatically skips network addresses (.0) and broadcast addresses (.255)
- **Parallel Port Checking**: Simultaneously checks Web (7860) and Synthesis (9880) ports
- **Configurable Performance**: Adjustable timeout settings and thread counts
- **Unicode-Safe Output**: Handles encoding issues with safe print functions
- **Smart Segment Filtering**: Intelligent IP network segment filtering to skip virtual network cards

### SoundManager
- **Contextual Audio Feedback**: Plays appropriate sound effects for preview and search operations
- **Multi-threaded Audio Playback**: Background sound effects with proper resource management
- **Intelligent Sound Control**: Automatically stops sound effects when TTS audio is received or operations complete
- **File Path Management**: Automatic sound file discovery for both development and packaged environments
- **Event-Driven Architecture**: Uses custom SoundStopEvent for thread-safe audio control
- **Graceful Degradation**: Silently handles missing sound files without affecting core functionality
- **Resource Management**: Proper pygame.mixer initialization, cleanup, and state management

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

### High-Performance Network Scanning
The NetworkScanner implements advanced scanning capabilities for comprehensive server discovery:

#### Smart Network Segment Filtering
The application now includes intelligent network segment filtering to automatically skip virtual network cards and optimize scanning performance:

```python
# Segment categories with priorities
SEGMENT_CATEGORIES = {
    'HIGH_PRIORITY': {
        'name': '高优先级网段',
        'segments': ['192.168.0.0/16', '10.0.0.0/8', '172.16.0.0/12'],
        'scan_mode': 'FULL'  # Complete scan
    },
    'MEDIUM_PRIORITY': {
        'name': '中优先级网段',
        'segments': ['100.64.0.0/10', '169.254.0.0/16'],
        'scan_mode': 'FAST'  # Quick scan
    },
    'LOW_PRIORITY': {
        'name': '低优先级网段',
        'segments': ['172.17.0.0/16', '172.18.0.0/16', ...],  # Docker, VPN
        'scan_mode': 'SKIP'  # Skip scanning
    }
}
```

#### Full Network Segment Scanning
```python
# Scans complete IP range (1-255) for maximum coverage
def _scan_segment_with_strategy(self, segment: str) -> List[str]:
    priority_ips = []
    
    # Prioritize local machine IP
    for adapter in adapters:
        for ip in adapter['ipv4']:
            if ip.startswith(segment):
                priority_ips.append(ip)
    
    # Full network scan: 1-255
    for i in range(1, 256):
        ip = f"{segment}.{i}"
        if ip not in priority_ips:
            priority_ips.append(ip)
    
    return priority_ips
```

#### Multi-threaded Performance Optimization
```python
# Up to 150 concurrent threads for rapid scanning
with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
    future_to_ip = {
        executor.submit(self._check_host_ports, ip): ip 
        for ip in ip_list
    }
```

#### Parallel Port Checking
```python
# Simultaneously check Web (7860) and Synthesis (9880) ports
def _check_host_ports(self, ip: str) -> Optional[Dict[str, Any]]:
    # Skip network and broadcast addresses
    if ip.endswith('.0') or ip.endswith('.255'):
        return None
    
    # Parallel port checking with threading
    web_thread = threading.Thread(target=check_web_port)
    synth_thread = threading.Thread(target=check_synth_port)
    
    web_thread.start()
    synth_thread.start()
    
    web_thread.join(timeout=self.timeout + 0.5)
    synth_thread.join(timeout=self.timeout + 0.5)
```

#### Dual-Mode Scanning
```python
# Fast mode vs Full network scanning
def scan_index_tts_servers(self, fast_mode: bool = True) -> List[Dict[str, Any]]:
    if fast_mode and len(servers) >= 2:
        logger.info("快速模式：已找到足够的服务器，跳过网络扫描")
    else:
        logger.info("全网段扫描模式：开始完整网络扫描")
```

#### Configuration and Performance Tuning
```python
# Configurable scanning parameters
scanner.set_scan_config(
    timeout=1.0,        # Timeout in seconds
    max_threads=150,    # Maximum concurrent threads
    fast_mode=True      # Fast scanning mode
)

# Performance estimation
estimate = scanner.estimate_scan_time()
print(f"预计扫描时间: {estimate['estimated_seconds']:.1f} 秒")
```

#### Safe Output Handling
```python
def safe_print(message: str) -> None:
    """Safe printing function for Unicode handling"""
    try:
        print(message)
    except UnicodeEncodeError:
        cleaned_message = message.encode('ascii', errors='ignore').decode('ascii')
        print(cleaned_message)
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
The application automatically creates `config/providers.json` on first run with a default index-tts provider configuration.

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
The TTSClient and NetworkScanner include comprehensive Unicode handling:
- Safe print functions that handle encoding errors gracefully
- Stdout redirection for gradio_client compatibility
- Automatic cleaning of problematic Unicode characters

### Network Scanning Issues
**Problem**: Can't find TTS servers on the local network
**Solution**: 
- Ensure full network scanning is enabled (scans 1-255 IP range)
- Check that TTS server is running on ports 7860 (Web) or 9880 (Synthesis)
- Verify network connectivity and firewall settings
- Use performance tuning to adjust timeout and thread settings

**Problem**: Scanning is too slow
**Solution**:
- Use fast mode for quick discovery
- Increase thread count (up to 150 concurrent threads)
- Reduce timeout settings for faster scanning
- Enable progress monitoring to track scanning status

**Problem**: Scanning misses local TTS server
**Solution**:
- The scanner now prioritizes local machine IP address
- Ensure local TTS server is running and accessible
- Check IP address configuration and network segment detection

**Problem**: Virtual network cards (Clash, Docker, VPN) are being scanned
**Solution**:
- The application now includes intelligent network segment filtering
- Virtual network segments are automatically detected and skipped
- Real LAN and tunneling segments are prioritized
- Performance is improved by 2-3x through smart filtering

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
- **Alt+L**: Focus voice role list
- **Alt+R**: Refresh role list
- **Alt+X**: Focus preview text input
- **Alt+P**: Focus speed control (Pace)
- **Alt+V**: Focus volume control
- **Alt+T**: Preview current role
- **Alt+O**: Stop audio playback
- **Space**: Select/deselect roles
- **Enter**: Navigate to role (no preview)
- **Alt+A**: Select all roles
- **Alt+D**: Deselect roles (Inverse selection)
- **Alt+E**: Export JSON

### Interface Characteristics
- **Real-time status display**: Shows refresh status via button labels when refreshing roles
- **Smart filtering**: Automatically filters "使用参考音频" and special options
- **Non-disruptive experience**: Direct result display without popup dialogs
- **Real-time updates**: Provider configuration changes take effect immediately
- **Parameter control optimization**: Speed and volume use text input with keyboard control
- **Smart validation**: Automatic range limiting (0.5-2.0) with one decimal formatting
- **Accessibility announcements**: Screen reader feedback for parameter changes

### Function Design Principles
- **Preview Function**: Preview is only available via the preview button (Alt+T shortcut). It's based on cursor position (current focused role), not checkbox selection state. Users navigate with arrow keys to focus a role, then press Alt+T to preview it.
- **Selection Function**: Spacebar is used only for selecting/deselecting roles for batch export operations. Selection state is independent from preview functionality.
- **Independent Operations**: Preview and selection are separate functions - users can preview any focused role via Alt+T, while independently selecting multiple roles for export using spacebar.
- **Restricted Triggers**: Only the preview button and Alt+T shortcut can trigger preview. Double-click and Enter key do not trigger preview.

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
│   ├── sound_manager.py    # Sound effect management
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
  - Sound effect system
  
- **Accessibility Support**
  - Keyboard navigation
  - Screen reader support
  - High contrast mode
  
- **index-tts Support**
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
  - **Complete keyboard shortcut system**: Unique Alt+key shortcuts for all controls
  - **Shortcut conflict resolution**: Resolved conflicts between export and parameter controls
  - **Simplified button state management**: Streamlined reset logic for improved stability
  - **Enhanced shortcut reliability**: Improved persistence after button operations
  
- **Advanced Network Scanning System**
  - **Full network segment scanning**: Complete IP range (1-255) coverage for comprehensive server discovery
  - **High-performance multi-threading**: Up to 150 concurrent threads for rapid scanning (8.6 IP/second)
  - **Performance optimization**: Configurable timeout settings and thread counts for different network environments
  - **Dual-mode scanning**: Fast mode for quick discovery and full mode for comprehensive scanning
  - **Smart IP prioritization**: Local machine IP is prioritized to ensure discovery of local TTS servers
  - **Parallel port checking**: Simultaneous Web (7860) and Synthesis (9880) port verification
  - **Real-time progress tracking**: Live scanning progress with detailed logging every 20 IP addresses
  - **Intelligent IP filtering**: Automatic skipping of network addresses (.0) and broadcast addresses (.255)
  - **Configurable performance**: Adjustable timeout settings and thread counts for different network environments
  - **Unicode-safe output**: Comprehensive encoding error handling for stable operation on Windows systems
  - **Performance estimation**: Built-in scanning time calculation and configuration optimization
  
- **Sound Effect System**
  - **Contextual audio feedback**: Different sound effects for preview and search operations
  - **Intelligent sound control**: Automatic stopping when TTS audio is received or operations complete
  - **Thread-safe architecture**: Event-driven sound management with proper resource cleanup
  - **Graceful error handling**: Silent failure when sound files are missing
  - **Cross-platform compatibility**: Works in both development and packaged environments
  - **Smart preview logic**: Sound effects only play after valid role selection
  - **Enhanced stop functionality**: Stop button controls both TTS audio and sound effects

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

### index-tts
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
- `pygame==2.5.2`: Audio playback for voice preview and sound effects
- `uuid==1.30`: UUID generation for provider IDs

### Platform Requirements
- Python 3.8+
- Windows 10/11 (primary target platform)
- Screen reader support (NVDA, JAWS recommended)

## Changelog

### [1.1.2] - 2024-08-27

#### New Features
- **Enhanced Preview Logic**: Preview function now based on cursor position rather than selection state
- **Improved User Experience**: Removed unnecessary "正在获取音色" placeholder text during refresh
- **Clearer Function Separation**: Independent preview and selection operations for better usability
- **Restricted Preview Triggers**: Preview only available via preview button or Alt+T shortcut

#### Function Design Improvements
- **Preview Function**: Only Alt+T shortcut can preview the role currently under cursor focus, regardless of checkbox selection
- **Selection Function**: Spacebar selection is now purely for batch export operations
- **Button Label Updates**: Changed "试听选中角色" to "试听当前角色" to reflect actual functionality
- **No Accidental Preview**: Double-click and Enter key no longer trigger preview to prevent accidental playback

#### Technical Improvements
- **Cleaner Refresh Process**: Removed temporary placeholder items during role list refresh
- **Better State Management**: Improved separation between navigation focus and selection state
- **Simplified Event Handling**: Removed preview triggers from double-click and Enter key events

### [1.1.3] - 2024-08-29

#### New Features
- **Sound Effect System**: Implemented comprehensive audio feedback system with contextual sound effects
- **Preview Sound Effects**: "ZhengZaiHeCheng.wav" → looping "DuMiao.wav" during voice preview
- **Search Sound Effects**: "ZhengZaiSouSuo.wav" → looping "DuMiao.wav" during LAN search
- **Smart Sound Control**: Sounds only play when appropriate (no sounds during role refresh)

#### Sound System Architecture
- **SoundManager Class**: Dedicated audio management with pygame.mixer integration
- **Event-Driven Architecture**: Custom SoundStopEvent for thread-safe audio control
- **Multi-threaded Audio**: Background sound playback with proper resource management
- **File Path Management**: Automatic sound file discovery for both development and packaged environments

#### Technical Implementation
- **Audio Resource Management**: Proper pygame.mixer initialization and cleanup
- **Thread Safety**: Custom wxPython events for cross-thread communication
- **Graceful Error Handling**: Silent failure when sound files are missing
- **Memory Optimization**: Efficient temporary file cleanup with retry mechanisms

#### Bug Fixes
- **Stop Button Enhancement**: Stop button now properly stops both TTS audio and looping sound effects
- **Preview Logic Fix**: Sound effects only play after valid role selection, preventing unnecessary audio playback
- **File Locking Resolution**: Improved temporary file deletion with proper pygame.mixer resource release
- **Audio System Stability**: Enhanced mixer state management to prevent conflicts between sound effects and TTS audio

### [1.1.1] - 2024-08-27

#### New Features
- **Complete Keyboard Shortcut System**: Comprehensive Alt+key shortcuts for all interface controls
- **Shortcut Conflict Resolution**: Resolved conflicts between export and speed control shortcuts
- **Enhanced Accessibility**: Improved keyboard navigation with unique shortcuts for all controls

#### Keyboard Shortcut Updates
- **Speed Control**: Changed from Alt+E to Alt+P (Pace) to avoid conflict with export
- **Preview Text**: Changed from Alt+P to Alt+X (Te**X**t) to avoid conflict with speed
- **Export Function**: Maintained Alt+E (Export) without conflicts
- **Voice Role List**: Added Alt+L for direct list focus
- **Stop Playback**: Added Alt+O for stopping audio playback

#### Technical Improvements
- **Simplified Button State Management**: Streamlined button label reset logic for improved stability
- **Enhanced Shortcut Reliability**: Improved shortcut key persistence after button operations
- **Optimized Focus Management**: Simplified focus handling to prevent navigation issues

### [1.1.0] - 2024-08-27

#### New Features
- **Full Network Segment Scanning**: Complete IP range (1-255) coverage for comprehensive TTS server discovery
- **High-Performance Multi-threading**: Up to 150 concurrent threads for rapid scanning (8.6 IP/second)
- **Dual-Mode Scanning**: Fast mode for quick discovery and full mode for comprehensive scanning
- **Smart IP Prioritization**: Local machine IP is prioritized to ensure discovery of local TTS servers
- **Parallel Port Checking**: Simultaneous Web (7860) and Synthesis (9880) port verification
- **Real-time Progress Tracking**: Live scanning progress with detailed logging
- **Configurable Performance**: Adjustable timeout settings and thread counts
- **Performance Estimation**: Built-in scanning time calculation and optimization

#### Technical Improvements
- **Unicode-safe Output**: Comprehensive encoding error handling for Windows systems
- **Intelligent IP Filtering**: Automatic skipping of network addresses (.0) and broadcast addresses (.255)
- **Enhanced Error Handling**: Robust exception handling for network operations
- **Memory Optimization**: Improved resource management and cleanup
- **Logging Enhancement**: Detailed progress tracking and debugging information

#### Bug Fixes
- **GBK Encoding Issues**: Fixed Unicode character encoding problems in network scanning
- **Local Server Discovery**: Resolved issues with detecting TTS servers running on local machine
- **Network Configuration**: Improved network segment detection and IP range generation
- **Performance Stability**: Enhanced threading stability and resource cleanup

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