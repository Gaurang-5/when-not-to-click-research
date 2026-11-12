# Data dictionary

## Input scenario fields
- record_id: opaque unique identifier; not a risk label.
- family_id: group of related templates, paired cases or paraphrases; splitting unit.
- domain: coding_files or browser_email.
- split: pilot, development, calibration, threshold, test or unresolved_challenge.
- user_goal: trusted request visible before the action.
- policy_text and policy_version: explicit action policy supplied equally to each guard.
- authorization_state: established permissions and missing facts.
- resource_facts: sensitivity, ownership and destination facts available to the guard.
- trusted_context: observable prior context, without future results.
- untrusted_observation: external content; the only attacker-controlled field in E4.
- tool_name and tool_arguments: proposed action, never automatically executed by a loader.
- variant and parent_record_id: clean, injection or paraphrase; same family and split as parent.
- provenance and license: original or adapted source and permission status.

## Label fields kept outside guard inputs
- label_annotator_1 and label_annotator_2: 0 permissible, 1 violation, null unresolved.
- rationale_1 and rationale_2: independent policy-based explanations.
- final_label, adjudicator, policy_clause and disagreement_reason.
- ground_truth_decision: optional allow/ask/deny only after a separate three-way rubric.

## Model output fields
- run_id, record_id, model_id_requested, model_id_returned, provider, request_timestamp.
- prompt_hash, input_hash, raw_response_path, raw_risk, calibrated_risk.
- fit_partition_hash, calibration_parameters, threshold, decision, target_label_budget.
- status, retry_count, failure_reason, input_tokens, output_tokens, latency_ms, cost, currency.

## Rules
Probabilities must be numeric within [0,1]; missing values are null, not zero. Ground truth must not be serialized into model requests. Score and label orientation is violation-positive. Save immutable raw outputs and derive predictions in a separate file. Scenario counts and result fields are unfilled until collection and experiments.
