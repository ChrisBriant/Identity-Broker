from .google_provider import GoogleProvider
from .discord_provider import DiscordProvider
from .github_provider import GitHubProvider
from .spotify_provider import SpotifyProvider
from .linkedin_provider import LinkedInProvider
from .auth0_provider import Auth0Provider

def get_provider(provider_name: str):

    providers = {
        "google": GoogleProvider(),
        'discord' : DiscordProvider(),
        'github' : GitHubProvider(),
        'spotify' : SpotifyProvider(),
        'linkedin' : LinkedInProvider(),
        'auth0' : Auth0Provider(),
    }

    provider = providers.get(provider_name)

    if not provider:
        raise ValueError("Unsupported provider")

    return provider