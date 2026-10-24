# Production source

No production calculation source exists yet. Follow
[architecture](../docs/REPOSITORY_STRUCTURE.md) and
[decisions](../docs/DECISIONS.md) before adding components.

Core calculations belong in core; supported facade declarations in modules;
host-independent models in classes; Excel adapters in workbook and forms.
These directories are reserved until their first real component. Do not place
tests, generated workbooks or reference derivations in the production import set.
The workbook is built from reviewed exported source; Python is not its runtime.
