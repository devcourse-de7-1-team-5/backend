from abc import ABC, abstractmethod


class NextUrlSetter(ABC):
    @abstractmethod
    def get_next_url(self, current_url: str, current_params: dict,
        data: dict) -> tuple[str | None, dict]:
        ...
