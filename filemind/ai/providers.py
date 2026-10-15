"""Supported OpenAI-compatible provider defaults."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderPreset:
    """Public default connection values for one chat-completions provider."""

    provider_id: str
    name: str
    base_url: str
    model: str
    note: str


PROVIDERS: tuple[ProviderPreset, ...] = (
    ProviderPreset("deepseek", "DeepSeek", "https://api.deepseek.com", "deepseek-flash",
                   "官方当前通用模型 DeepSeek-V4.1-Flash；模型 ID 为 deepseek-flash，兼容 Chat Completions。"),
    ProviderPreset("openai", "OpenAI", "https://api.openai.com/v1", "gpt-5-mini",
                   "使用 OpenAI Chat Completions；需单独开通 API 计费与权限。"),
    ProviderPreset("siliconflow", "硅基流动 SiliconFlow", "https://api.siliconflow.cn/v1",
                   "deepseek-ai/DeepSeek-V4-Flash", "模型可用性和名称以 SiliconFlow 模型广场为准。"),
    ProviderPreset("dashscope", "阿里云百炼 DashScope", "https://dashscope.aliyuncs.com/compatible-mode/v1",
                   "qwen-plus", "预设北京公共兼容端点；地域、业务空间和模型授权可能影响可用性。"),
    ProviderPreset("custom", "自定义 OpenAI 兼容接口", "", "", "仅支持兼容的 Chat Completions 接口。"),
)

PROVIDER_BY_ID = {provider.provider_id: provider for provider in PROVIDERS}
ENVIRONMENT_KEY_NAMES = {
    "deepseek": "DEEPSEEK_API_KEY",
    "openai": "OPENAI_API_KEY",
    "siliconflow": "SILICONFLOW_API_KEY",
    "dashscope": "DASHSCOPE_API_KEY",
    "custom": "FILEMIND_API_KEY",
}
