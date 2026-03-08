from .google_provider import GoogleProvider

def get_provider(provider_name: str):

    providers = {
        "google": GoogleProvider(),
    }

    provider = providers.get(provider_name)

    if not provider:
        raise ValueError("Unsupported provider")

    return provider