import argparse
import sys
from http.client import HTTPException
from time import perf_counter
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


REQUEST_COUNT = 10
CHUNK_SIZE = 64 * 1024
TIMEOUT_SECONDS = 30


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def download(opener, request):
    started = perf_counter()
    downloaded = 0

    with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
        while chunk := response.read(CHUNK_SIZE):
            downloaded += len(chunk)

        content_length = response.headers.get("Content-Length")
        if content_length is not None and "Transfer-Encoding" not in response.headers:
            if int(content_length) != downloaded:
                raise ValueError(f"Ожидалось {content_length} байт, получено {downloaded}")

    return downloaded, perf_counter() - started


def main():
    parser = argparse.ArgumentParser(description="Измерить скорость скачивания по HTTP или HTTPS.")
    parser.add_argument("url", help="Прямая ссылка на скачиваемый ресурс")
    args = parser.parse_args()

    try:
        url = urlsplit(args.url)
        if url.scheme not in ("http", "https") or not url.hostname:
            raise ValueError
    except ValueError:
        parser.error("Укажите полный URL с http:// или https:// и именем сервера.")

    opener = build_opener(NoRedirects())
    request = Request(args.url, method="GET")
    total_bytes = 0
    total_seconds = 0.0

    for number in range(1, REQUEST_COUNT + 1):
        try:
            downloaded, elapsed = download(opener, request)
        except (OSError, HTTPException, ValueError) as error:
            print(f"Запрос {number} из {REQUEST_COUNT} завершился ошибкой: {error}", file=sys.stderr)
            return 1
        total_bytes += downloaded
        total_seconds += elapsed

    average_ms = total_seconds / REQUEST_COUNT * 1000
    speed_mbps = total_bytes * 8 / total_seconds / 1_000_000

    print(f"Запросов выполнено: {REQUEST_COUNT}")
    print(f"Среднее время запроса: {average_ms:.2f} мс")
    print(f"Скачано: {total_bytes} байт")
    print(f"Скорость скачивания: {speed_mbps:.2f} Мбит/с")
    return 0


if __name__ == "__main__":
    sys.exit(main())
