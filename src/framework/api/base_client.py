import logging
from typing import Any

from playwright.sync_api import APIRequestContext, APIResponse

logger = logging.getLogger(__name__)

QueryParams = dict[str, str | float | bool]


class BaseClient:
    def __init__(self, request_context: APIRequestContext, base_url: str) -> None:
        self._request_context = request_context
        self._base_url = base_url.rstrip("/")

    def get(self, path: str, *, params: QueryParams | None = None) -> APIResponse:
        url = self._url(path)
        logger.info("GET %s", url)
        response = self._request_context.get(url, params=params)
        logger.info("-> %s %s", response.status, url)
        return response

    def post(self, path: str, *, data: dict[str, Any] | None = None) -> APIResponse:
        url = self._url(path)
        logger.info("POST %s", url)
        response = self._request_context.post(url, data=data)
        logger.info("-> %s %s", response.status, url)
        return response

    def delete(self, path: str, *, data: dict[str, Any] | None = None) -> APIResponse:
        url = self._url(path)
        logger.info("DELETE %s", url)
        response = self._request_context.delete(url, data=data)
        logger.info("-> %s %s", response.status, url)
        return response

    def _url(self, path: str) -> str:
        return f"{self._base_url}{path}"
