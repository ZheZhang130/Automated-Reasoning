# Frontier to local coding agent orchestration

This is the proposed integration contract for the CSC2108 project. Zhe, Sam, and Peter can develop independently against the boundaries below. Field names and pilot counting rules are provisional team decisions. Confirm them before freezing the main experiment. The first implementation should use in-process Python interfaces. Each workstream may choose its own internal implementation.

## Ownership

| Owner | Builds | Hands off |
| --- | --- | --- |
| Zhe | mini-SWE-agent integration, local and frontier coding model adapters, task workspaces, public test execution, run limits, guidance delivery, and logging | Final submission and run record |
| Sam | Guidance prompts, generation adapter, and experimental condition definitions | One guidance response for a plan, contract, or diagnosis request |
| Peter | LiveCodeBench task selection and normalization, public test fixtures, private evaluation, and metric aggregation | Public task bundle for the runner and private evaluation results keyed by run ID |

## Run inputs

The runner accepts a public task bundle and a run configuration. Validate both before invoking a model.

| Input | Required content |
| --- | --- |
| Public task bundle | Stable task ID, problem statement, submission type and path, starter files when needed, and public test cases or fixtures |
| Submission type | A standalone Python program with stdin/stdout, or a Python function or method with an agreed invocation contract. The first fixture uses stdin/stdout. Peter and Zhe should confirm supported types against the selected dataset release before scaling. |
| Public test interface | A task-specific test adapter returns a normalized status and bounded public feedback. Peter supplies fixture semantics and expected outputs. Zhe invokes the adapter in the task environment. |
| Run configuration | Run ID, condition ID, coding model ID, guidance model ID when applicable, action cap, repair cap, and wall-clock deadline. Capture a configuration version and a task bundle version in the result. |

Use a fresh task workspace per run. Give the agent the task statement, submission instructions, starter files, and public development tests. Peter retains private tests and reference answers in a separate evaluator. The runner exports submissions for scoring after execution. Private evaluation results do not flow back into the agent.

## Conditions and guidance handoff

| Condition | Coding model | Guidance request |
| --- | --- | --- |
| A Local Only | Local | None |
| B Frontier Only | Frontier | None. The frontier model drives the same coding workflow. |
| C Frontier Plan | Local | One plan before the first coding action |
| D Frontier Contract | Local | One contract before the first coding action |
| E Frontier Diagnosis | Local | At most one diagnosis, after the first qualifying public test failure |
| F Combined (optional) | Local | One upfront request for plan and contract guidance. Implement after A–E pass the pilot. |

**Request from Zhe to Sam.** Include the guidance kind, task ID, problem statement, and submission instructions. For diagnosis, also include the candidate code at the time of the failure and the corresponding public test feedback. The guidance adapter returns the requested kind, nonempty guidance text on success, and any available provider usage data. Provider or validation errors must be explicit. Sam owns the prompts and any internal structured format. Plain text at the handoff is sufficient for the first implementation. Diagnosis should describe likely causes and suggest repairs without supplying replacement code.

**Delivery by Zhe.** Put plans and contracts in the initial coding context. For E, record the failing candidate and test output, call the guidance adapter, then add its response to the existing conversation before the next coding action. Preserve workspace contents, conversation history, and remaining limits. Record guidance request and delivery separately. For the pilot, use no automatic guidance retries. If the request fails, log the failure and continue within the remaining limits where possible. Mark the run as having a guidance error so Peter can apply the agreed evaluation policy.

## Public test feedback and budgets

Normalize a public test execution as **pass**, **candidate failure**, or **infrastructure error**. A candidate failure includes a wrong answer or a candidate exception observed by a functioning test runner. A missing test fixture or broken runner is an infrastructure error. For the pilot, a qualifying diagnosis trigger is a candidate failure on a recognized public test after a candidate exists. Confirm timeout classification and any other edge cases with Sam and Peter before the main experiments. A run with no qualifying failure is a valid E run.

Apply the same task environment, tools, and configured coding limits across conditions. Start from the proposal's pilot settings of about 20 tool actions, up to three repairs, and a 10–15 minute timeout. Count each dispatched agent tool action, including unsuccessful actions, toward the action limit. Proposed repair counting rule: a repair begins with the first code edit after a candidate fails a recognized public test. Edits before the next test of a changed candidate belong to the same repair. Repeating a test on unchanged code does not consume another repair. Log each repair start so the pilot can validate the rule.

Measure wall-clock time from the start of task execution through submission or termination, including any guidance calls. Check limits before starting additional work and bound model calls and test executions by the remaining deadline. Save the latest candidate when available, even when a limit is reached.

## Run output and evaluation handoff

Emit one result for every scheduled run, including runs without a submission.

| Record | Contents |
| --- | --- |
| Identity | Run ID, task ID, condition, task version, configuration version, and model IDs |
| Submission | Saved candidate file or explicit absence, plus the submission type |
| Execution | Stop reason, action and repair counts, elapsed time, and ordered trace of edits, public test outcomes, and errors |
| Guidance | Requested kind, whether diagnosis triggered, whether guidance was delivered, and any guidance failure |
| Usage | Coding and guidance usage separately where available, plus frontier API cost when known. Represent unavailable measurements as missing, rather than zero. |

Use distinct stop reasons for submission, action limit, repair limit, deadline, and infrastructure failure. A submitted candidate can fail correctness evaluation. Peter joins private evaluation to the run by run ID and calculates final pass rate and recovery metrics. Include all E tasks in the overall comparison and use the recorded trigger to identify the additional diagnosis subset. Agree on how missing submissions and infrastructure failures count before running the full batch.

## Fixture for independent development

**Task ID** fixture-sum-signed. **Submission** solution.py, a program that reads two signed integers from stdin and prints their sum. Public case 1 takes `2 3` and expects `5`. Public case 2 takes `-4 1` and expects `-3`. Use a known incorrect candidate that takes the absolute value of the sum to exercise the second case. It prints `3` instead of `-3`.

| Guidance kind | Fixed response |
| --- | --- |
| Plan | Read the two integers, add them, and print the result. Check a case with a negative sum. |
| Contract | For any two valid signed integers, print their exact signed sum followed by a newline. |
| Diagnosis | The negative-sum case returned 3 instead of -3. Check whether the implementation discards the sign after adding the inputs. |

**Illustrative E run record.** Run ID fixture-e-001, task fixture-sum-signed, condition E. The first public test invocation reports a wrong answer on case 2. The runner records diagnosis requested and delivered. The agent edits the same candidate, reruns the public tests, and submits solution.py. Record both test outcomes, one repair, the actual action count and elapsed time, and missing provider usage for the fixed response. The private score belongs in a separate evaluation record.

## Implementation order and acceptance checks

1. **Zhe starts with A on the fixture.** Verify that the local agent can write a submission, receive public test output, and terminate with a saved run record. Exercise a budget stop and confirm it preserves the latest candidate. A known failing candidate or scripted agent trajectory can exercise the repair path deterministically if the live model solves the fixture immediately.
2. **Zhe exercises C, D, and E with fixed responses.** Check that C and D deliver guidance before any coding action. Check that E delivers guidance once, keeps the same workspace and conversation, and preserves the remaining budget. Also exercise E with passing tests and with a test runner error. Neither should request diagnosis.
3. **Sam implements the live guidance adapter.** Use the request fields above and return guidance text with usage where available. Validate each guidance kind against a sample request. Confirm with Zhe how invalid responses and provider failures are reported.
4. **Peter supplies a real pilot task and evaluates a saved submission.** Verify that the agent sees only public tests and that the private evaluator can match a score to the run ID. Then supply the 5–10 task pilot manifest separately from the main evaluation set.
5. **The team runs A–E on the pilot.** Check comparable coding limits, complete run records, and cost and runtime accounting. Adjust prompts, model choice, task selection, or limits using pilot results, then freeze configurations before the main batch. Keep F optional.
