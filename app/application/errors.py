from dataclasses import dataclass


@dataclass
class ApplicationError(Exception):
    status_code: in
    code: str
    message: str

    def __post_init__(self) -> None:
        super().__init__(self.message)
