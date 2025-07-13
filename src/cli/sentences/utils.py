from src.cli.utils.console import Answers, Color, Style
from src.schemas.sentences import DirectObject, IndirectObject, Negation


def problem_formatter(sentences) -> str:
    output: str = ""

    for sentence in sentences:
        output = output + " ".join(
            [
                Answers.CORRECT if sentence.is_correct is True else Answers.INCORRECT,
                f"{Color.LIGHT_GRAY}{'COD' if sentence.direct_object != DirectObject.NONE.value else '---'}{Style.RESET}",
                f"{Color.LIGHT_GRAY}{'COI' if sentence.indirect_object != IndirectObject.NONE.value else '---'}{Style.RESET}",
                f"{Color.LIGHT_GRAY}{'NEG' if sentence.negation != Negation.NONE.value else '---'}{Style.RESET}",
                sentence.content,
                f"{Color.BRIGHT_BLUE}({sentence.translation}){Style.RESET}"
                if sentence.is_correct
                else f"{Color.LIGHT_RED}({sentence.explanation}){Style.RESET}",
                "\n",
            ]
        )

    return output
