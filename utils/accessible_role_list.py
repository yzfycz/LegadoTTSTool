#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
无障碍语音角色列表控件
使用 wx.ListCtrl + EnableCheckBoxes() 实现完整的无障碍支持
"""

import wx
from typing import Optional, List, Any, Tuple

# 尝试导入wx.accessibility，如果不存在则使用替代方案
try:
    import wx.accessibility
    HAS_ACCESSIBILITY = True
except ImportError:
    HAS_ACCESSIBILITY = False
    
    # 创建替代的常量定义
    class AccessibilityConstants:
        ROLE_LIST = 0x21
        ROLE_LISTITEM = 0x22
        ROLE_SYSTEM_NOTHING = 0
        STATE_SYSTEM_FOCUSABLE = 0x00100000
        STATE_SYSTEM_FOCUSED = 0x00000004
        STATE_SYSTEM_SELECTABLE = 0x00200000
        STATE_SYSTEM_SELECTED = 0x00000002
        STATE_SYSTEM_CHECKED = 0x00000008
        STATE_SYSTEM_ENABLED = 0x10000000
        STATE_SYSTEM_UNAVAILABLE = 0x00000001
        EVENT_OBJECT_FOCUS = 0x8005
        EVENT_OBJECT_STATECHANGE = 0x800A
        EVENT_OBJECT_SELECTION = 0x8006
        OBJID_CLIENT = -4
        ACCESSIBLE_SELF = 0
        ACCESSIBLE_NONE = -1
    
    wx.accessibility = AccessibilityConstants()

# 为wx模块添加缺失的常量
if not hasattr(wx, 'ACCESSIBLE_SELF'):
    wx.ACCESSIBLE_SELF = 0
if not hasattr(wx, 'ACCESSIBLE_NONE'):
    wx.ACCESSIBLE_NONE = -1

# 为wx模块添加缺失的事件类
if not hasattr(wx, 'ListEvent'):
    wx.ListEvent = wx.CommandEvent


class AccessibleRoleList(wx.ListCtrl):
    """具有完整无障碍支持的语音角色列表控件
    
    使用 wx.ListCtrl + EnableCheckBoxes() 实现更好的屏幕阅读器兼容性
    """
    
    def __init__(self, parent, choices=None, **kwargs):
        """初始化可访问的角色列表
        
        Args:
            parent: 父窗口
            choices: 选项列表
            **kwargs: 其他参数
        """
        if choices is None:
            choices = []
        
        # 设置默认样式
        style = kwargs.get('style', wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_NO_HEADER)
        kwargs['style'] = style
        
        # 调用父类构造函数
        super().__init__(parent, **kwargs)
        
        # 设置无障碍支持
        self._accessible = None
        
        # 存储选项数据
        self._choices = list(choices)
        self._checked_states = [False] * len(choices)
        
        # 设置默认的无障碍属性
        name = kwargs.get('name', "语音角色列表")
        self.SetName(name)
        self.SetHelpText("使用上下光标键浏览，空格键选择或取消选择")
        
        # 初始化列表
        self._setup_list()
        
        # 绑定事件
        self._bind_events()
    
    def _setup_list(self):
        """设置列表控件"""
        # 添加列
        self.InsertColumn(0, "语音角色", width=350)
        
        # 启用复选框功能
        self.EnableCheckBoxes(True)
        
        # 添加项目
        for i, choice in enumerate(self._choices):
            self.InsertItem(i, choice)
            # 设置初始选中状态
            self.CheckItem(i, self._checked_states[i])
    
    def _bind_events(self):
        """绑定事件处理"""
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self._on_item_selected)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self._on_item_activated)
        self.Bind(wx.EVT_LIST_KEY_DOWN, self._on_key_down)
        self.Bind(wx.EVT_CHAR, self._on_char)
    
    def _on_item_selected(self, event: wx.ListEvent):
        """项目选中事件"""
        index = event.GetIndex()
        if index >= 0 and index < len(self._choices):
            # 通知焦点变化
            self._notify_focus_change(index)
        event.Skip()
    
    def _on_item_activated(self, event: wx.ListEvent):
        """项目激活事件（双击或回车）"""
        index = event.GetIndex()
        if index >= 0 and index < len(self._choices):
            # 可以在这里添加双击或回车的处理逻辑
            pass
        event.Skip()
    
    def _on_key_down(self, event: wx.ListEvent):
        """键盘事件处理"""
        keycode = event.GetKeyCode()
        
        # 处理空格键
        if keycode == wx.WXK_SPACE:
            index = self.GetFocusedItem()
            if index >= 0 and index < len(self._choices):
                # 切换选中状态
                current_state = self.IsItemChecked(index)
                self.CheckItem(index, not current_state)
                self._checked_states[index] = not current_state
                
                # 通知状态变化
                self._notify_state_change(index)
                
                # 阻止默认处理
                return
        
        event.Skip()
    
    def _on_char(self, event: wx.KeyEvent):
        """字符输入事件处理"""
        keycode = event.GetKeyCode()
        
        # 处理上下光标键
        if keycode in [wx.WXK_UP, wx.WXK_DOWN]:
            old_focus = self.GetFocusedItem()
            event.Skip()  # 让默认处理先执行
            
            # 在默认处理后检查焦点是否变化
            wx.CallAfter(self._handle_focus_change, old_focus)
            return
        
        event.Skip()
    
    def _handle_focus_change(self, old_focus: int):
        """处理焦点变化"""
        try:
            new_focus = self.GetFocusedItem()
            if new_focus != old_focus and new_focus >= 0:
                # 通知焦点变化
                self._notify_focus_change(new_focus)
        except Exception:
            pass
    
    def _notify_focus_change(self, childId: int):
        """通知焦点变化"""
        try:
            if HAS_ACCESSIBILITY:
                accessible = self.GetAccessible()
                if accessible and hasattr(accessible, 'NotifyEvent'):
                    accessible.NotifyEvent(wx.accessibility.EVENT_OBJECT_FOCUS, childId)
        except Exception:
            pass
    
    def _notify_state_change(self, childId: int):
        """通知状态变化"""
        try:
            if HAS_ACCESSIBILITY:
                accessible = self.GetAccessible()
                if accessible and hasattr(accessible, 'NotifyEvent'):
                    accessible.NotifyEvent(wx.accessibility.EVENT_OBJECT_STATECHANGE, childId)
        except Exception:
            pass
    
    def GetAccessible(self) -> Optional[object]:
        """获取控件的无障碍对象"""
        try:
            if self._accessible is None:
                self._accessible = RoleListAccessible(self)
            return self._accessible
        except Exception:
            return None
    
    # 兼容 wx.CheckListBox 的接口方法
    def GetCount(self) -> int:
        """获取项目数量"""
        return self.GetItemCount()
    
    def GetString(self, index: int) -> str:
        """获取指定索引的文本"""
        if 0 <= index < self.GetItemCount():
            return self.GetItemText(index)
        return ""
    
    def IsChecked(self, index: int) -> bool:
        """检查指定索引的项目是否被选中"""
        if 0 <= index < self.GetItemCount():
            return self.IsItemChecked(index)
        return False
    
    def Check(self, index: int, check: bool = True):
        """设置指定索引项目的选中状态"""
        if 0 <= index < self.GetItemCount():
            self.CheckItem(index, check)
            self._checked_states[index] = check
            self._notify_state_change(index)
    
    def GetSelection(self) -> int:
        """获取当前选中的项目索引"""
        return self.GetFocusedItem()
    
    def SetSelection(self, index: int):
        """设置当前选中的项目"""
        if 0 <= index < self.GetItemCount():
            self.SetItemState(index, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
            self.SetItemState(index, wx.LIST_STATE_FOCUSED, wx.LIST_STATE_FOCUSED)
            self._notify_focus_change(index)
    
    def Clear(self):
        """清空列表"""
        self.DeleteAllItems()
        self._choices.clear()
        self._checked_states.clear()
    
    def Append(self, item: str):
        """添加项目"""
        index = self.GetItemCount()
        self._choices.append(item)
        self._checked_states.append(False)
        self.InsertItem(index, item)
        self.CheckItem(index, False)
    
    def AppendItems(self, items: List[str]):
        """批量添加项目"""
        for item in items:
            self.Append(item)
    
    def GetCheckedItems(self) -> List[int]:
        """获取所有选中项目的索引"""
        checked_indices = []
        for i in range(self.GetItemCount()):
            if self.IsItemChecked(i):
                checked_indices.append(i)
        return checked_indices
    
    def GetCheckedStrings(self) -> List[str]:
        """获取所有选中项目的文本"""
        checked_strings = []
        for i in range(self.GetItemCount()):
            if self.IsItemChecked(i):
                checked_strings.append(self.GetItemText(i))
        return checked_strings
    
    def SetCheckedItems(self, indices: List[int]):
        """批量设置选中状态"""
        for i in range(self.GetItemCount()):
            is_checked = i in indices
            self.CheckItem(i, is_checked)
            self._checked_states[i] = is_checked


class RoleListAccessible(object):
    """角色列表无障碍支持类"""
    
    def __init__(self, control):
        """初始化无障碍支持
        
        Args:
            control: 关联的wx.ListCtrl控件
        """
        self.control = control
    
    def GetName(self, childId: int = wx.ACCESSIBLE_SELF) -> str:
        """获取控件或子项的名称"""
        try:
            if childId == wx.ACCESSIBLE_SELF:
                # 返回整个控件的名称
                return self.control.GetName() or "语音角色列表"
            else:
                # 返回特定列表项的名称
                if 0 <= childId < self.control.GetItemCount():
                    item_text = self.control.GetItemText(childId)
                    is_checked = self.control.IsItemChecked(childId)
                    status = "已选中" if is_checked else "未选中"
                    return f"{item_text} {status}"
                return ""
        except Exception:
            return ""
    
    def GetRole(self, childId: int = wx.ACCESSIBLE_SELF) -> Any:
        """获取控件或子项的角色"""
        try:
            if childId == wx.ACCESSIBLE_SELF:
                # 整个控件是列表角色
                return wx.accessibility.ROLE_LIST
            else:
                # 列表项是列表项角色
                return wx.accessibility.ROLE_LISTITEM
        except Exception:
            return wx.accessibility.ROLE_SYSTEM_NOTHING
    
    def GetState(self, childId: int = wx.ACCESSIBLE_SELF) -> Any:
        """获取控件或子项的状态"""
        try:
            if childId == wx.ACCESSIBLE_SELF:
                # 整个控件的状态
                state = wx.accessibility.STATE_SYSTEM_FOCUSABLE
                if self.control.HasFocus():
                    state |= wx.accessibility.STATE_SYSTEM_FOCUSED
                if self.control.IsEnabled():
                    state |= wx.accessibility.STATE_SYSTEM_ENABLED
                return state
            else:
                # 列表项的状态
                state = wx.accessibility.STATE_SYSTEM_FOCUSABLE | wx.accessibility.STATE_SYSTEM_SELECTABLE
                if 0 <= childId < self.control.GetItemCount():
                    # 检查是否被选中
                    if self.control.IsItemChecked(childId):
                        state |= wx.accessibility.STATE_SYSTEM_CHECKED
                    
                    # 检查是否有焦点
                    if self.control.GetFocusedItem() == childId and self.control.HasFocus():
                        state |= wx.accessibility.STATE_SYSTEM_FOCUSED | wx.accessibility.STATE_SYSTEM_SELECTED
                
                return state
        except Exception:
            return wx.accessibility.STATE_SYSTEM_UNAVAILABLE
    
    def GetChildCount(self) -> int:
        """获取子项数量"""
        try:
            return self.control.GetItemCount()
        except Exception:
            return 0
    
    def GetChild(self, childId: int) -> Optional[object]:
        """获取指定子项的无障碍对象"""
        try:
            if 0 <= childId < self.control.GetItemCount():
                # 返回自身，因为我们处理所有子项
                return self
            return None
        except Exception:
            return None
    
    def GetDefaultAction(self, childId: int = wx.ACCESSIBLE_SELF) -> str:
        """获取默认操作"""
        try:
            if childId == wx.ACCESSIBLE_SELF:
                return ""
            else:
                # 列表项的默认操作是切换选中状态
                return "切换选中状态"
        except Exception:
            return ""
    
    def DoDefaultAction(self, childId: int = wx.ACCESSIBLE_SELF):
        """执行默认操作"""
        try:
            if childId != wx.ACCESSIBLE_SELF and 0 <= childId < self.control.GetItemCount():
                # 切换选中状态
                current_state = self.control.IsItemChecked(childId)
                self.control.CheckItem(childId, not current_state)
                
                # 触发事件通知无障碍状态变化
                self.NotifyEvent(wx.accessibility.EVENT_OBJECT_STATECHANGE, childId)
        except Exception:
            pass
    
    def NotifyEvent(self, event_type: int, childId: int = wx.ACCESSIBLE_SELF):
        """通知无障碍事件"""
        try:
            if HAS_ACCESSIBILITY and hasattr(self, 'NotifyWinEvent'):
                self.NotifyWinEvent(event_type, self.control.GetHWND(), wx.OBJID_CLIENT, childId)
        except Exception:
            pass