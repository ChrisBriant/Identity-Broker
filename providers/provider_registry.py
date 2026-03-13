from .google_provider import GoogleProvider
from .discord_provider import DiscordProvider
from .github_provider import GitHubProvider
from .spotify_provider import SpotifyProvider

def get_provider(provider_name: str):

    providers = {
        "google": GoogleProvider(),
        'discord' : DiscordProvider(),
        'github' : GitHubProvider(),
        'spotify' : SpotifyProvider(),
    }

    provider = providers.get(provider_name)

    if not provider:
        raise ValueError("Unsupported provider")

    return provider