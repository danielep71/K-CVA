import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtemp, readFile, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

for (const name of ['extra|label', 'extra`label', 'extra|`label']) {
  test(`raw label ${name} survives drift comparison and evidence`, async () => {
    const dir = await mkdtemp(join(tmpdir(), 'drift-evidence-'));
    try {
      const manifest = JSON.parse(await readFile('.github/labels.json', 'utf8'));
      const policy = JSON.parse(await readFile('.github/label-policy.json', 'utf8'));
      const live = [...manifest.core, ...manifest.overlays.profile[policy.profile],
        ...policy.label_domains.flatMap(domain => manifest.overlays.domain[domain]),
        { name, color: 'ABCDEF', description: 'synthetic extra label' }];
      const source = join(dir, 'live.json');
      const output = join(dir, 'report.json');
      const summary = join(dir, 'report.md');
      await writeFile(source, JSON.stringify(live));
      const result = spawnSync(process.execPath, ['.github/scripts/labels-drift.mjs',
        '--live', source, '--output', output, '--summary', summary],
      { encoding: 'utf8', env: { ...process.env, GITHUB_STEP_SUMMARY: '' } });
      assert.equal(result.status, 1, result.stderr); // Drift, not contract failure.
      const report = JSON.parse(await readFile(output, 'utf8'));
      assert.equal(report.canonical_plan_verified, true);
      assert.equal(report.counts.differences, 1);
      assert.equal(report.differences[0].name, name);
      assert.equal(report.differences[0].action, 'delete');
      assert.match(await readFile(summary, 'utf8'), /Canonical reconciliation plan cross-check: \*\*PASS\*\*/);
    } finally { await rm(dir, { recursive: true, force: true }); }
  });
}
