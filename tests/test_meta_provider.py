#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#
# 验证 NeoDB / 豆瓣V2 信息源 get_metadata_by_provider 的"应用选中条目"逻辑：
# 选择 refer 对话框中的结果后，应按 provider_value 重新匹配并构建完整元数据，
# 而不是直接返回本地原始 mi（否则 smart_update 等于用书自身覆盖自身）。

from unittest import TestCase, mock

from webserver.plugins.meta.douban_v2.plugin import DoubanV2MetaPlugin
from webserver.plugins.meta.neodb.plugin import NeodbMetaPlugin


class FakeMi:
    def __init__(self, title=None, isbn=None, cover_url=None):
        self.title = title
        self.isbn = isbn
        self.cover_url = cover_url


class TestNeodbProvider(TestCase):
    @mock.patch("webserver.plugins.meta.neodb.plugin.api.build_metadata")
    @mock.patch("webserver.plugins.meta.neodb.plugin.api.search")
    def test_matches_provider_value(self, m_search, m_build):
        m_search.return_value = [
            {"url": "https://neodb.social/book/AAA", "title": "A"},
            {"url": "https://neodb.social/book/BBB", "title": "B"},
        ]
        m_build.return_value = "BUILT"
        mi = FakeMi(title="书名")
        result = NeodbMetaPlugin().get_metadata_by_provider("https://neodb.social/book/BBB", mi)
        self.assertEqual(result, "BUILT")
        m_search.assert_called_once_with("书名", max_count=10)
        # 用匹配到的第二个条目（而非首个）构建完整元数据
        self.assertEqual(m_build.call_args.args[0]["url"], "https://neodb.social/book/BBB")

    @mock.patch("webserver.plugins.meta.neodb.plugin.api.get_cover")
    @mock.patch("webserver.plugins.meta.neodb.plugin.api.build_metadata")
    @mock.patch("webserver.plugins.meta.neodb.plugin.api.search")
    def test_no_match_falls_back_to_cover(self, m_search, m_build, m_cover):
        m_search.return_value = [{"url": "https://neodb.social/book/AAA"}]
        m_cover.return_value = ("jpg", b"x")
        mi = FakeMi(title="书名", cover_url="http://c/cover.jpg")
        result = NeodbMetaPlugin().get_metadata_by_provider("https://neodb.social/book/ZZZ", mi)
        self.assertIs(result, mi)
        m_build.assert_not_called()
        self.assertEqual(mi.cover_data, ("jpg", b"x"))

    @mock.patch("webserver.plugins.meta.neodb.plugin.api.search")
    def test_prefers_isbn_query(self, m_search):
        m_search.return_value = []
        mi = FakeMi(title="书名", isbn="9787000000000")
        NeodbMetaPlugin().get_metadata_by_provider("x", mi)
        m_search.assert_called_once_with("9787000000000", max_count=10)


class TestDoubanV2Provider(TestCase):
    @mock.patch("webserver.plugins.meta.douban_v2.plugin.api.build_metadata")
    @mock.patch("webserver.plugins.meta.douban_v2.plugin.api.search")
    def test_matches_by_id_via_isbn_search(self, m_search, m_build):
        m_search.return_value = ([{"id": 111}, {"id": 222}], "http://search")
        m_build.return_value = "BUILT"
        mi = FakeMi(title="标题", isbn="9787000000000")
        result = DoubanV2MetaPlugin().get_metadata_by_provider("222", mi)
        self.assertEqual(result, "BUILT")
        # 初次可能用 ISBN 搜到的条目，应按 ISBN 重搜而非仅按标题
        m_search.assert_called_once_with("9787000000000", max_count=10)
        self.assertEqual(m_build.call_args.args[0]["id"], 222)

    @mock.patch("webserver.plugins.meta.douban_v2.plugin.api.get_cover")
    @mock.patch("webserver.plugins.meta.douban_v2.plugin.api.build_metadata")
    @mock.patch("webserver.plugins.meta.douban_v2.plugin.api.search")
    def test_no_match_falls_back_to_cover(self, m_search, m_build, m_cover):
        m_search.return_value = ([{"id": 111}], "http://search")
        m_cover.return_value = ("jpg", b"x")
        mi = FakeMi(title="标题", cover_url="http://c.jpg")
        result = DoubanV2MetaPlugin().get_metadata_by_provider("999", mi)
        self.assertIs(result, mi)
        m_build.assert_not_called()
        self.assertEqual(mi.cover_data, ("jpg", b"x"))
