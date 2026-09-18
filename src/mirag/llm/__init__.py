"""Everything that talks to a language model, behind one gateway.

* :class:`ChatModel` - the port. :class:`OpenRouterChatModel` is the real adapter and
  :class:`ScriptedChatModel` the deterministic double used by demos and tests.
* :class:`LLMGateway` - the only object the rest of the application calls. It applies the
  offline lock first and the spending budget second, for every model alike.
"""

from mirag.llm.budget import Budget, BudgetSnapshot
from mirag.llm.gateway import LLMGateway, LLMGatewayFactory
from mirag.llm.messages import assistant_text, raw_tool_call, tool_call
from mirag.llm.models import ChatModel, LLMResponse, OpenRouterChatModel, Usage
from mirag.llm.scripted import ScriptedChatModel

__all__ = [
    "Budget",
    "BudgetSnapshot",
    "ChatModel",
    "LLMGateway",
    "LLMGatewayFactory",
    "LLMResponse",
    "OpenRouterChatModel",
    "ScriptedChatModel",
    "Usage",
    "assistant_text",
    "raw_tool_call",
    "tool_call",
]
