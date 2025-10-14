from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional, Dict
from urllib.parse import urlencode

import httpx

from common.next_url_setter import NextUrlSetter  # 반드시 클래스로 import 해야 함

T = TypeVar('T')


class BaseCrawler(Generic[T], ABC):
    _default_headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/118.0.5993.88 Safari/537.36"
        ),
        "Referer": "https://search.naver.com/search.naver",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
    }

    def __init__(
        self,
        base_url: str, next_url_setter: Optional[NextUrlSetter] = None,
        *,
        params: Dict[str, object],
        headers: Optional[Dict[str, str]] = None,

    ):
        self.base_url = base_url
        self.params = params
        self._headers = headers or self._default_headers
        self.next_url = f"{self.base_url}?{urlencode(self.params)}"
        self.next_url_setter = next_url_setter

    async def all(self) -> List[T]:
        """모든 페이지의 결과를 비동기적으로 수집하여 하나의 리스트로 반환"""
        all_items: List[T] = []
        async for page in self:
            all_items.extend(page)
        return all_items

    def __aiter__(self):
        return self

    async def __anext__(self) -> List[T]:
        if not self.has_next_page():
            raise StopAsyncIteration("No more pages to fetch.")
        return await self._fetch_next()

    async def _fetch_next(self) -> List[T]:
        """다음 페이지 요청 및 파싱 처리"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.next_url,
                params=self.params,
                headers=self._headers
            )

        response.raise_for_status()
        data = response.json()

        if self.next_url_setter:
            self.next_url, self.params = self.next_url_setter.get_next_url(
                current_url=self.next_url,
                current_params=self.params,
                data=data
            )

        return self._parse_data(data)

    @abstractmethod
    def _parse_data(self, data: dict) -> List[T]:
        """
        Template Method:
        데이터를 파싱하여 T 타입의 리스트로 반환.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def has_next_page(self) -> bool:
        """다음 페이지가 있는지 확인"""
        return self.next_url is not None
