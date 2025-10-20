from dataclasses import dataclass
from typing import Any, Iterator

# 단일 연결 노드: slots로 메모리/속도 최적화
@dataclass(slots=True)
class _Node:
    value: Any
    next: "_Node | None" = None  # 전방참조는 문자열

class LinkedList:
    """단순 연결리스트 (singly linked list).

    규약:
    - insert: 0 ≤ index ≤ len(self) 아니면 IndexError('index out of range')
    - delete: 0 ≤ index <  len(self) 아니면 IndexError('index out of range')
    - to_list: 맨 앞(head)부터 순서대로 값 리스트 반환
    """

    def __init__(self) -> None:
        self._head: "_Node | None" = None
        self._size: int = 0

    # --- 공개 메서드 ---

    def insert(self, index: int, value: Any) -> None:
        if index < 0 or index > self._size:
            raise IndexError("index out of range")

        new = _Node(value)

        if index == 0:
            new.next = self._head
            self._head = new
        else:
            prev = self._node_at(index - 1)
            assert prev is not None  # _node_at 보장
            new.next = prev.next
            prev.next = new

        self._size += 1

    def delete(self, index: int) -> Any:
        if index < 0 or index >= self._size:
            raise IndexError("index out of range")

        if index == 0:
            assert self._head is not None
            removed = self._head
            self._head = removed.next
        else:
            prev = self._node_at(index - 1)
            assert prev is not None and prev.next is not None
            removed = prev.next
            prev.next = removed.next

        self._size -= 1
        return removed.value

    def to_list(self) -> list[Any]:
        out: list[Any] = []
        cur = self._head
        while cur is not None:
            out.append(cur.value)
            cur = cur.next
        return out

    def __len__(self) -> int:
        return self._size

    def __iter__(self) -> Iterator[Any]:
        cur = self._head
        while cur is not None:
            yield cur.value
            cur = cur.next

    # --- 내부 유틸 ---

    def _node_at(self, index: int) -> "_Node | None":
        cur = self._head
        i = 0
        while cur is not None and i < index:
            cur = cur.next
            i += 1
        return cur


class CircularList:
    """원형 연결리스트 (cursor 기반).

    규약:
    - insert(value): 비었으면 단일 노드 원형(cur.next = cur), 아니면 cursor 뒤에 삽입 후 cursor = 새 노드
    - delete(value) -> bool: 한 바퀴 내 첫 매칭만 삭제. 단일 노드 삭제 시 빈 리스트가 됨.
    - get_next() -> Any | None: 비었으면 None, 아니면 cursor를 다음 노드로 이동시키고 그 값을 반환
    - search(value) -> bool: 한 바퀴 내 존재여부
    - snapshot(steps) -> list[Any]: get_next를 steps번 호출한 결과
    """

    def __init__(self) -> None:
        self._cursor: "_Node | None" = None  # 전방참조는 문자열

    # --- 공개 메서드 ---

    def insert(self, value: Any) -> None:
        new = _Node(value)
        cur = self._cursor

        if cur is None:
            new.next = new
            self._cursor = new
            return

        new.next = cur.next
        cur.next = new
        self._cursor = new  # 새로 넣은 노드를 현재로

    def delete(self, value: Any) -> bool:
        cur = self._cursor
        if cur is None:
            return False

        # 단일 노드
        if cur.next is cur:
            if cur.value == value:
                self._cursor = None
                return True
            return False

        # 다중 노드: 한 바퀴 탐색
        prev = cur
        node = cur.next  # 시작점
        start = node

        while True:
            if node.value == value:
                prev.next = node.next
                if node is self._cursor:
                    self._cursor = prev  # 삭제가 cursor면 이전 노드로 보정
                return True

            prev = node
            node = node.next  # type: ignore[assignment]
            if node is start:
                break

        return False

    def get_next(self) -> Any | None:
        cur = self._cursor
        if cur is None:
            return None
        self._cursor = cur.next  # type: ignore[assignment]
        return self._cursor.value  # type: ignore[return-value]

    def search(self, value: Any) -> bool:
        cur = self._cursor
        if cur is None:
            return False

        node = cur.next
        start = node
        while True:
            if node.value == value:
                return True
            node = node.next  # type: ignore[assignment]
            if node is start:
                break
        return False

    def snapshot(self, steps: int) -> list[Any]:
        out: list[Any] = []
        for _ in range(max(0, steps)):
            out.append(self.get_next())
        return out


# 간단 동작 확인 (필요 없으면 지워도 됨)
if __name__ == "__main__":
    # Singly
    s = LinkedList()
    s.insert(0, "A")
    s.insert(1, "C")
    s.insert(1, "B")
    assert s.to_list() == ["A", "B", "C"]
    assert s.delete(1) == "B"
    assert s.to_list() == ["A", "C"]
    assert len(s) == 2

    # Circular
    c = CircularList()
    assert c.get_next() is None
    c.insert("A"); c.insert("B"); c.insert("C")
    assert c.search("B") is True
    assert c.delete("X") is False
    _ = c.snapshot(5)
    assert c.delete("C") is True
