# OmniAssist CX Orchestrator — LangGraph Customer Support Triage & Resolution

## Project Overview
OmniAssist CX Orchestrator is a production-grade, LangGraph-powered customer support agent for chat, email, and ticket channels. It classifies intents, retrieves grounded knowledge via Qdrant-based RAG (docs, runbooks, FAQs, annotated tickets, macros, product catalog, invoices/payment history), executes safe automations (refunds, password resets, order status), and escalates with a full state bundle. Conditional edges use confidence, sentiment, sensitivity (PII), and account tier to route to clarify, tool, or human. Checkpointing and memory persist context through tool calls and handoffs. Responses are concise, empathetic, and cited for auditability.

---

## Problem Statement

- **The Problem:**  
  - Slow, inconsistent triage across channels.  
  - Fragmented knowledge (docs, FAQs, tickets) wastes time and causes errors.  
  - Repetitive tasks drain agent capacity.  
  - Context loss during escalations harms customer experience.

- **How This Solves It:**  
  - Automates tier‑1 triage and resolution using a graph of nodes: planner, clarify, RAG, tools, synthesis, escalation.  
  - Conditional routing driven by confidence, sentiment, sensitivity, and account tier.  
  - Checkpoints + memory keep state intact across retries and handoffs.  
  - Grounded answers with citations and full audit trails.

- **Why Use It:**  
  - Faster first response and higher self‑resolution.  
  - Safe automations reduce cost-to-serve.  
  - Explainable outputs with citations.  
  - Extensible, policy-driven, and omni‑channel.

---

## Tech Stack / Tools

- **Core Orchestration:** LangGraph (nodes, conditional edges, checkpointing).
- **Vector Store:** Qdrant (collections: docs, runbooks, FAQs, annotated tickets, macros, product_catalog, invoices/payments).
- **LLM Uses:**  
  - **Planner/Triage:** Intent, confidence, sensitivity, required slots.  
  - **Synthesis:** Grounded answers with citations.  
  - **Signals:** Sentiment and PII detection (can be LLM- or model-based).
- **Retrieval:**  
  - **Embeddings:** Embedding model for chunk vectors.  
  - **Re-ranking:** Cross-encoder after MMR for precision.  
  - **Filters:** product, version, locale, tier, severity, updated_at.
- **State & Memory:**  
  - **Checkpointing:** Per-node persist/resume.  
  - **Memory:** Conversation (short-term) and user/account (long-term) in relational DB.
- **Connectors:** Chat widget API, email ingestion, ticketing API.
- **Tool Integrations:** Internal APIs for refunds, password resets, order lookups, invoice fetch.
- **Observability:** Structured logs, traces, metrics; audit logs with citations and tool use.
- **Security:** Secrets vault, PII redaction, RBAC, encryption.

### Recommendations
- **Relational DB:** Postgres for memory, checkpoints, audit, and configuration.  
- **Cache:** Redis for session state and hot chunks.  
- **Tracing:** OpenTelemetry-compatible tracing for node spans.  
- **Queue:** Lightweight queue for email/ticket events and retries.  
- **LLM Profiles:** Small model for planner; larger model for synthesis if needed for quality.

---

## Core Workflow

### Phase 1 — Requirements (What to gather and define)

1. **Stakeholders & Goals**
   - **Stakeholders:** Support leads, L2/L3 agents, product/ops, compliance, SRE/infra, data eng.  
   - **Goals:** Tier‑1 deflection, safe automations, explainable answers, seamless handoffs.

2. **Channels & Payloads**
   - **Chat:** message, user_id, session_id, locale, client_info.  
   - **Email:** from, subject, body, attachments, thread_id.  
   - **Ticketing:** ticket_id, account_id, priority, tags.

3. **Intent Taxonomy & Slots (initial)**
   - **billing_inquiry:** slots: account_id, invoice_id, date_range.  
   - **refund_request:** slots: order_id, item_id, reason, payment_method.  
   - **technical_issue:** slots: product, version, platform, error_code, steps_taken.  
   - **product_recommendation:** slots: category, budget, preferences.  
   - **order_troubleshooting:** slots: order_id, carrier, delivery_status.  
   - **general_question:** slots: topic.
   - **Slot strategy:** Identify critical vs optional. Clarify missing critical slots up to N attempts (default 2–3).

4. **Policy & Safety**
   - **PII:** Detect and mask where required (email, phone, address, payment tokens).  
   - **Refund caps:** Per tier and per period; require manual approval above cap.  
   - **Password reset:** Out-of-band confirmation only.  
   - **Sensitive topics:** Always escalate (legal threats, self-harm, harassment).

5. **Routing Thresholds (initial defaults)**
   - **Intent confidence:** tool ≥ 0.7; RAG ≥ 0.5; clarify 0.3–0.5; human < 0.3.  
   - **Retrieval coverage:** sufficient ≥ 0.6 (weighted relevance).  
   - **Sentiment:** negative ≤ −0.3; strongly negative ≤ −0.6 (consider escalation).  
   - **Clarify attempts:** max 2 (then escalate).

6. **Qdrant Collections & Metadata**
   - **docs/runbooks/faqs/tickets/macros/catalog/invoices:**  
     - **Metadata:** product, version, tier, locale, updated_at, severity, policy_tag, source_url, account_id (when allowed).  
     - **Chunking:** 300–500 tokens with 50–100 overlap.

7. **Audit & Checkpoint Requirements**
   - **Checkpoint after each node:** node_id, state, time.  
   - **Audit event per decision/tool:** decision summary, scores, inputs/outputs refs, actor, time.

---

### Phase 2 — Design (Graph, data, and decisions)

1. **Graph Topology**
   - **Nodes:** ingestion → planner/triage → conditional(clarify | retrieval | tool | human) → synthesis → finalize (or escalate anytime)  
   - **Subgraphs:** tool subgraph per automation; retrieval subgraph supports multi-hop.  
   - **Memory/Checkpoints:** Persist after each node; resume on failure or handoff.

2. **Node Contracts (I/O Schemas)**
   - **Common input:** { conversation_id, user_id, channel, msg, slots, history, attempts, profile, tier, locale }  
   - **Planner output:** { intent, intent_conf, sentiment, sensitivity, required_slots[], missing_slots[], route }  
   - **Retrieval output:** { chunks[], citations[], coverage, retrieval_conf }  
   - **Tool output:** { tool_name, request, response, success, validation_score }  
   - **Synthesis output:** { reply_text, citations[], next_action }

3. **Routing Logic (deterministic + model-informed)**
   - **Clarify when:** missing critical slots and attempts < max AND sensitivity == low.  
   - **Tool when:** intent actionable AND slots present AND intent_conf ≥ 0.7 AND sensitivity == low.  
   - **Retrieval when:** question or explanation needed OR intent_conf in [0.5, 0.7).  
   - **Human when:** intent_conf < 0.3 OR sensitivity high OR repeated clarify failure OR strong negative sentiment OR policy flags.  
   - **Safety override:** Escalate immediately on sensitive topics (policy_tag) or PII+policy conflict.

4. **Scoring & Confidence Fusion**
   - **overall_conf = 0.5*intent_conf + 0.3*retrieval_coverage + 0.2*tool_validation_score** (if applicable).  
   - **retrieval_coverage:** sum(top_k relevance)/k normalized to [0,1].  
   - **tool_validation_score:** schema validation + RBAC + pre-condition checks (0–1).

5. **Multi-hop Retrieval Decision**
   - **If coverage < 0.6:**  
     - Extract missing entities/keywords.  
     - Option A: Ask a clarify question.  
     - Option B: Reformulate query with new terms and re-run retrieval.

---

### Phase 3 — Implementation (Step-by-step, with logic)

1. **Repository & Environments**
   - **Structure:**  
     - **/graph:** node/edge definitions.  
     - **/nodes:** ingestion, planner, clarify, retrieval, synthesis, escalation.  
     - **/tools:** refund, password, order, invoice.  
     - **/retrieval:** qdrant client, MMR, re-ranker.  
     - **/memory:** short/long-term stores.  
     - **/checkpoints:** persistence interface.  
     - **/connectors:** chat/email/ticket adapters.  
     - **/policies:** PII, refunds, safety rules.  
     - **/tests, /ops, /configs**.  
   - **Environments:** dev, staging, prod; separate keys and Qdrant namespaces.  
   - **CI/CD:** lint, type-check, unit/integration, security scan, deploy with gates.

2. **Ingestion Node (normalize + enrich)**
   - **Input:** raw channel payload.  
   - **Steps:**  
     - Parse into unified schema; strip HTML; normalize whitespace.  
     - Detect locale; parse entities (order_id via regex; email; phone).  
     - Load user profile (tier, past issues, preferences).  
     - Redact PII in logs; preserve secure copy in state as allowed by policy.  
     - Checkpoint state.  
   - **Edge:** to planner/triage.

3. **Planner/Triage Node (intent + route)**
   - **Prompt (LLM) returns JSON:** intent, confidence, sentiment ∈ [−1,1], sensitivity ∈ {low,med,high}, required_slots[], missing_slots[].  
   - **Heuristics:**  
     - If contains keywords ["refund","return"] AND sentiment < −0.3 → boost refund_request by +0.1.  
     - If contains ["password","reset"] → sub-intent password_reset; route to tool if account_id present.  
     - If error_code pattern (e.g., ABC-123) → technical_issue; add product/version if present.  
   - **Compute route:** apply thresholds and safety overrides.  
   - **Persist decision:** audit with scores and rationale.  
   - **Edges:** clarify | retrieval | tool | human.

   - **Pseudo-code:**
     ```
     triage = llm_classify(msg, profile)
     triage.intent_conf = apply_heuristics(triage, msg, profile)
     if is_sensitive(triage) or policy_violation(msg): route = 'human'
     elif missing_critical_slots(triage) and attempts < MAX: route = 'clarify'
     elif actionable(triage) and triage.intent_conf >= 0.7: route = 'tool'
     elif triage.intent_conf >= 0.5: route = 'retrieval'
     else: route = 'human'
     ```

4. **Clarify Node (targeted Q&A to fill slots)**
   - **Logic:**  
     - For each missing critical slot, ask a single, specific question with examples.  
     - Keep tone concise and empathetic; one slot per turn to reduce confusion.  
     - Parse reply; update slots; increment attempts.  
     - If attempts >= max or user refusal → escalate human.  
     - If all critical slots filled → re-run planner to confirm route (cheap LLM or rules).
   - **Example prompt template:**  
     - “To help with your {intent}, I need {slot_label}. Please provide {format_hint} (e.g., {example}).”
   - **Edge:** planner (re-check) → tool or retrieval; or human on failure.

5. **Retrieval Subgraph (Qdrant RAG with MMR + re-rank)**
   - **Build query text:** combine latest user message + slots + intent description.  
   - **Filters:** product, version, locale, tier, policy_tag; include account_id only if policy allows.  
   - **MMR:** fetch 50 candidates, lambda=0.5; top 20.  
   - **Re-rank:** cross-encoder on 20; select top_k=6 with scores.  
   - **Coverage:** normalized sum(scores)/k.  
   - **Multi-hop:** if coverage < 0.6, either ask a clarify question or reformulate query with auto-extracted keywords and re-run once.  
   - **Output:** snippets + citation metadata (title, url, collection, chunk_id).  
   - **Edge:** to synthesis if coverage ≥ 0.4 else clarify/human.

   - **Pseudo-code:**
     ```
     query = compose_query(msg, slots, intent)
     cands = qdrant.search(query, filters, top=50, mmr=True, lambda=0.5)
     reranked = cross_encoder.rank(query, cands[:20])
     chunks = reranked[:6]
     coverage = normalize(sum([c.score for c in chunks])/6)
     if coverage < 0.6 and can_clarify(): route='clarify'
     elif coverage < 0.4: route='human'
     else: route='synthesis'
     ```

6. **Tool Subgraphs (safe automations)**
   - **Common guardrails:**  
     - Validate inputs (schema, ownership, existence).  
     - Enforce RBAC by tier and agent policy.  
     - Idempotency key = hash(conversation_id, tool_name, inputs).  
     - Rate limits and retries with jitter on 5xx.  
     - Confirm destructive actions with the user (“Are you sure?”) unless policy says silent.
   - **Refund Tool:**  
     - check_eligibility(order_id, item_id, account_id) → {eligible, reason, cap, window}.  
     - If eligible and amount ≤ cap → process_refund(idempotency_key).  
     - On success: return transaction_id; on partial/deny: include policy citation.  
     - Always log audit with inputs (masked), outputs, and decision.  
   - **Password Reset Tool:**  
     - initiate_reset(account_id) → issues token via secure channel; never returns password.  
     - Confirm user sees the reset email/SMS.  
   - **Order Status Tool:**  
     - get_order_status(order_id) → status, carrier, ETA, tracking_url.  
     - If “delayed”, fetch policy for compensation; propose next steps.  
   - **Invoice Retrieval Tool:**  
     - get_invoices(account_id, range) → list of invoices; attach URLs or masked details.  
     - For billing_inquiry, cite invoice entries in reply.
   - **Edge:** to synthesis; if tool fails twice or validation fails → human.

   - **Pseudo-code (refund path):**
     ```
     valid = validate_inputs(slots, user)
     if not valid: ask_clarify_missing()
     elig = refund.check_eligibility(order_id, item_id, account_id)
     if not elig.eligible: route='synthesis' (explain with policy citation)
     elif elig.amount <= policy.cap and not high_risk(user): 
         res = refund.process(idempotency_key)
         if res.success: route='synthesis'
         else if retryable: retry() else route='human'
     else: route='human' (requires approval)
     ```

7. **Synthesis Node (compose grounded reply with citations)**
   - **Inputs:** intent, slots, chunks/citations, tool results, sentiment, tier.  
   - **Rules:**  
     - Answer directly; keep concise.  
     - Include citations (e.g., “[1] Product FAQ”, “[2] Runbook Step 3”).  
     - If low coverage (0.4–0.6), hedge: “Based on our docs, likely steps are…” and offer escalation.  
     - If a tool performed an action, confirm what happened and what to expect next.  
     - Close with a check: “Did this resolve your issue?”  
   - **Edge:** finalize if user confirms; else loop back to planner or clarify.

8. **Escalation Node (state bundle + ticket)**
   - **When:** low confidence, sensitive, repeated clarify failure, or policy triggers.  
   - **State bundle content:**  
     - **Conversation:** full transcript + timestamps.  
     - **Profile:** user/account tier, preferences.  
     - **Slots:** filled/missing with attempts.  
     - **Retrieval:** citations, chunks refs, coverage scores.  
     - **Tools:** calls made, inputs (masked), outputs, errors.  
     - **Decisions:** triage summaries, thresholds, reasons.  
     - **Attachments:** invoice refs, order refs, relevant artifacts.  
   - **Ticket payload:** priority based on tier/sentiment; route to correct queue; include next best actions.  
   - **Edge:** human queue; checkpoint saved for seamless resume after human resolves.

9. **Memory & Checkpointing**
   - **Short-term memory:** conversation turns, last node, attempts, recent slots. TTL bound to session.  
   - **Long-term memory:** preferences (locale, tone), device history, prior resolutions; scope-limited to account.  
   - **Checkpoint fields:** conversation_id, node_id, state_hash, payload_ref, time.  
   - **Resume policy:** on failure, resume at last checkpoint; if tool partially executed, re-check idempotency key to avoid duplicates.

10. **Observability & Auditing**
    - **Metrics:** intent_F1, retrieval_precision@k, deflection_rate, escalation_rate, tool_success_rate, P95_latency.  
    - **Tracing:** span per node with correlation_id = conversation_id.  
    - **Audit:** store decisions, citations, tool calls, and policy outcomes.  
    - **Privacy:** never store raw secrets; mask PII in logs; keep secure vault references.

---

### Phase 4 — Testing (what to test and how)

1. **Unit Tests**
   - **Planner:** JSON schema validity, confidence thresholds, heuristic overrides.  
   - **Clarify:** slot extraction accuracy, retry limit behavior.  
   - **Retrieval:** MMR + re-rank ordering; filter correctness; citation mapping.  
   - **Tools:** input validation, RBAC enforcement, idempotency, retry logic.  
   - **PII/Policy:** detection accuracy, redaction, blocked routes.

2. **Integration Tests**
   - **E2E flows:**  
     - billing_inquiry → invoice citation → resolve.  
     - refund_request (eligible) → process → confirm.  
     - refund_request (ineligible) → explain with policy citations.  
     - technical_issue → multi-hop retrieval → runbook steps.  
     - password reset → token issued → confirm instructions.  
     - order_troubleshooting → delayed shipment → next steps.  
     - ambiguous → clarify → tool or RAG → resolve.  
     - PII-heavy/legal threat → immediate escalation with state bundle.

3. **Performance & Load**
   - **Targets:** P95 < 4s for RAG; < 7s with a single tool call; throughput per node stable under N concurrent sessions.  
   - **Methods:** replay logs; k6/Locust scripts; backpressure tests.

4. **Safety & Security**
   - **Prompt injection:** ensure retrieval content cannot force tool execution; sanitize context.  
   - **Data leakage:** PII never appears in logs or unauthorized responses.  
   - **Policy adherence:** refund caps/approvals enforced; sensitive topics escalated.

5. **Acceptance Criteria**
   - **Citations:** present for any RAG-sourced answer.  
   - **Deflection:** ≥ target tier‑1 resolution rate.  
   - **Escalation quality:** tickets include complete, reproducible state bundle.  
   - **Resume:** workflow resumes correctly from checkpoints after induced failures.

---

### Phase 5 — Deployment (how to launch and operate)

1. **Pre-deploy**
   - **Seed Qdrant:** ingest docs, FAQs, runbooks, macros, tickets (annotated), catalog, invoices/payments summaries.  
   - **Index params:** choose distance metric (cosine), payload indexes on metadata fields.  
   - **Configs:** thresholds, feature flags, RBAC rules; secrets in vault.  
   - **Warm-up:** prime caches; run smoke tests.

2. **Rollout**
   - **Canary:** low-risk intents first (general_question, order_status); monitor SLIs.  
   - **Expand:** add technical_issue, billing, refunds; watch tool error rates.  
   - **Backups:** routine Qdrant and DB snapshots; verified restores.

3. **Runtime Operations**
   - **Dashboards:** latency, errors, deflection, escalations, tool failures.  
   - **Alerts:** SLA breaches, retrieval coverage dips, consecutive tool failures.  
   - **Runbooks:** retrieval degradation actions, tool outage steps, escalation surge handling.  
   - **Continuous tuning:** review conversations, refine prompts, update docs, re-index changed content.

4. **Governance**
   - **Audits:** periodic PII and policy compliance checks.  
   - **Access reviews:** RBAC changes tracked.  
   - **Data retention:** enforce TTLs for memory and logs.

---

## Deliverables

1. **Source Code**
   - **LangGraph graph:** nodes, edges, conditional routing, checkpoints.  
   - **Node implementations:** ingestion, planner, clarify, retrieval, synthesis, escalation.  
   - **Tool adapters:** refund, password reset, order status, invoice retrieval (with validation and RBAC).  
   - **Connectors:** chat, email, ticketing.  
   - **Memory/Checkpoint layers:** DB schemas and interfaces.  
   - **Policies:** PII detection/redaction, safety, refund rules.

2. **RAG Assets**
   - **Qdrant setup scripts:** collections, payload indexes, index params.  
   - **Ingestion pipelines:** chunking, embeddings, upsert jobs; metadata mapping.  
   - **Re-ranking config:** MMR + cross-encoder parameters.

3. **Configuration & Prompts**
   - **Planner and synthesis prompts:** JSON schemas and examples.  
   - **Thresholds & feature flags:** per environment.  
   - **RBAC mappings:** tool permissions by role/tier.

4. **Testing Artifacts**
   - **Unit/integration/E2E suites:** fixtures, mocks, and golden sets.  
   - **RAG eval dataset:** labeled queries and expected sources.  
   - **Load test scripts:** scenarios and targets.

5. **Documentation**
   - **SRS (this doc).**  
   - **Architecture guide:** diagrams and data flows.  
   - **API specs:** request/response schemas, error codes, idempotency rules.  
   - **Ops runbook:** monitoring, alerts, incident response, backup/restore.  
   - **Security & compliance:** PII handling, retention, access controls.

6. **Deployment Assets**
   - **Manifests:** environment configs and secrets templates.  
   - **CI/CD pipelines:** build, test, deploy, rollback workflows.

7. **Handoff Materials**
   - **State bundle schema:** for human escalations.  
   - **Support agent guide:** how to use citations and decision summaries.  
   - **Demo recording:** E2E walkthrough across chat/email/ticket.

---