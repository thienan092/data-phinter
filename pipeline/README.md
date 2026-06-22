# NotebookLM Pipeline Status

| File | Status | Role |
|---|---|---|
| `build_exemplar.py` | Supported | Build the representative exemplar and audit-only coverage manifest. |
| `aggregate_runs.py` | Supported | Combine generated runs while enforcing shared strict-candidate rules. |
| `validate_candidates.py` | Supported | Executable strict-completion gate used before pointer updates. |
| `candidate_quality.py` | Supported internal module | Shared URL, topic, listing, duplicate, and target rules. |
| `build_request.py` | Legacy unsupported | Historical steered prompt builder; exits unless explicitly acknowledged. |

The supported workflow is defined by `notebooklm-sst-research`. It may use exemplar representation
and a compact URL-only exclusion index, but must not steer Deep Research with fixed niche, brand,
domain, or region lists.
