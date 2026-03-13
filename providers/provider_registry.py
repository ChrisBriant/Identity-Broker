from .google_provider import GoogleProvider
from .discord_provider import DiscordProvider
from .github_provider import GitHubProvider

def get_provider(provider_name: str):

    providers = {
        "google": GoogleProvider(),
        'discord' : DiscordProvider(),
        'github' : GitHubProvider()
    }

    provider = providers.get(provider_name)

    if not provider:
        raise ValueError("Unsupported provider")

    return provider