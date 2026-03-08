from .google_provider import GoogleProvider
from .discord_provider import DiscordProvider

def get_provider(provider_name: str):

    providers = {
        "google": GoogleProvider(),
        'discord' : DiscordProvider(),
    }

    provider = providers.get(provider_name)

    if not provider:
        raise ValueError("Unsupported provider")

    return provider