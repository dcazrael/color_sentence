# Code Conventions (color_sentence)

## Language
- English docstrings and identifiers everywhere.

## Typing
- 100% typing: annotate parameters, return types **and** local variables.
- Avoid multi-target assignments (`a = b = 0`); declare one variable per line with an explicit type.
- Prefer `Final` for constants.

## Readability
- Descriptive names; avoid cryptic abbreviations.
- Keep functions short and single-purpose.
- Module docstrings describe *what* the module does.

## “Magic numbers”
- Do not inline numeric thresholds. Put them into `config.py` (or module-level `Final` constants if truly module-specific).

## Errors
- Narrow exceptions only. Prefer library-specific errors (e.g., `httpx.HTTPError`) to `Exception`.
- Validate inputs early; fail fast with clear messages.

## Color naming
- Prefer The Color API for human-readable names. Fall back to internal HSV heuristic only when the API is unavailable.

## Tests
- Add unit tests for each public function path (happy path + edge cases).

## Style tools
- Keep `ruff` and `mypy` strict. Use `pyright` for enforcing typed locals.
