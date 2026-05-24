from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ConnectionInfo:
    host: str
    port: int
    username: str
    password: str
    database: str


class DatabaseEngine(ABC):
    @abstractmethod
    def dump_cmd(self, info: ConnectionInfo, output_path: str, compression: bool) -> list[str]:
        ...

    @abstractmethod
    def restore_cmd(self, info: ConnectionInfo, input_path: str) -> list[str]:
        ...

    @abstractmethod
    def get_tables_cmd(self, info: ConnectionInfo) -> list[str]:
        ...

    @abstractmethod
    def transfer_schema_cmd(self, info: ConnectionInfo, dump_path: str) -> list[str]:
        ...
