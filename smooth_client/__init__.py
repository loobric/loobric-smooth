# MIT License
# Copyright (c) 2025 sliptonic
# SPDX-License-Identifier: MIT
"""Smooth client — importable Python library for the Smooth Core API.

Speaks only the public REST API and depends on nothing from the server, so a
client (FreeCAD, future Fusion, scripts) can `pip install loobric-smooth` and
reuse this rather than writing its own HTTP layer.
"""
from smooth_client.client import Client
from smooth_client.errors import (
    AuthRequired,
    ConnectionFailed,
    HTTPError,
    NotFound,
    SmoothClientError,
)

__all__ = [
    "Client",
    "SmoothClientError",
    "ConnectionFailed",
    "HTTPError",
    "NotFound",
    "AuthRequired",
]
