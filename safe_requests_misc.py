import os
import json
import time
import random
import hashlib
import http.client
from pathlib import Path
from threading import Lock
from dataclasses import dataclass

# --------------------------------------------------------------------
# Configuration (edit these values if needed)
# --------------------------------------------------------------------

cacheDir = Path("C:/Users/hughm/PycharmProjects/.cache")        # where cached responses are stored
cacheTtl = 60 * 60 * 6            # how long to keep cached data (6h)
requestsPerSecond = 1          # throttle speed (1 req per second)
maxRetries = 2                    # max retry attempts
backoffBase = 2.0                 # exponential backoff base
userAgent = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/121.0 Safari/537.36"
)


# --------------------------------------------------------------------

lock = Lock()
lastRequestTime = 0

@dataclass
class HttpResponse:
    statusCode: int
    headers: dict
    text: str
    url: str
    fromCache: bool

def hashUrl(url: str) -> str:
    cleaned = url.replace("https://", "").replace("http://", "")
    safe = cleaned.replace("/", "_").replace("?", "_").replace("&", "_").replace(":", "_").replace("=", "_")
    h = hashlib.sha256(url.encode("utf-8")).hexdigest()[:8]
    return f"{safe}_{h}"


def getCachePath(url: str) -> Path:
    """Return the path of the cache file for a URL."""
    cacheDir.mkdir(exist_ok=True)
    return cacheDir / f"{hashUrl(url)}.json"


def loadFromCache(url: str, ttl: float):
    """Try to load a cached response if it exists and is fresh."""
    path = getCachePath(url)
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            cached = json.load(f)
            age = time.time() - cached["timestamp"]
            # If cache_ttl is 0, treat it as "cache forever"
            if ttl == 0 or age < ttl or cached["isPermanent"]:
                return cached["statusCode"], cached["headers"], cached["text"], cached['isPermanent']
    except Exception:
        return None
    return None


def saveToCache(url: str, statusCode: int, headers: dict, text: str, isPermanent: bool):
    """Save response data to the cache."""
    path = getCachePath(url)
    tmpPath = path.with_suffix(".tmp")
    try:
        with open(tmpPath, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "timestamp": time.time(),
                    "statusCode": statusCode,
                    "headers": headers,
                    "text": text,
                    "isPermanent": isPermanent,
                },
                f,
            )
        os.replace(tmpPath, path)
    except Exception as e:
        print(f"[safe_requests] Cache save failed for {url}: {e}")


def enforceRateLimit():
    """Ensure we don't exceed REQUESTS_PER_SECOND."""
    global lastRequestTime
    with lock:
        now = time.time()
        elapsed = now - lastRequestTime
        delayNeeded = max(0, (1.0 / requestsPerSecond) - elapsed)
        if delayNeeded > 0:
            # jitter: +/- up to 30%
            time.sleep(delayNeeded + random.uniform(0, delayNeeded * 0.3))
        lastRequestTime = time.time()


def safeRequest(path: str, method: str = "GET", headers: dict = None, body: str = None, ttl: float = cacheTtl, permanent: bool = None, connection: object = None) -> HttpResponse:
    # Step 1: check cache
    path = path.replace(" ", "%20")
    fullUrl = f"{connection.host}{path}"

    cached = loadFromCache(fullUrl, ttl)
    if cached:
        statusCode, cachedHeaders, text, isPermanent = cached
        if permanent and isPermanent == False:
            print(f"[safeRequests] Permanent cache hit: {fullUrl}")
            saveToCache(fullUrl, statusCode, cachedHeaders, text, permanent)
        elif permanent == False and isPermanent == True:
            print(f"[safeRequests] Changed cache hit: {fullUrl}")
            saveToCache(fullUrl, statusCode, cachedHeaders, text, permanent)
        else:
            print(f"[safeRequests] Cache hit: {fullUrl}")
        return HttpResponse(statusCode, cachedHeaders, text, fullUrl, True)

    requestHeaders = {"User-Agent": userAgent}
    if headers:
        requestHeaders.update(headers)

    attempt = 0

    while attempt < maxRetries:
        enforceRateLimit()
        try:
            connection.request(method, path, body=body, headers=requestHeaders)
            resp = connection.getresponse()
            text = resp.read().decode("utf-8")
            respHeaders = dict(resp.getheaders())

            if resp.status == 200:
                saveToCache(fullUrl, resp.status, respHeaders, text, permanent==True)
                print(f"[safe_requests] Fetched OK: {fullUrl}")
                return HttpResponse(resp.status, respHeaders, text, fullUrl, False)
            elif resp.status in (403, 429) or 500 <= resp.status < 600:
                delay = backoffBase ** attempt + random.uniform(0, 1)
                print(f"[safe_requests] Got {resp.status}, retrying in {delay:.1f}s...")
                time.sleep(delay)
                attempt += 1
            else:
                print(f"[safe_requests] Non-retryable {resp.status} for {fullUrl}")
                return HttpResponse(resp.status, respHeaders, text, fullUrl, False)
        except Exception as e:
            delay = backoffBase ** attempt + random.uniform(0, 1)
            print(f"[safe_requests] Exception {e}, retrying in {delay:.1f}s...")
            time.sleep(delay)
            attempt += 1
            connection.close()
            connection.connect()
    raise RuntimeError(f"[safe_requests] Failed after {maxRetries} attempts: {fullUrl}")
