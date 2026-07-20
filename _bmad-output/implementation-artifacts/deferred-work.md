- source_spec: `_bmad-output/implementation-artifacts/spec-post-call-qualification-outcome.md`
  summary: Make voice-worker call-artifact persistence retryable after transient internal API failures.
  evidence: `_persist_call_artifacts` marks artifacts persisted before `_store_call_artifacts` succeeds, so the pre-existing shutdown callback cannot retry a failed upload.
