from enum import Enum

class PromptEnum(Enum):
    @property
    def prompt(self):
        return self.name.replace('_', ' ')
