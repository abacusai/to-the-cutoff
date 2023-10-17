from datetime import datetime
from typing import Any, Dict, List, Union

from github.GithubObject import CompletableGithubObject, _NotSetType
from github.HookResponse import HookResponse

class Hook(CompletableGithubObject):
    def __repr__(self) -> str: ...
    def _initAttributes(self) -> None: ...
    def _useAttributes(self, attributes: Dict[str, Any]) -> None: ...
    @property
    def active(self) -> bool: ...
    @property
    def config(self) -> Dict[str, str]: ...
    @property
    def created_at(self) -> datetime: ...
    def delete(self) -> None: ...
    def edit(
        self,
        name: str,
        config: Dict[str, str],
        events: Union[_NotSetType, List[str]] = ...,
        add_events: Union[_NotSetType, List[str]] = ...,
        remove_events: Union[_NotSetType, List[str]] = ...,
        active: Union[bool, _NotSetType] = ...,
    ) -> None: ...
    @property
    def events(self) -> List[str]: ...
    @property
    def id(self) -> int: ...
    @property
    def last_response(self) -> HookResponse: ...
    @property
    def name(self) -> str: ...
    def ping(self) -> None: ...
    @property
    def ping_url(self) -> str: ...
    def test(self) -> None: ...
    @property
    def test_url(self) -> str: ...
    @property
    def updated_at(self) -> datetime: ...
    @property
    def url(self) -> str: ...