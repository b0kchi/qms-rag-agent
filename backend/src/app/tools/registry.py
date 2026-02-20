# 도구(Tools) 등록 모듈

from dataclasses import dataclass # dataclass 데코레이터가 붙은 클래스는 __init__, __repr__ 등의 기능이 자동으로 생긴다
from typing import Callable, Any, Dict, List # Callable은 함수타입을 표현할 때 쓴다.

@dataclass
class ToolSpec:
    name: str
    description: str
    fn: Callable[..., Any] # 파이썬 함수를 담는 필드, ...은 인자 형태를 제한하지 않음을 뜻함, Any: 반환값 타입도 제한하지 않음

class ToolRegistry:
    def __init__(self): # ToolRegistry 객체가 생성될때 자동 실행되는 생성자
        self._tools: Dict[str, ToolSpec] = {} # 여기서 _tools는 인스턴스 변수로 self 객체안에 동적으로 생성되는 속성이다.

    def register(self, name: str, description: str, fn: Callable[..., Any]) -> None:
        self._tools[name] = ToolSpec(name=name, description=description, fn=fn)

    def list_tools(self) -> List[ToolSpec]:
        return list(self._tools.values())

    def get(self, name: str) -> ToolSpec:
        return self._tools[name]