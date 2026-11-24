"""Agent adapters; concrete vendor integrations remain explicitly unverified."""

from adapters.agent.claude_code_adapter import ClaudeCodeAdapter
from adapters.agent.codex_adapter import CodexAdapter
from adapters.agent.deepseek_harness_adapter import DeepSeekHarnessAdapter
from adapters.agent.generic_cli import GenericCLIAgent
from adapters.agent.mock_agent import MockAgent
from adapters.agent.opencode_adapter import OpenCodeAdapter
from adapters.agent.zcode_adapter import ZcodeAdapter

__all__ = [
    "ADAPTER_CLASS_PATHS",
    "ClaudeCodeAdapter",
    "CodexAdapter",
    "DeepSeekHarnessAdapter",
    "GenericCLIAgent",
    "MockAgent",
    "OpenCodeAdapter",
    "ZcodeAdapter",
]

# Single source of truth for agent type -> importable class. The engine and the
# adapter verification tool both resolve adapters through this mapping.
ADAPTER_CLASS_PATHS: dict[str, tuple[str, str]] = {
    "mock": ("adapters.agent.mock_agent", "MockAgent"),
    "mock_agent": ("adapters.agent.mock_agent", "MockAgent"),
    "generic_cli": ("adapters.agent.generic_cli", "GenericCLIAgent"),
    "codex": ("adapters.agent.codex_adapter", "CodexAdapter"),
    "claude_code": ("adapters.agent.claude_code_adapter", "ClaudeCodeAdapter"),
    "opencode": ("adapters.agent.opencode_adapter", "OpenCodeAdapter"),
    "deepseek_harness": ("adapters.agent.deepseek_harness_adapter", "DeepSeekHarnessAdapter"),
    "zcode": ("adapters.agent.zcode_adapter", "ZcodeAdapter"),
}

# FILE END: adapters/agent/__init__.py
