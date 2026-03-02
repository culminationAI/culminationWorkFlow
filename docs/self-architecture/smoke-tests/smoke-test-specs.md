# Smoke Test: Spec Lifecycle

## Overview

Validates that atomic capability units (specs) can be created, activated standalone, composed into builds, and cherry-picked.

## Tests

### T1: Create Standalone Spec

**Setup:** Create a test spec (AGENT type)
**Steps:**
1. Define spec manifest: `{id: "spec-agent-test-dummy", type: "AGENT", description: "Test agent for validation", definition: {path: ".claude/agents/test-dummy.md", name: "test-dummy", domain_keywords: ["testing"]}, state: "AVAILABLE", used_by_builds: [], standalone_activatable: true}`
2. Coordinator: Edit `spec-registry.json` → append spec to `specs` array
3. Verify: Read `spec-registry.json` → spec exists with state=AVAILABLE

**Pass:** Spec registered, state=AVAILABLE, `used_by_builds` empty

### T2: Activate Spec Standalone

**Steps:**
1. Coordinator: Read spec definition from registry
2. Coordinator: Write `.claude/agents/test-dummy.md` (minimal agent file)
3. Coordinator: Edit `spec-registry.json` → state=IN_USE, `used_by_builds: ["standalone"]`
4. Verify: Glob `.claude/agents/test-dummy.md` → exists

**Pass:** Agent file created, spec state=IN_USE

### T3: Compose Build from 2 Specs

**Setup:** Create second spec (PROTOCOL type)
**Steps:**
1. Register second spec: `{id: "spec-protocol-test-dummy", type: "PROTOCOL", ...}`
2. Create build manifest in `build-registry.json` with `spec_refs: ["spec-agent-test-dummy", "spec-protocol-test-dummy"]`
3. Activate build: coordinator resolves spec refs → Write files → Edit registries
4. Verify: both specs have state=IN_USE, build is active

**Pass:** Build active, both specs IN_USE, `used_by_builds` includes build ID

### T4: Deactivate Build, Specs Return to AVAILABLE

**Steps:**
1. Deactivate build: delete created files, update build manifest state=buffered
2. Update specs: remove build_id from `used_by_builds`
3. If `used_by_builds` empty → state=AVAILABLE
4. Verify: specs state=AVAILABLE, build state=buffered

**Pass:** Specs AVAILABLE, build buffered, files cleaned up

### T5: Cherry-pick Spec Reuse

**Steps:**
1. Create new build referencing only `spec-agent-test-dummy`
2. Verify: spec's `used_by_builds` updated with new build ID
3. Source build (buffered) unaffected

**Pass:** Spec shared between builds, no duplication

### Cleanup

1. Delete test agent file: `.claude/agents/test-dummy.md`
2. Delete test protocol file
3. Remove test specs from `spec-registry.json`
4. Remove test builds from `build-registry.json`
