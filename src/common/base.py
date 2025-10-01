from typing import Dict, Any


class BaseResponse:

    def to_dict(self) -> Dict[str, Any]:
        raise NotImplementedError("impl to_dict method")
