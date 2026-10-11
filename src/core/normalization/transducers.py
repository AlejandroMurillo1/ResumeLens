import string
from abc import ABC, abstractmethod
from functools import reduce

from pyformlang.fst import FST

class Transducer(ABC):
    @abstractmethod
    def apply(self, text: str) -> str:
        raise NotImplementedError


class StrippingTransducer(Transducer):
    """Collapses separators so spelling variants reach the same surface form.

    Every run of separators (space, ``.``, ``-``, ``_``, ``/``) becomes one
    space, and runs at the start or end of the text are dropped. Letters and
    digits pass through unchanged (case is left to ``CaseFoldingTransducer``),
    so ``React.js`` -> ``React js`` and ``scikit-learn`` -> ``scikit learn``.
    Any other character is outside the alphabet and raises ``ValueError``.

    Formal definition (deterministic FST, outputs on transitions)::

        Q = {start, word, pending}     q0 = start     F = Q
        Sigma = [A-Za-z0-9] U SEP      Gamma = Sigma' U {" "}   (SEP = " .-_/")
        start   --sep/eps--> start      start   --c/c-->     word
        word    --sep/eps--> pending    word    --c/c-->     word
        pending --sep/eps--> pending    pending --c/" "c-->  word

    The space is emitted lazily (``pending`` -> ``word``), which is what drops
    trailing separators without a second pass.
    """

    SEPARATORS = " .-_/"
    _WORD_CHARS = string.ascii_letters + string.digits

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
        for sep in StrippingTransducer.SEPARATORS:
            fst.add_transition("start", sep, "start", [])
            fst.add_transition("word", sep, "pending", [])
            fst.add_transition("pending", sep, "pending", [])
        for char in StrippingTransducer._WORD_CHARS:
            fst.add_transition("start", char, "word", [char])
            fst.add_transition("word", char, "word", [char])
            fst.add_transition("pending", char, "word", [" ", char])
        fst.add_start_state("start")
        for state in ("start", "word", "pending"):
            fst.add_final_state(state)
        return fst


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


def _check_unambiguous(entries: dict[str, list[str]]) -> None:
    """Reject a spelling that would map to two different canonical tokens."""
    owner: dict[str, str] = {}
    for canonical, spellings in entries.items():
        for spelling in spellings:
            if owner.setdefault(spelling, canonical) != canonical:
                raise ValueError(
                    f"Spelling {spelling!r} is listed for both "
                    f"{owner[spelling]!r} and {canonical!r}"
                )


def build_vocabulary_fst(entries: dict[str, list[str]]) -> FST:
    _check_unambiguous(entries)
    token_fsts = [
        build_token_fst(canonical, spellings)
        for canonical, spellings in entries.items()
    ]
    return reduce(lambda acc, fst: acc | fst, token_fsts)
