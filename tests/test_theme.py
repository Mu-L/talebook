#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import io
import json
import os
import zipfile
from unittest import mock

from tests import test_main
from tests.test_main import TestApp, TestWithAdminUser, get_db
from tests.test_main import setUpModule as init
from webserver.handlers import theme as theme_module
from webserver import models


def setUpModule():
    init()
    # users.db fixture 中不含 installed_themes 表，需在测试前创建
    models.user_syncdb(test_main._app._engine)
    theme_module.CONF["ACTIVE_THEME"] = ""


def make_theme_zip(theme_name="test-theme", version="1.0.0"):
    """构造一个最小有效主题 ZIP 包，返回 bytes。"""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        theme_json = {
            "name": theme_name,
            "version": version,
            "author": "test",
            "description": "测试主题",
            "components": {
                "AppHeader": f"/static/themes/{theme_name}/components/AppHeader.js"
            },
        }
        zf.writestr("theme.json", json.dumps(theme_json))
        zf.writestr(f"components/AppHeader.js", "export default {};")
    return buf.getvalue()


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
    def test_install_requires_admin(self):
        body = json.dumps({"download_url": "https://github.com/test/theme/archive/main.zip"})
        d = self.json("/api/themes/install", method="POST", body=body)
        self.assertEqual(d["err"], "user.need_login")

    def test_activate_requires_admin(self):
        body = json.dumps({"name": "test-theme"})
        d = self.json("/api/themes/activate", method="POST", body=body)
        self.assertEqual(d["err"], "user.need_login")

    def test_delete_requires_admin(self):
        d = self.json("/api/themes/test-theme", method="DELETE")
        self.assertEqual(d["err"], "user.need_login")


class TestThemeAdmin(TestWithAdminUser):
    def setUp(self):
        super().setUp()
        theme_module.CONF["ACTIVE_THEME"] = ""
        # 清理测试残留主题
        session = get_db()
        session.query(models.InstalledTheme).filter(
            models.InstalledTheme.name.in_(["test-theme", "test-theme-v2"])
        ).delete(synchronize_session=False)
        session.commit()

    def tearDown(self):
        theme_module.CONF["ACTIVE_THEME"] = ""
        session = get_db()
        session.query(models.InstalledTheme).filter(
            models.InstalledTheme.name.in_(["test-theme", "test-theme-v2"])
        ).delete(synchronize_session=False)
        session.commit()
        super().tearDown()

    def _create_theme(self, name="test-theme"):
        """直接在数据库中插入一个测试主题。"""
        session = get_db()
        theme = models.InstalledTheme(name=name, version="1.0.0", author="test")
        theme.data = {"components": {}}
        session.add(theme)
        session.commit()
        return theme

    def test_list_themes(self):
        d = self.json("/api/themes")
        self.assertEqual(d["err"], "ok")
        self.assertIsInstance(d["themes"], list)

    def test_list_includes_builtin_themes(self):
        d = self.json("/api/themes")
        self.assertEqual(d["err"], "ok")
        builtin_names = {theme["name"] for theme in d["themes"] if theme.get("builtin")}
        builtin_display_names = {theme["name"]: theme["display_name"] for theme in d["themes"] if theme.get("builtin")}
        self.assertEqual(
            builtin_names,
            {"cloudflare-radar", "mybooks-midnight", "hacker-news-compact"},
        )
        self.assertEqual(
            builtin_display_names,
            {
                "cloudflare-radar": "蓝色科技主题",
                "mybooks-midnight": "灰色紧凑主题",
                "hacker-news-compact": "极简主题",
            },
        )

    def test_install_blocked_url(self):
        """非白名单 URL 必须被拒绝。"""
        body = json.dumps({"download_url": "https://evil.com/theme.zip"})
        d = self.json("/api/themes/install", method="POST", body=body)
        self.assertEqual(d["err"], "params.invalid")

    def test_install_http_url_blocked(self):
        """HTTP (非 HTTPS) URL 必须被拒绝。"""
        body = json.dumps({"download_url": "http://github.com/test/theme.zip"})
        d = self.json("/api/themes/install", method="POST", body=body)
        self.assertEqual(d["err"], "params.invalid")

    def test_install_missing_url(self):
        body = json.dumps({})
        d = self.json("/api/themes/install", method="POST", body=body)
        self.assertEqual(d["err"], "params.invalid")

    @mock.patch("webserver.handlers.theme._assert_public_host")
    @mock.patch("webserver.handlers.theme.requests.get")
    def test_install_reserved_name_rejected(self, mock_get, mock_assert_host):
        """主题名为保留名称（active/install/activate）时必须拒绝，避免路由冲突。"""
        for reserved in ("active", "install", "activate"):
            zip_bytes = make_theme_zip(reserved)
            mock_response = mock.MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_response.status_code = 200
            mock_response.iter_content.return_value = iter([zip_bytes])
            mock_get.return_value = mock_response

            body = json.dumps({"download_url": "https://github.com/talebook/test-theme/archive/main.zip"})
            d = self.json("/api/themes/install", method="POST", body=body)
            self.assertEqual(d["err"], "params.invalid", f"保留名称 '{reserved}' 应被拒绝")

    @mock.patch("webserver.handlers.theme._assert_public_host")
    @mock.patch("webserver.handlers.theme.requests.get")
    def test_install_dot_theme_name_rejected(self, mock_get, mock_assert_host):
        """主题名为 . 时必须拒绝，避免目标目录变成 themes 根目录。"""
        zip_bytes = make_theme_zip(".")
        mock_response = mock.MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.status_code = 200
        mock_response.iter_content.return_value = iter([zip_bytes])
        mock_get.return_value = mock_response

        body = json.dumps({"download_url": "https://github.com/talebook/test-theme/archive/main.zip"})
        d = self.json("/api/themes/install", method="POST", body=body)
        self.assertEqual(d["err"], "params.invalid")

    @mock.patch("webserver.handlers.theme._assert_public_host")
    @mock.patch("webserver.handlers.theme.requests.get")
    def test_install_external_component_url_rejected(self, mock_get, mock_assert_host):
        """组件地址必须限定在本主题的 /static/themes/<name>/ 目录下。"""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            theme_json = {
                "name": "test-theme",
                "version": "1.0.0",
                "components": {"AppHeader": "https://evil.com/AppHeader.js"},
            }
            zf.writestr("theme.json", json.dumps(theme_json))
            zf.writestr("components/AppHeader.js", "export default {};")

        mock_response = mock.MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.status_code = 200
        mock_response.iter_content.return_value = iter([buf.getvalue()])
        mock_get.return_value = mock_response

        body = json.dumps({"download_url": "https://github.com/talebook/test-theme/archive/main.zip"})
        d = self.json("/api/themes/install", method="POST", body=body)
        self.assertEqual(d["err"], "security.error")

    @mock.patch("webserver.handlers.theme._assert_public_host")
    @mock.patch("webserver.handlers.theme.requests.get")
    def test_install_ignores_suffix_named_fake_manifest(self, mock_get, mock_assert_host):
        """只允许根目录或一级目录下 basename 精确为 theme.json 的 manifest。"""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("old-theme.json", json.dumps({
                "name": "test-theme",
                "version": "1.0.0",
                "author": "test",
                "description": "fake",
                "components": {"AppHeader": "/static/themes/test-theme/components/AppHeader.js"},
            }))
            zf.writestr("components/AppHeader.js", "export default {};")

        mock_response = mock.MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.status_code = 200
        mock_response.iter_content.return_value = iter([buf.getvalue()])
        mock_get.return_value = mock_response

        body = json.dumps({"download_url": "https://github.com/talebook/test-theme/archive/main.zip"})
        d = self.json("/api/themes/install", method="POST", body=body)
        self.assertEqual(d["err"], "params.invalid")

    @mock.patch("webserver.handlers.theme._assert_public_host")
    @mock.patch("webserver.handlers.theme.requests.get")
    def test_install_uses_exact_nested_theme_manifest(self, mock_get, mock_assert_host):
        """GitHub/Gitee 存档的一层根目录下 theme.json 仍应可安装。"""
        import tempfile

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("repo-main/old-theme.json", json.dumps({"name": "wrong"}))
            zf.writestr("repo-main/theme.json", json.dumps({
                "name": "test-theme",
                "version": "1.0.0",
                "author": "test",
                "description": "ok",
                "components": {"AppHeader": "/static/themes/test-theme/components/AppHeader.js"},
            }))
            zf.writestr("repo-main/components/AppHeader.js", "export default {};")

        mock_response = mock.MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.status_code = 200
        mock_response.iter_content.return_value = iter([buf.getvalue()])
        mock_get.return_value = mock_response

        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch("webserver.handlers.theme.get_themes_path", return_value=tmpdir):
                with mock.patch("webserver.handlers.theme.safe_extract"):
                    body = json.dumps({"download_url": "https://github.com/talebook/test-theme/archive/main.zip"})
                    d = self.json("/api/themes/install", method="POST", body=body)

        self.assertEqual(d["err"], "ok")
        self.assertEqual(d["theme"]["name"], "test-theme")

    @mock.patch("webserver.handlers.theme._assert_public_host")
    @mock.patch("webserver.handlers.theme.requests.get")
    def test_install_success(self, mock_get, mock_assert_host):
        """正常安装流程：ZIP 包合法，主题应被记录到数据库。"""
        import tempfile

        zip_bytes = make_theme_zip("test-theme")

        mock_response = mock.MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.iter_content.return_value = iter([zip_bytes])
        mock_response.url = "https://github.com/talebook/test-theme/archive/main.zip"
        mock_get.return_value = mock_response

        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch("webserver.handlers.theme.get_themes_path", return_value=tmpdir):
                with mock.patch("webserver.handlers.theme.safe_extract"):
                    body = json.dumps({"download_url": "https://github.com/talebook/test-theme/archive/main.zip"})
                    d = self.json("/api/themes/install", method="POST", body=body)

        self.assertEqual(d["err"], "ok")
        self.assertIn("theme", d)
        self.assertEqual(d["theme"]["name"], "test-theme")

    @mock.patch("webserver.handlers.theme._assert_public_host")
    @mock.patch("webserver.handlers.theme.requests.get")
    def test_install_oversized_rejected(self, mock_get, mock_assert_host):
        """超过 10MB 的主题包必须被拒绝。"""
        big_chunk = b"x" * (11 * 1024 * 1024)

        mock_response = mock.MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.iter_content.return_value = iter([big_chunk])
        mock_response.url = "https://github.com/talebook/big-theme/archive/main.zip"
        mock_get.return_value = mock_response

        body = json.dumps({"download_url": "https://github.com/talebook/big-theme/archive/main.zip"})
        d = self.json("/api/themes/install", method="POST", body=body)
        self.assertEqual(d["err"], "params.invalid")

    @mock.patch("webserver.handlers.theme._assert_public_host")
    @mock.patch("webserver.handlers.theme.requests.get")
    def test_install_redirect_ssrf_blocked(self, mock_get, mock_assert_host):
        """重定向到非白名单域名必须被拒绝（逐跳校验 Location）。"""
        mock_response = mock.MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.status_code = 302
        mock_response.headers = {"Location": "http://169.254.169.254/latest/meta-data/"}
        mock_get.return_value = mock_response

        body = json.dumps({"download_url": "https://github.com/talebook/theme/archive/main.zip"})
        d = self.json("/api/themes/install", method="POST", body=body)
        self.assertEqual(d["err"], "params.invalid")

    @mock.patch("webserver.handlers.theme._assert_public_host")
    @mock.patch("webserver.handlers.theme.requests.get")
    def test_install_allowed_redirect(self, mock_get, mock_assert_host):
        """重定向到白名单域名（如 codeload.github.com）应正常完成安装。"""
        import tempfile

        zip_bytes = make_theme_zip("test-theme")

        # 第一次调用返回 302 重定向到 codeload.github.com
        redirect_resp = mock.MagicMock()
        redirect_resp.raise_for_status.return_value = None
        redirect_resp.status_code = 302
        redirect_resp.headers = {"Location": "https://codeload.github.com/talebook/test-theme/zip/refs/heads/main"}

        # 第二次调用（跟随重定向）返回实际内容
        final_resp = mock.MagicMock()
        final_resp.raise_for_status.return_value = None
        final_resp.status_code = 200
        final_resp.iter_content.return_value = iter([zip_bytes])

        mock_get.side_effect = [redirect_resp, final_resp]

        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch("webserver.handlers.theme.get_themes_path", return_value=tmpdir):
                with mock.patch("webserver.handlers.theme.safe_extract"):
                    body = json.dumps({"download_url": "https://github.com/talebook/test-theme/archive/main.zip"})
                    d = self.json("/api/themes/install", method="POST", body=body)

        self.assertEqual(d["err"], "ok")
        self.assertEqual(d["theme"]["name"], "test-theme")

    @mock.patch("webserver.handlers.theme._assert_public_host")
    @mock.patch("webserver.handlers.theme.requests.get")
    def test_failed_reinstall_keeps_existing_files(self, mock_get, mock_assert_host):
        """重装解压失败时，不应删除当前正在服务的旧主题目录。"""
        import tempfile

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("theme.json", json.dumps({
                "name": "test-theme",
                "version": "2.0.0",
                "components": {"AppHeader": "/static/themes/test-theme/components/AppHeader.js"},
            }))
            zf.writestr("../evil.js", "bad")

        mock_response = mock.MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.status_code = 200
        mock_response.iter_content.return_value = iter([buf.getvalue()])
        mock_get.return_value = mock_response

        with tempfile.TemporaryDirectory() as tmpdir:
            theme_dir = os.path.join(tmpdir, "test-theme")
            os.makedirs(theme_dir)
            old_file = os.path.join(theme_dir, "old.js")
            with open(old_file, "w") as f:
                f.write("old")

            with mock.patch("webserver.handlers.theme.get_themes_path", return_value=tmpdir):
                body = json.dumps({"download_url": "https://github.com/talebook/test-theme/archive/main.zip"})
                d = self.json("/api/themes/install", method="POST", body=body)

            self.assertEqual(d["err"], "security.error")
            self.assertTrue(os.path.exists(old_file))

    def test_activate_not_found(self):
        body = json.dumps({"name": "nonexistent-theme"})
        d = self.json("/api/themes/activate", method="POST", body=body)
        self.assertEqual(d["err"], "not_found")

    def test_activate_builtin_theme(self):
        body = json.dumps({"name": "cloudflare-radar"})
        with mock.patch("webserver.handlers.theme.save_active_theme") as mock_save_active_theme:
            d = self.json("/api/themes/activate", method="POST", body=body)
        self.assertEqual(d["err"], "ok")
        self.assertEqual(d["theme"]["name"], "cloudflare-radar")
        self.assertTrue(d["theme"]["active"])
        self.assertTrue(d["theme"]["builtin"])
        mock_save_active_theme.assert_called_once_with("cloudflare-radar")

        theme_module.CONF["ACTIVE_THEME"] = "cloudflare-radar"

        active = self.json("/api/themes/active")
        self.assertEqual(active["err"], "ok")
        self.assertEqual(active["theme"]["name"], "cloudflare-radar")
        self.assertTrue(active["theme"]["active"])
        self.assertTrue(active["theme"]["builtin"])

    def test_activate_and_deactivate(self):
        self._create_theme("test-theme")

        body = json.dumps({"name": "test-theme"})
        with mock.patch("webserver.handlers.theme.save_active_theme") as mock_save_active_theme:
            d = self.json("/api/themes/activate", method="POST", body=body)
        self.assertEqual(d["err"], "ok")
        self.assertEqual(d["theme"]["name"], "test-theme")
        self.assertTrue(d["theme"]["active"])
        mock_save_active_theme.assert_called_once_with("test-theme")

        # 再次激活默认（空 name）
        body = json.dumps({"name": ""})
        with mock.patch("webserver.handlers.theme.save_active_theme") as mock_save_active_theme:
            d = self.json("/api/themes/activate", method="POST", body=body)
        self.assertEqual(d["err"], "ok")
        mock_save_active_theme.assert_called_once_with("")

    def test_delete_not_found(self):
        d = self.json("/api/themes/nonexistent", method="DELETE")
        self.assertEqual(d["err"], "not_found")

    def test_delete_builtin_theme_rejected(self):
        d = self.json("/api/themes/cloudflare-radar", method="DELETE")
        self.assertEqual(d["err"], "params.invalid")

    def test_delete_theme(self):
        import tempfile

        self._create_theme("test-theme")

        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch("webserver.handlers.theme.get_themes_path", return_value=tmpdir):
                d = self.json("/api/themes/test-theme", method="DELETE")

        self.assertEqual(d["err"], "ok")

        # 验证已从数据库删除
        session = get_db()
        theme = session.query(models.InstalledTheme).filter(models.InstalledTheme.name == "test-theme").first()
        self.assertIsNone(theme)

    def test_active_theme_endpoint(self):
        """激活后 /api/themes/active 应返回对应主题。"""
        self._create_theme("test-theme")
        body = json.dumps({"name": "test-theme"})
        self.json("/api/themes/activate", method="POST", body=body)

        d = self.json("/api/themes/active")
        self.assertEqual(d["err"], "ok")
        self.assertIsNotNone(d["theme"])
        self.assertEqual(d["theme"]["name"], "test-theme")


class TestSafeExtract(TestApp):
    def test_safe_extract_blocks_path_traversal(self):
        """safe_extract 必须阻止路径穿越攻击（ZipSlip）。"""
        import tempfile

        from webserver.handlers.theme import safe_extract

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            info = zipfile.ZipInfo("../../etc/passwd")
            zf.writestr(info, "malicious content")

        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, "evil.zip")
            with open(zip_path, "wb") as f:
                f.write(buf.getvalue())

            dest = os.path.join(tmpdir, "dest")
            os.makedirs(dest)

            with self.assertRaises(ValueError):
                safe_extract(zip_path, dest)

    def test_safe_extract_normal(self):
        """safe_extract 应正常解压合法 ZIP。"""
        import tempfile

        from webserver.handlers.theme import safe_extract

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("theme.json", '{"name": "ok"}')
            zf.writestr("components/Header.js", "export default {};")

        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, "theme.zip")
            with open(zip_path, "wb") as f:
                f.write(buf.getvalue())

            dest = os.path.join(tmpdir, "dest")
            os.makedirs(dest)
            safe_extract(zip_path, dest)
            self.assertTrue(os.path.exists(os.path.join(dest, "theme.json")))

    def test_safe_extract_strip_prefix(self):
        """safe_extract 应剥离 GitHub 存档根目录前缀（如 'repo-main/'）。"""
        import tempfile

        from webserver.handlers.theme import safe_extract

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr(zipfile.ZipInfo("repo-main/"), "")  # 目录条目
            zf.writestr("repo-main/theme.json", '{"name": "ok"}')
            zf.writestr("repo-main/components/Header.js", "export default {};")

        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, "theme.zip")
            with open(zip_path, "wb") as f:
                f.write(buf.getvalue())

            dest = os.path.join(tmpdir, "dest")
            os.makedirs(dest)
            safe_extract(zip_path, dest, strip_prefix="repo-main/")
            self.assertTrue(os.path.exists(os.path.join(dest, "theme.json")))
            self.assertTrue(os.path.exists(os.path.join(dest, "components", "Header.js")))
            self.assertFalse(os.path.exists(os.path.join(dest, "repo-main")))

    def test_safe_extract_zip_bomb_blocked(self):
        """safe_extract 必须阻止 ZIP bomb（解压后超过大小限制）。"""
        import tempfile

        from webserver.handlers import theme as theme_module
        from webserver.handlers.theme import safe_extract

        # 暂时调低限制，便于用小数据测试
        original_limit = theme_module.MAX_UNCOMPRESSED_THEME_SIZE
        theme_module.MAX_UNCOMPRESSED_THEME_SIZE = 100
        try:
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w") as zf:
                zf.writestr("file1.txt", "x" * 60)
                zf.writestr("file2.txt", "y" * 60)  # 合计 120 > 100

            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = os.path.join(tmpdir, "bomb.zip")
                with open(zip_path, "wb") as f:
                    f.write(buf.getvalue())

                dest = os.path.join(tmpdir, "dest")
                os.makedirs(dest)
                with self.assertRaises(ValueError):
                    safe_extract(zip_path, dest)
        finally:
            theme_module.MAX_UNCOMPRESSED_THEME_SIZE = original_limit


class TestIsAllowedUrl(TestApp):
    def test_allowed_domains(self):
        from webserver.handlers.theme import is_allowed_url

        self.assertTrue(is_allowed_url("https://github.com/talebook/theme.zip"))
        self.assertTrue(is_allowed_url("https://raw.githubusercontent.com/talebook/theme/main/theme.zip"))
        self.assertTrue(is_allowed_url("https://codeload.github.com/talebook/theme/zip/refs/heads/main"))
        self.assertTrue(is_allowed_url("https://gitee.com/talebook/theme.zip"))
        self.assertTrue(is_allowed_url("https://cdn.jsdelivr.net/gh/talebook/theme@main/theme.zip"))

    def test_blocked_domains(self):
        from webserver.handlers.theme import is_allowed_url

        self.assertFalse(is_allowed_url("https://evil.com/theme.zip"))
        self.assertFalse(is_allowed_url("https://github.com.evil.com/theme.zip"))
        self.assertFalse(is_allowed_url("http://github.com/theme.zip"))
        self.assertFalse(is_allowed_url("ftp://github.com/theme.zip"))
        self.assertFalse(is_allowed_url(""))
