import enum

class PromptEnum(enum.Enum):
    @property
    def prompt(self):
        return self.name.replace('_', ' ')
