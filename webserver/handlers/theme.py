#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import json
import logging

from webserver import loader
from webserver.handlers.base import BaseHandler, is_admin, js
from webserver.i18n import _


CONF = loader.get_settings()

BUILTIN_THEMES = [
    {
        "id": "builtin-brass",
        "name": "brass",
        "display_name": _("黄铜主题"),
        "version": "1.0.0",
        "author": "Talebook",
        "description": _("暖褐炭灰打底，一线黄铜勾勒轮廓，衬线书名沉静内敛——像台灯下摊开的一册旧书，最宜夜里慢读细品。"),
        "installed_at": None,
        "builtin": True,
        "components": {
            "AppHeader": "builtin:brass/AppHeader",
            "AppFooter": "builtin:brass/AppFooter",
        },
    },
    {
        "id": "builtin-graphite",
        "name": "graphite",
        "display_name": _("石墨主题"),
        "version": "1.0.0",
        "author": "Talebook",
        "description": _("冷调蓝灰如石墨般沉着，墨蓝作唯一亮色，选中项亮起一道细边——信息井然有序，久看不觉刺眼。"),
        "installed_at": None,
        "builtin": True,
        "components": {
            "AppHeader": "builtin:graphite/AppHeader",
            "AppFooter": "builtin:graphite/AppFooter",
        },
    },
    {
        "id": "builtin-light-gray",
        "name": "light-gray",
        "display_name": _("浅灰主题"),
        "version": "1.0.0",
        "author": "Talebook",
        "description": _("通透的高级浅灰，低饱和配色搭紧凑侧栏，清爽而不喧宾夺主——日常打理书库，久对屏幕也轻松。"),
        "installed_at": None,
        "builtin": True,
        "components": {
            "AppHeader": "builtin:light-gray/AppHeader",
            "AppFooter": "builtin:light-gray/AppFooter",
        },
    },
    {
        "id": "builtin-warm-red",
        "name": "warm-red",
        "display_name": _("暖红主题"),
        "version": "1.0.0",
        "author": "Talebook",
        "description": _("微黄纸感的明亮底色，牛血红点题，侧栏以虚线分行如旧时图书馆的索引卡——带着纸页与目录的温度。"),
        "installed_at": None,
        "builtin": True,
        "components": {
            "AppHeader": "builtin:warm-red/AppHeader",
            "AppFooter": "builtin:warm-red/AppFooter",
        },
    },
    {
        "id": "builtin-minimal",
        "name": "minimal",
        "display_name": _("极简主题"),
        "version": "1.0.0",
        "author": "Talebook",
        "description": _("去尽多余装饰，只留文字与留白，小字号、高密度——明暗两色皆为一目十行的快速浏览而生。"),
        "installed_at": None,
        "builtin": True,
        "components": {
            "AppHeader": "builtin:minimal/AppHeader",
            "AppFooter": "builtin:minimal/AppFooter",
        },
    },
]
BUILTIN_THEME_MAP = {theme["name"]: theme for theme in BUILTIN_THEMES}


def get_builtin_theme(name):
    theme = BUILTIN_THEME_MAP.get(name)
    if not theme:
        return None
    data = dict(theme)
    data["components"] = dict(theme["components"])
    data["active"] = CONF.get("ACTIVE_THEME") == name
    return data


def list_builtin_themes():
    return [get_builtin_theme(theme["name"]) for theme in BUILTIN_THEMES]


def save_active_theme(name):
    CONF["ACTIVE_THEME"] = name
    CONF.dumpfile()


class ThemeListHandler(BaseHandler):
    @js
    def get(self):
        return {"err": "ok", "themes": list_builtin_themes()}


class ThemeActivateHandler(BaseHandler):
    @js
    @is_admin
    def post(self):
        try:
            body = json.loads(self.request.body)
        except (json.JSONDecodeError, TypeError):
            return {"err": "params.invalid", "msg": _("请求参数格式错误")}

        name = body.get("name", "").strip()

        if not name:
            try:
                save_active_theme("")
            except Exception as exc:
                logging.exception("failed to clear active theme")
                return {"err": "file.permission", "msg": _("保存主题配置失败：%s") % str(exc)}
            return {"err": "ok", "msg": _("已恢复默认主题")}

        theme = get_builtin_theme(name)
        if not theme:
            return {"err": "not_found", "msg": _("主题不存在")}

        try:
            save_active_theme(name)
        except Exception as exc:
            logging.exception("failed to save active theme")
            return {"err": "file.permission", "msg": _("保存主题配置失败：%s") % str(exc)}

        theme["active"] = True
        return {"err": "ok", "msg": _("已激活主题：%s") % name, "theme": theme}


class ThemeActiveHandler(BaseHandler):
    """获取当前激活主题的信息（供前端初始化使用，无需登录）。"""

    @js
    def get(self):
        active_theme_name = CONF.get("ACTIVE_THEME")
        if active_theme_name in BUILTIN_THEME_MAP:
            return {"err": "ok", "theme": get_builtin_theme(active_theme_name)}
        return {"err": "ok", "theme": None}


def routes():
    return [
        (r"/api/themes", ThemeListHandler),
        (r"/api/themes/activate", ThemeActivateHandler),
        (r"/api/themes/active", ThemeActiveHandler),
    ]
