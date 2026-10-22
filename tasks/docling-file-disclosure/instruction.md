# Docling copies files from the host into converted output

Docling is a Python SDK and CLI that converts documents (PDF, Office, HTML, images and more) into a unified Docling document, which can be exported to Markdown, HTML or JSON. A Docling document serialized as JSON is itself an accepted input, so documents are routinely passed between systems in this form and converted again, for example to re-export them. That serialized data is content: it often comes from other people, pipelines or machines, and docling must treat it as untrusted.

## Observed impact

A JSON document received from someone else is converted and exported with its images embedded:

```python
from docling.document_converter import DocumentConverter
from docling_core.types.doc import ImageRefMode

result = DocumentConverter().convert("report.json")
result.document.save_as_markdown("report.md", image_mode=ImageRefMode.EMBEDDED)
```

If a picture in `report.json` refers to an image at `/srv/private/scan.png` on the machine running the conversion, `report.md` contains that file's content, base64-encoded. Whoever supplied the JSON can thus read image files from the converting host once the output is shared back.

## Required behaviour

- No image reference inside serialized document data that docling reads, in any form and anywhere in the document, may cause docling to read, embed or copy a file from the local filesystem into any output.
- This holds wherever docling reads such serialized document data from, not only for the example above.
- For such a reference, docling either leaves that image out (the rest of the document loads and exports normally) or refuses the document with an error. In neither case may any content of the local file reach an output.
- An explicit opt-in for input the caller trusts may be offered, but without it the rules above apply.

The example above is one example, not the full set.

## Must keep working exactly as today

- Embedded images (`data:` URIs) load and export exactly as today.
- Remote image links (`http`/`https`) stay in the document unchanged, as links; docling does not fetch them.
- Text, tables and every other part of a document come through unchanged, wherever docling reads serialized document data from.
- The project's existing test suite.

## Constraints

- Fix the problem and its close variants, not only the example above.
- Keep legitimate use working.
- Do not modify or add tests.
- Do not look up the upstream fix.
- Do not special-case the example.
