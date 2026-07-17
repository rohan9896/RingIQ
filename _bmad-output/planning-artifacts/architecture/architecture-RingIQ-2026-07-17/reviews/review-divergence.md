# Independent-Unit Divergence Review

Verdict: Pass after three clarifications.

## Findings

1. High: A Background Worker could interpret AD-3 as forbidden from applying state mutations, while the Core API could interpret itself as the only process allowed to write. Clarify that shared Core application services own mutations; Background Workers invoke them, and Voice Workers emit events.
2. High: One implementation could pin the KB when the attempt is queued while another pins it only after connection. Define attempt creation as the pinning transaction.
3. Medium: Queue workers need an explicit control-plane access model for cross-tenant claims before entering tenant-scoped product transactions.
4. Low: The remaining module ownership and storage rules are sufficiently convergent.

