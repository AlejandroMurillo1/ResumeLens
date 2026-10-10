from pathlib import Path

from textx import metamodel_from_file, get_location, TextXSyntaxError, TextXSemanticError

from src.core.models.models import DSLError, DSLErrorKind


class DSLValidator:
    def __init__(self, grammar_path: str | Path, valid_profile_names: tuple[str, ...]) -> None:
        self._valid_profile_names = set(valid_profile_names)
        self._metamodel = metamodel_from_file(str(grammar_path), autokwd=True)
        # NOTE: "ProfileResult" is a placeholder rule name — update it to
        # match whatever you actually call the rule for a profile entry
        # inside the `profiles { ... }` block once candidate.tx exists.
        self._metamodel.register_obj_processors({
            "ProfileResult": self._check_profile_name,
        })

    def validate(self, text: str):
        try:
            return self._metamodel.model_from_str(text)
        except TextXSyntaxError as exc:
            raise DSLError(
                kind=DSLErrorKind.SYNTAX,
                message=exc.message,
                line=exc.line,
                column=exc.col,
            ) from exc
        except TextXSemanticError as exc:
            raise DSLError(
                kind=DSLErrorKind.SEMANTIC,
                message=exc.message,
                line=getattr(exc, "line", None),
                column=getattr(exc, "col", None),
            ) from exc

    def _check_profile_name(self, profile_result) -> None:
        if profile_result.name not in self._valid_profile_names:
            raise TextXSemanticError(
                f"Unknown profile name: '{profile_result.name}'",
                **get_location(profile_result),
            )