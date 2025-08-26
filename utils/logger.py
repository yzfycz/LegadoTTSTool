#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志系统模块
提供文件日志记录功能
"""

import os
import time
import datetime
from pathlib import Path
from typing import Optional
import threading

class Logger:
    """日志记录器"""
    
    def __init__(self, log_dir: str = "logs"):
        """初始化日志记录器"""
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        self.debug_mode = False
        self.log_file = None
        self.lock = threading.Lock()
        
        # 启动时创建新的日志文件
        self._create_new_log_file()
    
    def _create_new_log_file(self):
        """创建新的日志文件"""
        try:
            # 生成日志文件名：debug_YYYYMMDD.log
            today = datetime.datetime.now().strftime("%Y%m%d")
            log_filename = f"debug_{today}.log"
            log_path = self.log_dir / log_filename
            
            # 关闭之前的日志文件
            if self.log_file:
                self.log_file.close()
            
            # 打开新的日志文件
            self.log_file = open(log_path, "a", encoding="utf-8")
            
            # 写入文件头
            header = f"\n{'='*50}\n"
            header += f"日志启动时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            header += f"{'='*50}\n"
            self._write_to_file(header)
            
        except Exception as e:
            print(f"创建日志文件失败: {e}")
    
    def _write_to_file(self, message: str):
        """写入文件"""
        try:
            if self.log_file:
                self.log_file.write(message)
                self.log_file.flush()
        except Exception as e:
            print(f"写入日志文件失败: {e}")
    
    def set_debug_mode(self, enabled: bool):
        """设置调试模式"""
        with self.lock:
            self.debug_mode = enabled
            self._log("INFO", f"调试模式: {'开启' if enabled else '关闭'}")
    
    def _log(self, level: str, message: str):
        """内部日志记录方法"""
        if not self.debug_mode:
            return
        
        try:
            # 生成时间戳
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            
            # 生成日志行
            log_line = f"[{timestamp}] [{level}] {message}\n"
            
            # 写入文件
            with self.lock:
                self._write_to_file(log_line)
                
        except Exception as e:
            print(f"日志记录失败: {e}")
    
    def debug(self, message: str):
        """调试信息"""
        self._log("DEBUG", message)
    
    def info(self, message: str):
        """普通信息"""
        self._log("INFO", message)
    
    def warning(self, message: str):
        """警告信息"""
        self._log("WARNING", message)
    
    def error(self, message: str):
        """错误信息"""
        self._log("ERROR", message)
    
    def log_function_call(self, func_name: str, args: dict = None, result: str = "成功"):
        """记录函数调用"""
        args_str = ", ".join([f"{k}={v}" for k, v in args.items()]) if args else "无参数"
        self.debug(f"函数调用: {func_name}({args_str}) -> {result}")
    
    def log_network_operation(self, operation: str, details: str):
        """记录网络操作"""
        self.info(f"网络操作: {operation} - {details}")
    
    def log_ui_event(self, event_type: str, details: str):
        """记录UI事件"""
        self.debug(f"UI事件: {event_type} - {details}")
    
    def close(self):
        """关闭日志记录器"""
        try:
            if self.log_file:
                self.info("日志系统关闭")
                self.log_file.close()
                self.log_file = None
        except Exception as e:
            print(f"关闭日志记录器失败: {e}")

# 全局日志实例
logger = Logger()

def get_logger() -> Logger:
    """获取全局日志实例"""
    return logger