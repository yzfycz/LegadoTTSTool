#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件工具模块
提供文件操作相关的工具函数
"""

import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import time
import zipfile

class FileUtils:
    """文件工具类"""
    
    @staticmethod
    def ensure_directory(path: Union[str, Path]) -> Path:
        """确保目录存在"""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @staticmethod
    def read_json_file(file_path: Union[str, Path]) -> Dict[str, Any]:
        """读取JSON文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError as e:
            raise Exception(f"JSON文件格式错误: {e}")
        except Exception as e:
            raise Exception(f"读取文件失败: {e}")
    
    @staticmethod
    def write_json_file(file_path: Union[str, Path], data: Dict[str, Any], indent: int = 2) -> None:
        """写入JSON文件"""
        try:
            # 确保目录存在
            FileUtils.ensure_directory(Path(file_path).parent)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=indent)
        except Exception as e:
            raise Exception(f"写入文件失败: {e}")
    
    @staticmethod
    def read_text_file(file_path: Union[str, Path], encoding: str = 'utf-8') -> str:
        """读取文本文件"""
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except FileNotFoundError:
            return ""
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    return f.read()
            except UnicodeDecodeError:
                try:
                    with open(file_path, 'r', encoding='latin-1') as f:
                        return f.read()
                except Exception as e:
                    raise Exception(f"无法解码文件: {e}")
        except Exception as e:
            raise Exception(f"读取文件失败: {e}")
    
    @staticmethod
    def write_text_file(file_path: Union[str, Path], content: str, encoding: str = 'utf-8') -> None:
        """写入文本文件"""
        try:
            # 确保目录存在
            FileUtils.ensure_directory(Path(file_path).parent)
            
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(content)
        except Exception as e:
            raise Exception(f"写入文件失败: {e}")
    
    @staticmethod
    def copy_file(src: Union[str, Path], dst: Union[str, Path]) -> None:
        """复制文件"""
        try:
            shutil.copy2(src, dst)
        except Exception as e:
            raise Exception(f"复制文件失败: {e}")
    
    @staticmethod
    def move_file(src: Union[str, Path], dst: Union[str, Path]) -> None:
        """移动文件"""
        try:
            shutil.move(str(src), str(dst))
        except Exception as e:
            raise Exception(f"移动文件失败: {e}")
    
    @staticmethod
    def delete_file(file_path: Union[str, Path]) -> bool:
        """删除文件"""
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                return True
            return False
        except Exception as e:
            print(f"删除文件失败: {e}")
            return False
    
    @staticmethod
    def delete_directory(dir_path: Union[str, Path], recursive: bool = True) -> bool:
        """删除目录"""
        try:
            path = Path(dir_path)
            if path.exists():
                if recursive:
                    shutil.rmtree(path)
                else:
                    path.rmdir()
                return True
            return False
        except Exception as e:
            print(f"删除目录失败: {e}")
            return False
    
    @staticmethod
    def file_exists(file_path: Union[str, Path]) -> bool:
        """检查文件是否存在"""
        return Path(file_path).exists()
    
    @staticmethod
    def get_file_size(file_path: Union[str, Path]) -> int:
        """获取文件大小"""
        try:
            return Path(file_path).stat().st_size
        except Exception:
            return 0
    
    @staticmethod
    def get_file_info(file_path: Union[str, Path]) -> Dict[str, Any]:
        """获取文件信息"""
        try:
            path = Path(file_path)
            if not path.exists():
                return {}
            
            stat = path.stat()
            
            return {
                'name': path.name,
                'size': stat.st_size,
                'created_time': stat.st_ctime,
                'modified_time': stat.st_mtime,
                'is_file': path.is_file(),
                'is_dir': path.is_dir(),
                'extension': path.suffix,
                'parent': str(path.parent)
            }
        except Exception as e:
            print(f"获取文件信息失败: {e}")
            return {}
    
    @staticmethod
    def list_files(directory: Union[str, Path], pattern: str = "*", recursive: bool = False) -> List[Path]:
        """列出文件"""
        try:
            path = Path(directory)
            if not path.exists():
                return []
            
            if recursive:
                return list(path.rglob(pattern))
            else:
                return list(path.glob(pattern))
        except Exception as e:
            print(f"列出文件失败: {e}")
            return []
    
    @staticmethod
    def create_temp_file(suffix: str = ".tmp", prefix: str = "tmp_", dir: str = None) -> str:
        """创建临时文件"""
        try:
            if dir:
                FileUtils.ensure_directory(dir)
            
            fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=dir)
            os.close(fd)
            return temp_path
        except Exception as e:
            raise Exception(f"创建临时文件失败: {e}")
    
    @staticmethod
    def create_temp_directory(prefix: str = "tmp_", dir: str = None) -> str:
        """创建临时目录"""
        try:
            if dir:
                FileUtils.ensure_directory(dir)
            
            return tempfile.mkdtemp(prefix=prefix, dir=dir)
        except Exception as e:
            raise Exception(f"创建临时目录失败: {e}")
    
    @staticmethod
    def clean_temp_files(temp_dir: Union[str, Path], max_age_hours: int = 24) -> int:
        """清理临时文件"""
        try:
            path = Path(temp_dir)
            if not path.exists():
                return 0
            
            current_time = time.time()
            max_age = max_age_hours * 3600
            cleaned_count = 0
            
            for file_path in path.rglob("*"):
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > max_age:
                        try:
                            file_path.unlink()
                            cleaned_count += 1
                        except Exception:
                            pass
            
            return cleaned_count
        except Exception as e:
            print(f"清理临时文件失败: {e}")
            return 0
    
    @staticmethod
    def create_zip(zip_path: Union[str, Path], files_to_add: List[Union[str, Path]], base_dir: Union[str, Path] = None) -> None:
        """创建ZIP文件"""
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in files_to_add:
                    file_path = Path(file_path)
                    if file_path.exists():
                        if base_dir:
                            arcname = str(file_path.relative_to(base_dir))
                        else:
                            arcname = file_path.name
                        
                        zipf.write(file_path, arcname)
        except Exception as e:
            raise Exception(f"创建ZIP文件失败: {e}")
    
    @staticmethod
    def extract_zip(zip_path: Union[str, Path], extract_to: Union[str, Path]) -> List[str]:
        """解压ZIP文件"""
        try:
            extracted_files = []
            
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                zipf.extractall(extract_to)
                extracted_files = zipf.namelist()
            
            return extracted_files
        except Exception as e:
            raise Exception(f"解压ZIP文件失败: {e}")
    
    @staticmethod
    def get_directory_size(directory: Union[str, Path]) -> int:
        """获取目录大小"""
        try:
            path = Path(directory)
            if not path.exists():
                return 0
            
            total_size = 0
            for file_path in path.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            
            return total_size
        except Exception as e:
            print(f"获取目录大小失败: {e}")
            return 0
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    @staticmethod
    def is_file_readable(file_path: Union[str, Path]) -> bool:
        """检查文件是否可读"""
        try:
            path = Path(file_path)
            return path.exists() and os.access(path, os.R_OK)
        except Exception:
            return False
    
    @staticmethod
    def is_file_writable(file_path: Union[str, Path]) -> bool:
        """检查文件是否可写"""
        try:
            path = Path(file_path)
            if path.exists():
                return os.access(path, os.W_OK)
            else:
                # 检查父目录是否可写
                parent = path.parent
                return parent.exists() and os.access(parent, os.W_OK)
        except Exception:
            return False
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """清理文件名，移除非法字符"""
        import re
        
        # 替换Windows和Linux的非法字符
        illegal_chars = r'[<>:"/\\|?*]'
        sanitized = re.sub(illegal_chars, '_', filename)
        
        # 移除控制字符
        sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', sanitized)
        
        # 限制长度
        if len(sanitized) > 255:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[:255-len(ext)] + ext
        
        # 确保不以点开头或结尾
        sanitized = sanitized.strip('.')
        
        # 确保不是空字符串
        if not sanitized:
            sanitized = "unnamed_file"
        
        return sanitized
    
    @staticmethod
    def backup_file(file_path: Union[str, Path], backup_dir: Union[str, Path] = "backups") -> str:
        """备份文件"""
        try:
            source_path = Path(file_path)
            if not source_path.exists():
                raise Exception("源文件不存在")
            
            # 创建备份目录
            backup_path = Path(backup_dir)
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # 生成备份文件名
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            backup_name = f"{source_path.stem}_backup_{timestamp}{source_path.suffix}"
            backup_file_path = backup_path / backup_name
            
            # 复制文件
            shutil.copy2(source_path, backup_file_path)
            
            return str(backup_file_path)
        except Exception as e:
            raise Exception(f"备份文件失败: {e}")
    
    @staticmethod
    def restore_file(backup_path: Union[str, Path], target_path: Union[str, Path]) -> None:
        """恢复文件"""
        try:
            if not Path(backup_path).exists():
                raise Exception("备份文件不存在")
            
            shutil.copy2(backup_path, target_path)
        except Exception as e:
            raise Exception(f"恢复文件失败: {e}")