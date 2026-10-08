import string
from abc import ABC, abstractmethod
from functools import reduce

from pyformlang.fst import FST


class Transducer(ABC):
    @abstractmethod
    def apply(self, text: str) -> str:
        raise NotImplementedError


class CaseFoldingTransducer(Transducer):
    _PASSTHROUGH = string.digits + " "
    def __init__(self) -> None:
        self._fst: FST = self._build()

    def apply(self, text: str) -> str:
        results = list(self._fst.translate(list(text)))
        if not results:
            raise ValueError(f"Unexpected character in: {text!r}")
        return "".join(results[0])

    @staticmethod
    def _build() -> FST:
        fst = FST()
        for letter in string.ascii_lowercase:
            fst.add_transition(0, letter, 0, [letter.upper()])
        for letter in string.ascii_uppercase:
            fst.add_transition(0, letter, 0, [letter])
        for symbol in CaseFoldingTransducer._PASSTHROUGH:
            fst.add_transition(0, symbol, 0, [symbol])
        fst.add_start_state(0)
        fst.add_final_state(0)
        return fst


def build_token_fst(canonical: str, spellings: list[str]) -> FST:
    fst = FST()
    for spelling in spellings:
        fst.add_transition("0", spelling, "1", [canonical])
    fst.add_start_state("0")
    fst.add_final_state("1")
    return fst


def build_vocabulary_fst(entries: dict[str, list[str]]) -> FST:
    token_fsts = [
        build_token_fst(canonical, spellings)
        for canonical, spellings in entries.items()
    ]
    return reduce(lambda acc, fst: acc | fst, token_fsts)

