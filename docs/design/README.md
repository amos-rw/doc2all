# Design

Where each design lives. If two documents disagree, the [report text](../02-doc2all-report.md) wins.

| Design | Read it | Source to edit | Built by |
| --- | --- | --- | --- |
| Data-flow diagram, trust boundaries, design rules, threats | Report section 4.1 to 4.5 | `threat-model.src.html`, `build_threat_model.py`, report text | `build_threat_model.py` |
| Security rules for developers | [security-rules.md](security-rules.md) | the same file | written by hand |
| Screens | [screens.md](screens.md), report section 4.6 | `screens.src.html` | `build_screens.py`, `build_screen_shots.py`, `build_screens_doc.py` |
| The cat, colours and type | `doc2all-cat.html` (open in a browser) | the same file | written by hand |
| Data model | [data-model.md](data-model.md), report section 4.7 | `build_data_model.py` | `build_data_model.py` |
| Server interfaces | to be designed (report section 4.8) | | |

## Files here

| File | What it is |
| --- | --- |
| `*.src.html` | Sources you edit |
| `doc2all-*.html`, `_dfd_print.html` | Built pages (do not edit by hand, except `doc2all-cat.html`) |
| `shots/` | Pictures of the screens, light mode, computer view |
| `icons/` | Icons used in the diagram (from Pixabay) |
| `build_*.py` | The builders |

Interactive previews (private Claude pages of the author):
[report](https://claude.ai/artifact/R3YzPu7QBBQrbGVaPw6ZpK) ·
[threat model tour](https://claude.ai/artifact/36jnFcuxqsz5RbK412PoaP) ·
[screens](https://claude.ai/artifact/8aEvFXWLE7zcDjJ4owATdj) ·
[cat](https://claude.ai/artifact/Por6pHoLVCK7YRSGcGFXjJ) ·
[data model](https://claude.ai/artifact/V9gsmYkzTdkW5tRiqJyvTM)
