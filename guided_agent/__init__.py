"""Integrated A/C/D backend: frozen mini-SWE-agent + upfront frontier guidance + team judge.

Platform-independent core. Host differences stay in ``local_agent.platform_support`` and
``local_agent.portable``; this package composes with them rather than duplicating them.
"""
