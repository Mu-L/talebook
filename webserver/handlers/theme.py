#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import json
import logging
import os
import re
import shutil
import tempfile
import zipfile
from urllib.parse import urljoin, urlparse

import requests

from webserver import loader
from webserver.handlers.base import BaseHandler, is_admin, js
from webserver.i18n import _
from webserver.models import InstalledTheme


CONF = loader.get_settings()

MAX_THEME_SIZE = 10 * 1024 * 1024  # 10MB
MAX_UNCOMPRESSED_THEME_SIZE = 100 * 1024 * 1024  # 100MB
_REDIRECT_CODES = {301, 302, 303, 307, 308}
_THEME_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")
_RESERVED_THEME_NAMES = {"active", "install", "activate"}


def is_allowed_url(url):
    parsed = urlparse(url)
    if parsed.scheme != "https":
        return False
    host = parsed.netloc.lower()
    allowed = CONF.get("THEME_ALLOWED_DOMAINS", [])
    return any(host == d or host.endswith("." + d) for d in allowed)


def is_valid_theme_name(name):
    return bool(_THEME_NAME_RE.match(name)) and name not in {".", ".."}


def get_theme_dir(themes_path, theme_name):
    themes_root = os.path.realpath(themes_path)
    theme_dir = os.path.realpath(os.path.join(themes_root, theme_name))
    if theme_dir == themes_root or not theme_dir.startswith(themes_root + os.sep):
        raise ValueError(_("非法路径"))
    return theme_dir


def normalize_component_url(theme_name, component_url):
    if not isinstance(component_url, str):
        raise ValueError(_("主题组件地址无效"))
    expected_prefix = "/static/themes/%s/" % theme_name
    parsed = urlparse(component_url)
    if parsed.scheme or parsed.netloc or not parsed.path.startswith(expected_prefix):
        raise ValueError(_("主题组件地址必须位于当前主题目录"))
    if ".." in parsed.path.split("/"):
        raise ValueError(_("主题组件地址无效"))
    return parsed.path


def normalize_components(theme_name, components):
    if components is None:
        return {}
    if not isinstance(components, dict):
        raise ValueError(_("theme.json 中 components 字段无效"))
    return {key: normalize_component_url(theme_name, value) for key, value in components.items()}


def download_theme_archive(download_url):
    current_url = download_url
    for hop in range(6):
        if not is_allowed_url(current_url):
            raise ValueError(_("重定向目标地址不在允许列表中"))
        resp = requests.get(current_url, timeout=30, stream=True, allow_redirects=False)
        resp.raise_for_status()
        if resp.status_code not in _REDIRECT_CODES:
            return resp
        redirect_url = resp.headers.get("Location", "")
        current_url = urljoin(current_url, redirect_url)
    raise ValueError(_("重定向次数过多"))


def safe_extract(zip_path, dest_dir, strip_prefix=""):
    """解压 ZIP 到 dest_dir，支持剥离存档根目录前缀，并防范路径穿越和 ZIP bomb。"""
    dest_dir = os.path.realpath(dest_dir)
    total_uncompressed = 0
    with zipfile.ZipFile(zip_path) as zf:
        for member in zf.infolist():
            total_uncompressed += member.file_size
            if total_uncompressed > MAX_UNCOMPRESSED_THEME_SIZE:
                raise ValueError(_("主题包解压后超过 100MB 限制"))

            filename = member.filename
            if strip_prefix and filename.startswith(strip_prefix):
                filename = filename[len(strip_prefix) :]
                if not filename:
                    continue  # 跳过存档根目录本身

            target = os.path.realpath(os.path.join(dest_dir, filename))
            if target != dest_dir and not target.startswith(dest_dir + os.sep):
                raise ValueError(_("路径穿越攻击: %s") % member.filename)

            if filename.endswith("/"):
                os.makedirs(target, exist_ok=True)
            else:
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with zf.open(member) as src, open(target, "wb") as dst:
                    dst.write(src.read())


def get_themes_path():
    path = CONF.get("themes_path", "/data/books/themes/")
    os.makedirs(path, exist_ok=True)
    return path


class ThemeListHandler(BaseHandler):
    @js
    def get(self):
        themes = self.session.query(InstalledTheme).order_by(InstalledTheme.installed_at.desc()).all()
        return {"err": "ok", "themes": [t.to_dict() for t in themes]}


class ThemeInstallHandler(BaseHandler):
    @js
    @is_admin
    def post(self):
        content = None

        if self.request.files and "theme_file" in self.request.files:
            file_info = self.request.files["theme_file"][0]
            content = file_info["body"]
            filename = file_info.get("filename", "")
            if not filename.lower().endswith(".zip"):
                return {"err": "params.invalid", "msg": _("只支持上传 ZIP 格式的主题包")}
            if len(content) > MAX_THEME_SIZE:
                return {"err": "params.invalid", "msg": _("主题包超过 10MB 限制")}
        else:
            try:
                body = json.loads(self.request.body)
            except (json.JSONDecodeError, TypeError):
                return {"err": "params.invalid", "msg": _("请求参数格式错误")}

            download_url = body.get("download_url", "").strip()
            if not download_url:
                return {"err": "params.invalid", "msg": _("缺少 download_url 参数")}

            if not is_allowed_url(download_url):
                return {"err": "params.invalid", "msg": _("不允许的下载地址，仅支持 GitHub/Gitee/jsDelivr")}

            try:
                resp = download_theme_archive(download_url)
            except ValueError as e:
                return {"err": "params.invalid", "msg": str(e)}
            except Exception as e:
                logging.warning("主题下载失败: %s", e)
                return {"err": "network.error", "msg": _("下载失败：%s") % str(e)}

            content = b""
            for chunk in resp.iter_content(chunk_size=8192):
                content += chunk
                if len(content) > MAX_THEME_SIZE:
                    return {"err": "params.invalid", "msg": _("主题包超过 10MB 限制")}

        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            if not zipfile.is_zipfile(tmp_path):
                return {"err": "params.invalid", "msg": _("文件不是有效的 ZIP 格式")}

            with zipfile.ZipFile(tmp_path) as zf:
                names = zf.namelist()
                theme_json_candidates = [n for n in names if n.endswith("theme.json") and n.count("/") <= 1]
                if not theme_json_candidates:
                    return {"err": "params.invalid", "msg": _("ZIP 包中缺少 theme.json 文件")}

                theme_json_path = theme_json_candidates[0]
                theme_meta = json.loads(zf.read(theme_json_path).decode("utf-8"))

            theme_name = theme_meta.get("name", "").strip()
            if not is_valid_theme_name(theme_name) or theme_name in _RESERVED_THEME_NAMES:
                return {"err": "params.invalid", "msg": _("theme.json 中 name 字段无效")}

            components = normalize_components(theme_name, theme_meta.get("components", {}))
            themes_path = get_themes_path()
            dest_dir = get_theme_dir(themes_path, theme_name)
            parent_dir = os.path.dirname(dest_dir)
            temp_dest = tempfile.mkdtemp(prefix=theme_name + ".", suffix=".tmp", dir=parent_dir)
            try:
                # 剥离 GitHub/Gitee 存档的根目录前缀（如 "repo-branch/"）
                strip_prefix = ""
                if "/" in theme_json_path:
                    strip_prefix = theme_json_path.rsplit("/", 1)[0] + "/"
                safe_extract(tmp_path, temp_dest, strip_prefix=strip_prefix)
                if os.path.isdir(dest_dir):
                    shutil.rmtree(dest_dir)
                os.replace(temp_dest, dest_dir)
            except Exception:
                if os.path.isdir(temp_dest):
                    shutil.rmtree(temp_dest)
                raise

        except ValueError as e:
            return {"err": "security.error", "msg": str(e)}
        except Exception as e:
            logging.error("主题安装失败: %s", e)
            return {"err": "install.error", "msg": _("安装失败：%s") % str(e)}
        finally:
            os.unlink(tmp_path)

        existing = self.session.query(InstalledTheme).filter(InstalledTheme.name == theme_name).first()
        if existing:
            existing.version = theme_meta.get("version", "")
            existing.author = theme_meta.get("author", "")
            existing.description = theme_meta.get("description", "")
            existing.data = {"components": components}
            existing.save()
            theme = existing
        else:
            theme = InstalledTheme(
                name=theme_name,
                version=theme_meta.get("version", ""),
                author=theme_meta.get("author", ""),
                description=theme_meta.get("description", ""),
            )
            theme.data = {"components": components}
            theme.save()

        return {"err": "ok", "msg": _("主题安装成功"), "theme": theme.to_dict()}


class ThemeActivateHandler(BaseHandler):
    @js
    @is_admin
    def post(self):
        try:
            body = json.loads(self.request.body)
        except (json.JSONDecodeError, TypeError):
            return {"err": "params.invalid", "msg": _("请求参数格式错误")}

        name = body.get("name", "").strip()

        if name:
            theme = self.session.query(InstalledTheme).filter(InstalledTheme.name == name).first()
            if not theme:
                return {"err": "not_found", "msg": _("主题不存在")}

        self.session.query(InstalledTheme).update({"active": False})
        if name:
            theme.active = True
            self.session.add(theme)
        self.session.commit()

        if name:
            CONF["ACTIVE_THEME"] = name
            return {"err": "ok", "msg": _("已激活主题：%s") % name, "theme": theme.to_dict()}

        CONF["ACTIVE_THEME"] = ""
        return {"err": "ok", "msg": _("已恢复默认主题")}


class ThemeDeleteHandler(BaseHandler):
    @js
    @is_admin
    def delete(self, name):
        theme = self.session.query(InstalledTheme).filter(InstalledTheme.name == name).first()
        if not theme:
            return {"err": "not_found", "msg": _("主题不存在")}

        if theme.active:
            CONF["ACTIVE_THEME"] = ""

        themes_path = get_themes_path()
        theme_dir = os.path.realpath(os.path.join(themes_path, name))
        if not theme_dir.startswith(os.path.realpath(themes_path) + os.sep):
            return {"err": "security.error", "msg": _("非法路径")}

        if os.path.isdir(theme_dir):
            shutil.rmtree(theme_dir)

        self.session.delete(theme)
        self.session.commit()
        return {"err": "ok", "msg": _("主题已删除")}


class ThemeActiveHandler(BaseHandler):
    """获取当前激活主题的信息（供前端初始化使用，无需登录）。"""

    @js
    def get(self):
        theme = self.session.query(InstalledTheme).filter(InstalledTheme.active == True).first()  # noqa: E712
        if not theme:
            return {"err": "ok", "theme": None}
        return {"err": "ok", "theme": theme.to_dict()}


def routes():
    return [
        (r"/api/themes", ThemeListHandler),
        (r"/api/themes/install", ThemeInstallHandler),
        (r"/api/themes/activate", ThemeActivateHandler),
        (r"/api/themes/active", ThemeActiveHandler),
        (r"/api/themes/([^/]+)", ThemeDeleteHandler),
    ]
