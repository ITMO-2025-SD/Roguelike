from collections.abc import Callable
from typing import TypeVar, final

from cellcrawler.character.character_command import CharacterCommand, CommandType

U = TypeVar("U")


@final
class CommandBuilder[T]:
    def __init__(
        self,
        cmd_type: CommandType,
        command: Callable[[U], CharacterCommand],
        single: Callable[[T], U],
        composite: Callable[[list[T]], U],
    ) -> None:
        self.id = cmd_type
        self.command = command
        self.single = single
        self.composite = composite
        self.keys: dict[str, T] = {}

    def add(self, key: str, value: T):
        self.keys[key] = value
        return self.build()

    def remove(self, key: str):
        self.keys.pop(key, None)
        return self.build()

    def build(self) -> CharacterCommand | None:
        if len(self.keys) == 0:
            return None
        if len(self.keys) == 1:
            cmd = next(iter(self.keys.values()))
            return self.command(self.single(cmd))
        return self.command(self.composite(list(self.keys.values())))


def SingletonBuilder[T](cmd_type: CommandType, command: Callable[[T], CharacterCommand]):
    def should_not_call(_data: list[T]):
        raise ValueError("Incorrect usage of SingletonBuilder")

    return CommandBuilder(cmd_type, command, lambda x: x, should_not_call)
