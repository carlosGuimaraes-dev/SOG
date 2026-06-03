# SOGA-100 backend/shared reproduction

Date: 2026-06-03

## Scope

Reproduce the backend/shared focused regression command from QA after [SOGA-98](/SOG/issues/SOGA-98), using the current Tech Lead shared checkout.

## Command

```bash
python3 -m pytest api/tests/test_shared_contracts.py agente/tests/test_shared_contracts.py agente/tests/test_auth_manager.py agente/tests/test_emissao_idempotencia.py agente/tests/test_extrator_pdf.py -q
```

## Result

Initial reproduction before [SOGA-103](/SOG/issues/SOGA-103) completed failed before test collection:

```text
ERROR: file or directory not found: api/tests/test_shared_contracts.py

no tests ran in 0.00s
```

After [SOGA-103](/SOG/issues/SOGA-103) published commit `81b49ae` on `origin/main`, the SOGA-100-visible checkout could not fast-forward because it contained local frontend runtime commits `2760a21` and `6b2acfe`. A no-conflict merge was created locally as `25c4c43` to combine the backend/shared runtime artifacts with those existing local commits.

Final result in this checkout:

```text
31 passed in 0.74s
```

## Initial failure

The command fails before test collection:

```text
ERROR: file or directory not found: api/tests/test_shared_contracts.py

no tests ran in 0.00s
```

## File presence check

The following files are absent from the current checkout:

- `api/tests/test_shared_contracts.py`
- `agente/tests/test_shared_contracts.py`
- `agente/tests/test_auth_manager.py`
- `shared/sog_shared/runtime_preparation.py`

`git ls-files` only reports these two files from the focused command:

- `agente/tests/test_emissao_idempotencia.py`
- `agente/tests/test_extrator_pdf.py`

## Diagnosis

The QA failure was reproducible in this checkout before [SOGA-103](/SOG/issues/SOGA-103). The closure evidence from [SOGA-98](/SOG/issues/SOGA-98) did not match the files visible to this shared workspace.

The divergence is now reconciled for this checkout: the backend/shared artifacts are present, the focused command passes, and [SOGA-75](/SOG/issues/SOGA-75) can resume QA against the promoted trail.
