from abc import ABC, abstractmethod


class Promptable(ABC):
    @abstractmethod
    def prompt(self) -> str:
        pass
