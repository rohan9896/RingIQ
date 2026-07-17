# Prose Editorial Review

| Original Text | Revised Text | Changes |
| --- | --- | --- |
| The Core Backend is the sole policy owner and product-state writer. | Core application services are the sole policy and product-state mutation path. | Removes process-level ambiguity for Background Workers. |
| Resolve active tenant membership, then set tenant context. | Resolve identity through a narrow privileged function, then set transaction-local tenant context before product access. | Makes the pre-RLS step explicit. |
| Resolve active KB and pin it to attempt after Voice Worker dispatch. | Resolve and pin the active KB in the call-attempt creation transaction. | Removes timing ambiguity. |

