from urllib3.util.retry import Retry

import requests
from requests.adapters import HTTPAdapter


def session_retry():
    """Create a session with retry."""
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=(500, 502, 504))
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    return session
