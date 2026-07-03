#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import json
from unittest import mock

from tests.test_main import TestApp, TestWithAdminUser
from tests.test_main import setUpModule as init
from webserver.handlers import theme as theme_module


def setUpModule():
    init()
    theme_module.CONF["ACTIVE_THEME"] = ""


class TestThemeListAnonymous(TestApp):
    def test_list_themes_anonymous(self):
        """未登录用户可以获取主题列表（GET /api/themes）。"""
        d = self.json("/api/themes")
        self.assertEqual(d["err"], "ok")
        self.assertIn("themes", d)
        self.assertIsInstance(d["themes"], list)

    def test_active_theme_anonymous(self):
        """未登录用户可以获取当前激活主题（GET /api/themes/active）。"""
        d = self.json("/api/themes/active")
        self.assertEqual(d["err"], "ok")
        self.assertIn("theme", d)


class TestThemeAnonymousRestrict(TestApp):
    def test_activate_requires_admin(self):
        body = json.dumps({"name": "graphite"})
        d = self.json("/api/themes/activate", method="POST", body=body)
        self.assertEqual(d["err"], "user.need_login")


class TestThemeAdmin(TestWithAdminUser):
    def setUp(self):
        super().setUp()
        theme_module.CONF["ACTIVE_THEME"] = ""

    def tearDown(self):
        theme_module.CONF["ACTIVE_THEME"] = ""
        super().tearDown()

    def test_list_themes(self):
        d = self.json("/api/themes")
        self.assertEqual(d["err"], "ok")
        self.assertIsInstance(d["themes"], list)

    def test_list_only_builtin_themes(self):
        d = self.json("/api/themes")
        self.assertEqual(d["err"], "ok")
        builtin = [theme for theme in d["themes"] if theme.get("builtin")]
        # 只支持内置主题：列表里不应出现任何非内置主题
        self.assertEqual(len(builtin), len(d["themes"]))
        builtin_names = {theme["name"] for theme in builtin}
        builtin_display_names = {theme["name"]: theme["display_name"] for theme in builtin}
        self.assertEqual(
            builtin_names,
            {"brass", "graphite", "light-gray", "warm-red", "minimal"},
        )
        self.assertEqual(
            builtin_display_names,
            {
                "brass": "黄铜主题",
                "graphite": "石墨主题",
                "light-gray": "浅灰主题",
                "warm-red": "暖红主题",
                "minimal": "极简主题",
            },
        )
        # 内置主题次序固定：黄铜 → 石墨 → 浅灰 → 暖红 → 极简
        self.assertEqual(
            [theme["name"] for theme in builtin],
            ["brass", "graphite", "light-gray", "warm-red", "minimal"],
        )

    def test_activate_not_found(self):
        body = json.dumps({"name": "nonexistent-theme"})
        d = self.json("/api/themes/activate", method="POST", body=body)
        self.assertEqual(d["err"], "not_found")

    def test_activate_builtin_theme(self):
        body = json.dumps({"name": "graphite"})
        with mock.patch("webserver.handlers.theme.save_active_theme") as mock_save_active_theme:
            d = self.json("/api/themes/activate", method="POST", body=body)
        self.assertEqual(d["err"], "ok")
        self.assertEqual(d["theme"]["name"], "graphite")
        self.assertTrue(d["theme"]["active"])
        self.assertTrue(d["theme"]["builtin"])
        mock_save_active_theme.assert_called_once_with("graphite")

        theme_module.CONF["ACTIVE_THEME"] = "graphite"

        active = self.json("/api/themes/active")
        self.assertEqual(active["err"], "ok")
        self.assertEqual(active["theme"]["name"], "graphite")
        self.assertTrue(active["theme"]["active"])
        self.assertTrue(active["theme"]["builtin"])

    def test_activate_and_deactivate(self):
        body = json.dumps({"name": "brass"})
        with mock.patch("webserver.handlers.theme.save_active_theme") as mock_save_active_theme:
            d = self.json("/api/themes/activate", method="POST", body=body)
        self.assertEqual(d["err"], "ok")
        self.assertEqual(d["theme"]["name"], "brass")
        self.assertTrue(d["theme"]["active"])
        mock_save_active_theme.assert_called_once_with("brass")

        # 再次激活默认（空 name）：恢复默认，不返回 theme
        body = json.dumps({"name": ""})
        with mock.patch("webserver.handlers.theme.save_active_theme") as mock_save_active_theme:
            d = self.json("/api/themes/activate", method="POST", body=body)
        self.assertEqual(d["err"], "ok")
        mock_save_active_theme.assert_called_once_with("")
        self.assertNotIn("theme", d)

    def test_active_theme_endpoint(self):
        """激活内置主题后 /api/themes/active 应返回对应主题。"""
        theme_module.CONF["ACTIVE_THEME"] = "warm-red"
        d = self.json("/api/themes/active")
        self.assertEqual(d["err"], "ok")
        self.assertEqual(d["theme"]["name"], "warm-red")
        self.assertTrue(d["theme"]["active"])
        self.assertTrue(d["theme"]["builtin"])

    def test_active_theme_default_when_unset(self):
        """未设置激活主题时 /api/themes/active 返回 None。"""
        theme_module.CONF["ACTIVE_THEME"] = ""
        d = self.json("/api/themes/active")
        self.assertEqual(d["err"], "ok")
        self.assertIsNone(d["theme"])
