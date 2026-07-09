#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""Tests for the WebDAV service endpoint (/books/).

These tests require the optional ``wsgidav`` dependency. When it is not
installed (e.g. local dev without the extra), the whole module is skipped so
it never blocks the default test run.

Run with the dependency installed: ``pip install -r requirements.txt``.
"""

import logging

import pytest


pytest.importorskip("wsgidav")

from tests.test_main import TestApp  # noqa: E402
from tests.test_main import setUpModule as init


logger = logging.getLogger(__name__)


def setUpModule():
    init()


class TestWebDav(TestApp):
    def _auth_header(self, username, password):
        token = "%s:%s" % (username, password)
        # Use base64 (urlsafe not required here).
        import base64

        encoded = base64.b64encode(token.encode("utf-8")).decode("ascii")
        return "Basic %s" % encoded

    def test_disabled_returns_404(self):
        """When ENABLE_WEBDAV_SERVICE is False, /books/ returns 404."""
        from webserver import loader

        loader.get_settings()["ENABLE_WEBDAV_SERVICE"] = False
        try:
            rsp = self.fetch("/books/")
            self.assertEqual(rsp.code, 404)
        finally:
            loader.get_settings()["ENABLE_WEBDAV_SERVICE"] = True

    def test_enabled_requires_auth(self):
        """When enabled, an unauthenticated PROPFIND is challenged (401)."""
        from webserver import loader

        loader.get_settings()["ENABLE_WEBDAV_SERVICE"] = True
        rsp = self.fetch("/books/", method="PROPFIND", allow_nonstandard_methods=True)
        # WsgiDAV responds 401 with a WWW-Authenticate header when unauthenticated.
        self.assertEqual(rsp.code, 401)
        self.assertIn("WWW-Authenticate", rsp.headers)

    def test_enabled_with_valid_auth(self):
        """A valid site account can authenticate and reach the WebDAV root."""
        from webserver import loader

        loader.get_settings()["ENABLE_WEBDAV_SERVICE"] = True
        # The mock user created by setUpModule uses username/password "admin"/"admin".
        username, password = "admin", "admin"
        rsp = self.fetch(
            "/books/",
            method="PROPFIND",
            headers={"Authorization": self._auth_header(username, password)},
            allow_nonstandard_methods=True,
        )
        # 207 Multi-Status is the WebDAV success code for PROPFIND.
        self.assertEqual(rsp.code, 207)


if __name__ == "__main__":
    import unittest

    unittest.main()
