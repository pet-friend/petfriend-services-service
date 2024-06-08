from typing import Any, Callable, Generic, TypeVar

T = TypeVar("T")


class CustomMatcher(Generic[T]):
    def __init__(self, matcher: Callable[[T], bool | None]):
        self.matcher = matcher

    def __eq__(self, other: Any) -> bool:
        if self.matcher(other) is False:
            return False
        return True  # if True or None
