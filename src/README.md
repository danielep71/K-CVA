# Production source

> Prototype port (#180): sources, template and tooling are now present. Earlier
> setup-only absence statements below describe the v0.1.0 baseline. This port
> provides no numerical or Excel acceptance. See the [porting record](../docs/prototype/PORTING.md).

No production calculation source exists yet. Follow
[architecture](../docs/REPOSITORY_STRUCTURE.md) and
[decisions](../docs/DECISIONS.md) before adding components.

Core calculations belong in core; supported facade declarations in modules;
host-independent models in classes; Excel adapters in workbook and forms.
These directories are reserved until their first real component. Do not place
tests, generated workbooks or reference derivations in the production import set.
The workbook is built from reviewed exported source; Python is not its runtime.
