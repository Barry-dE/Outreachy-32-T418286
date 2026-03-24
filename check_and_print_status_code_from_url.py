import csv
import sys
import threading
import requests
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Tuple

INPUT_FILE = 'Task 2 - Intern.csv'
TIMEOUT_SECONDS = 20
MAX_WORKERS = 10


HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36 ' 
        'Edg/120.0.0.0 OS/10.0.22631'
    )
}


# Stores unique sessions for each thread 
_thread_local = threading.local()



# get_session creates or retrieves a session for the current thread. 
# This allows for TCP connection reuse across multiple URLs from the same host.
def get_session() -> requests.Session:
    if not hasattr(_thread_local, 'session'):
        session = requests.Session()
        session.headers.update(HEADERS)
        _thread_local.session = session
    return _thread_local.session


# is_valid_url filters out malformed urls before they cause network errors.
def is_valid_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return parsed.scheme in ('http', 'https') and bool(parsed.netloc)
    except Exception:
        return False

# get_status performs the network check. It tries a HEAD request first to save bandwidth.
# If the server doesn't allow HEAD, it falls back to a standard GET request.
def get_status(url: str) -> Tuple[str, str]:
    if not is_valid_url(url):
        return 'INVALID URL', url

    session = get_session()

    try:
        response = session.head(url, timeout=TIMEOUT_SECONDS, allow_redirects=True)

        # Some servers return 405 Method Not Allowed for HEAD requests
        if response.status_code == 405:
            response = session.get(url, timeout=TIMEOUT_SECONDS, allow_redirects=True, stream=True)
            response.close()
        return str(response.status_code), url

    except requests.exceptions.ConnectionError:
        return 'CONNECTION ERROR', url
    except requests.exceptions.Timeout:
        return 'TIMEOUT', url
    except requests.exceptions.RequestException as e:
        return type(e).__name__, url


# load_urls reads the CSV and extracts URLs from the 'urls' column.
# utf-8-sig handles potential Byte Order Marks from Windows files.
def load_urls(file_path: str) -> list:
    
    urls = []
    with open(file_path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row.get('urls', '').strip()
            if url:
                urls.append(url)
    return urls


# check_urls manages the thread pool and prints results.
# The list is pre-allocated to ensure the output order matches the input file. 
def check_urls(file_path: str) -> None:
    try:
        urls = load_urls(file_path)
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        sys.exit(1)

    
    results = [None] * len(urls)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_index = {
            executor.submit(get_status, url): i
            for i, url in enumerate(urls)
        }

        for future in as_completed(future_to_index):
            i = future_to_index[future]
            results[i] = future.result()

    for status, url in results:
        print(f'({status}) {url}')


if __name__ == '__main__':
    file_path = sys.argv[1] if len(sys.argv) > 1 else INPUT_FILE
    check_urls(file_path)