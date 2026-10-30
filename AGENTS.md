# Documentation Policy

- Keep every README concise and focused on introducing the project or the component
  it describes. Do not put implementation details, build or deployment procedures,
  configuration walkthroughs, experiment logs, measurements, validation evidence,
  troubleshooting records, or chronological status updates in a README.
- Store detailed project documentation in `notes/`. Maintain `notes/INDEX.md` as
  the entry point and link to the relevant notes from READMEs.
- Keep the root README languages in separate files: `README.md` is English by
  default and `README.zh-CN.md` is Simplified Chinese. Add reciprocal language
  links and equivalent high-level feature-status tables, distinguishing working,
  partial, unimplemented and unverified capabilities. Keep procedures and
  validation details in `notes/`, not in the feature tables.
- Keep notes and component READMEs bilingual. Both language versions must
  communicate the same facts, limitations, and instructions; a translated heading
  or short summary is not a substitute for a bilingual detailed note.
- Keep this `AGENTS.md` policy in English.
- Preserve historical records, existing edits, failures, evidence identifiers,
  authorization boundaries, and uncertainty when reorganizing documentation.
  Distinguish dated snapshots from current state; documentation is not permission
  to repeat device operations or a claim of new hardware validation.
- Do not publish private information in notes, including filenames and links:
  actual IP addresses or subnets, SSIDs, MAC addresses, host interface names,
  personal usernames, device/partition/boot/session identifiers, key material or
  fingerprints, private-artifact digests, or local paths outside the repository.
  Use consistent descriptive placeholders instead. Generic system paths and
  public upstream references may remain; never publish private redaction mappings.
- Privacy redaction takes precedence over preserving exact historical literals.
  Otherwise keep commands, hashes, service names, and code/evidence paths exact.
  Explain placeholders in `notes/INDEX.md`, distinguish sanitized examples from
  replayable instructions, and never weaken SSH host-key verification.
- Identify repository-root-relative paths in notes, and update relative Markdown
  links and machine-readable documentation references, including those in
  `device.json`, whenever documents move or receive privacy-safe filenames.
