"""
AgentPort schema — Pydantic models for the agent YAML format.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, model_validator


class LLMProvider(str, Enum):
    anthropic = "anthropic"
    openai = "openai"


class LLMConfig(BaseModel):
    provider: LLMProvider = LLMProvider.anthropic
    model: str = "claude-sonnet-4-6"
    temperature: float = 0.1
    max_tokens: int = 4096


class StateField(BaseModel):
    type: Literal["str", "int", "float", "bool", "list", "dict", "Any"] = "str"
    required: bool = False
    default: Optional[Any] = None
    description: Optional[str] = None
    phi: bool = False  # Protected Health Information flag (HIPAA)


class ToolParameter(BaseModel):
    name: str
    type: Literal["str", "int", "float", "bool", "list", "dict"] = "str"
    required: bool = True
    description: Optional[str] = None


class ToolSchema(BaseModel):
    name: str
    description: str
    parameters: list[ToolParameter] = []
    returns: Optional[dict[str, Any]] = None
    mock: Optional[Any] = None  # Stub return value for generated code


class NodeType(str, Enum):
    llm = "llm"
    tool_executor = "tool_executor"
    human_input = "human_input"


class NodeSchema(BaseModel):
    name: str
    type: NodeType
    system_prompt: Optional[str] = None
    prompt: Optional[str] = None  # alias for system_prompt
    tools: Optional[list[str]] = None  # names of tools this node can call

    @model_validator(mode="after")
    def _normalise_prompt(self) -> "NodeSchema":
        if self.system_prompt is None and self.prompt is not None:
            self.system_prompt = self.prompt
        return self


class EdgeCondition(str, Enum):
    has_tool_calls = "has_tool_calls"
    no_tool_calls = "no_tool_calls"
    always = "always"


class EdgeSchema(BaseModel):
    from_node: str = Field(alias="from")
    to: str
    condition: Optional[EdgeCondition] = None

    model_config = {"populate_by_name": True}


class AgentSchema(BaseModel):
    name: str
    version: str = "1.0.0"
    description: str = ""
    compliance: list[str] = []
    llm: LLMConfig = Field(default_factory=LLMConfig)
    state: dict[str, StateField] = {}
    tools: list[ToolSchema] = []
    nodes: list[NodeSchema] = []
    edges: list[EdgeSchema] = []
