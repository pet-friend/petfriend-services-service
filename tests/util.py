from typing import Callable, Any


class CustomMatcher:
    def __init__(self, matcher: Callable[[Any], bool]):
        self.matcher = matcher

    def __eq__(self, other: Any) -> bool:
        return self.matcher(other)
