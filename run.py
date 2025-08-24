#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LegadoTTSTool 启动脚本
用于测试和调试程序
"""

import sys
import os
import traceback

def main():
    """主函数"""
    try:
        print("正在启动 LegadoTTSTool...")
        
        # 添加项目根目录到Python路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, current_dir)
        
        # 检查依赖
        try:
            import wx
            print(f"wxPython 版本: {wx.__version__}")
        except ImportError:
            print("错误: 未找到 wxPython，请运行: pip install wxPython")
            return
        
        try:
            import requests
            print(f"requests 版本: {requests.__version__}")
        except ImportError:
            print("错误: 未找到 requests，请运行: pip install requests")
            return
        
        try:
            import gradio_client
            print(f"gradio_client 版本: {gradio_client.__version__}")
        except ImportError:
            print("错误: 未找到 gradio_client，请运行: pip install gradio_client")
            return
        
        # 导入主程序
        from main import main as app_main
        
        # 运行主程序
        print("程序启动成功！")
        app_main()
        
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序运行错误: {e}")
        print("\n详细信息:")
        traceback.print_exc()
        
        # 显示错误消息
        try:
            import wx
            app = wx.App()
            wx.MessageBox(f"程序启动失败:\n\n{str(e)}", "错误", wx.OK | wx.ICON_ERROR)
        except:
            pass

if __name__ == "__main__":
    main()