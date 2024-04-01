from typing import Callable, Any


class CustomMatcher:
    def __init__(self, matcher: Callable[[Any], bool | None]):
        self.matcher = matcher

    def __eq__(self, other: Any) -> bool:
        if self.matcher(other) is False:
            return False
        return True  # if True or None
