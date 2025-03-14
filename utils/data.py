from urllib.parse import urlparse

def get_base_url(url: str):
    """Given a URL, returns its base"""
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}/"
    return base_url