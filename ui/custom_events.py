#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自定义事件模块
定义应用程序中使用的所有自定义事件
"""

import wx
import wx.lib.newevent

# 创建自定义事件
RoleUpdateEvent, EVT_ROLE_UPDATE = wx.lib.newevent.NewEvent()
ScanCompleteEvent, EVT_SCAN_COMPLETE = wx.lib.newevent.NewEvent()
ProviderUpdateEvent, EVT_PROVIDER_UPDATE = wx.lib.newevent.NewEvent()