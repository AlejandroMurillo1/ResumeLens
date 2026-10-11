# Ingestion module — Test cases

Scope: `FileLoader` and its concrete subclasses (`TxtLoader`, `MdLoader`,
`DocxLoader`, `PdfLoader`), plus `LoaderFactory`. All loaders implement
`load(path: Path) -> str`, raising `IngestionError` (or a subclass) on
failure.

## `TxtLoader`

| ID | Scenario | Fixture | Expected result |
|---|---|---|---|
| ING-TXT-01 | Valid file with content | `tmp_path` file, UTF-8, containing `"John Doe\nSkills: Python, SQL"` | Returns the exact content, unchanged |
| ING-TXT-02 | Valid file, empty | `tmp_path` file, UTF-8, empty content (`""`) | Returns `""` |
| ING-TXT-03 | File encoded in a non-UTF-8 charset | `tmp_path` file written as Latin-1 bytes (`"José Pérez".encode("latin-1")`) | Raises `IngestionError` |
| ING-TXT-04 | Multiple consecutive newlines | `tmp_path` file with `"Experience\n\nSkills\n- Python\n- SQL"` | Returns the content with newlines preserved exactly |

## `MdLoader`

| ID | Scenario | Fixture | Expected result |
|---|---|---|---|
| ING-MD-01 | Headings present | `tmp_path` file with `"## Skills\n- Python\n- SQL"` | Returns content with `"## Skills"` preserved verbatim (not stripped or rendered) |
| ING-MD-02 | Valid file, empty | `tmp_path` file, empty content | Returns `""` |
| ING-MD-03 | File encoded in a non-UTF-8 charset | Same fixture as ING-TXT-03, `.md` extension | Raises `IngestionError` (inherited from `TxtLoader`) |
| ING-MD-04 | Bulleted list | `tmp_path` file with `"- Python\n- SQL\n- Docker"` | Returns content with bullet markers (`-`) preserved |
| ING-MD-05 | Regression: behaves like `TxtLoader` on the same input | `tmp_path` file with `"# Title\nBody"` | `MdLoader().load(path) == TxtLoader().load(path)` |

## `DocxLoader`

| ID | Scenario | Fixture | Expected result |
|---|---|---|---|
| ING-DOCX-01 | Valid file with paragraphs | `.docx` built in-test with `python-docx`: `add_paragraph("John Doe")`, `add_paragraph("Skills: Python, SQL")` | Returns paragraphs joined in original order, one per line |
| ING-DOCX-02 | Valid file, no paragraphs | `.docx` built with `python-docx`, no paragraphs added | Returns `""` |
| ING-DOCX-03 | Content inside a table | `.docx` built with `python-docx`: one normal paragraph + one `add_table(...)` with text in cells | Returns the paragraph text; **table text is absent** from the result (documented limitation, not an error) |
| ING-DOCX-04 | Corrupted file with `.docx` extension | `tmp_path` file named `corrupted.docx` containing arbitrary bytes (`b"this is not a real docx file"`) | Raises `IngestionError` |
| ING-DOCX-05 | Multiple paragraphs with blank lines between them | `.docx` built with `python-docx`: paragraph, empty paragraph, paragraph | Returns text with blank-line separators preserved between paragraphs |

## `PdfLoader`

| ID | Scenario | Fixture | Expected result |
|---|---|---|---|
| ING-PDF-01 | Single-column page with text | Static fixture `tests/fixtures/ingestion/single_column.pdf` | Returns the page's text content |
| ING-PDF-02 | Page with no extractable text | Static fixture `tests/fixtures/ingestion/blank_page.pdf` (empty page, no text layer) | Returns `""`, does **not** raise |
| ING-PDF-03 | Scanned document (image only, no text layer) | Static fixture `tests/fixtures/ingestion/scanned.pdf` | Returns `""` or near-empty string, does **not** raise |
| ING-PDF-04 | Corrupted or truncated file with `.pdf` extension | `tmp_path` file named `corrupted.pdf` containing arbitrary/truncated bytes | Raises `IngestionError` |
| ING-PDF-05 | Two-column layout *(observational, not a strict-order assertion)* | Static fixture `tests/fixtures/ingestion/two_column.pdf` | Weak assertion only: all expected keywords appear *somewhere* in the returned text. Documents the known risk that column order is not guaranteed; not a correctness guarantee |

## Shared across all four loaders

| ID | Scenario | Fixture | Expected result |
|---|---|---|---|
| ING-SHARED-01 | Path does not exist | `tmp_path / "does_not_exist.ext"`, parametrized over `TxtLoader`, `MdLoader`, `DocxLoader`, `PdfLoader` | Raises `FileNotFoundError` for all four |

## `LoaderFactory`

| ID | Scenario | Fixture | Expected result |
|---|---|---|---|
| ING-FACTORY-01 | Known extension (`.txt`) | `tmp_path / "a.txt"` (path only, file need not exist) | Returns an instance of `TxtLoader` |
| ING-FACTORY-02 | Unknown/unsupported extension | `tmp_path / "a.rtf"` | Raises `UnsupportedFileFormatError` |
| ING-FACTORY-03 | Extension in uppercase | `tmp_path / "a.PDF"` compared against `tmp_path / "a.pdf"` | Both resolve to the same loader type (`type(loader_upper) is type(loader_lower)`) |

## Notes

- `ING-PDF-01` to `ING-PDF-03` and `ING-PDF-05` rely on static fixture files
  under `tests/fixtures/ingestion/`, since generating realistic multi-column
  or scanned PDFs programmatically is more effort than creating a handful of
  small PDFs once (e.g., with `reportlab` or by hand) and committing them.
- `ING-DOCX-01`, `ING-DOCX-02`, `ING-DOCX-03` and `ING-DOCX-05` are built
  directly inside the test with `python-docx`, since that library can both
  write and read `.docx` files — no static fixture needed.
- `ING-PDF-05` is explicitly weaker than the others: it documents a known,
  accepted limitation (column order is not guaranteed) rather than asserting
  strict correctness.