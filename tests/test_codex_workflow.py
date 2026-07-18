from pathlib import Path

import yaml


ROOT = Path(__file__).parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "codex.yml"
ACTIONLINT_CONFIG = ROOT / ".github" / "actionlint.yaml"
PROMPT = ROOT / ".github" / "codex" / "prompts" / "comment-response.md"
PROGRESS_REPORTER = ROOT / ".github" / "codex" / "scripts" / "codex_progress_reporter.py"


def workflow_text():
    return WORKFLOW.read_text(encoding="utf-8")


def workflow_data():
    return yaml.safe_load(workflow_text())


def codex_job():
    return workflow_data()["jobs"]["codex"]


def workflow_step(*, step_id=None, name=None):
    for step in codex_job()["steps"]:
        if step_id is not None and step.get("id") == step_id:
            return step
        if name is not None and step.get("name") == name:
            return step
    raise AssertionError(f"workflow step not found: id={step_id!r}, name={name!r}")


def prompt_text():
    return PROMPT.read_text(encoding="utf-8")


def progress_reporter_text():
    return PROGRESS_REPORTER.read_text(encoding="utf-8")


def test_employee_job_is_bounded_and_serialized_per_request_target():
    job = codex_job()

    assert job["timeout-minutes"] == 25
    assert job["concurrency"] == {
        "group": "codex-${{ github.repository }}-${{ github.event.issue.number || github.event.pull_request.number }}",
        "cancel-in-progress": False,
    }


def test_only_repository_writers_can_trigger_the_employee():
    job = codex_job()
    job_condition = job["if"]
    context_script = workflow_step(step_id="context")["with"]["script"]

    assert workflow_data()["permissions"] == {"contents": "read"}
    assert "!endsWith(github.actor, '[bot]')" in job_condition
    assert "github.actor != 'github-actions[bot]'" not in job_condition
    assert all(role in job_condition for role in ("OWNER", "MEMBER", "COLLABORATOR"))
    assert all(trigger in job_condition for trigger in ("@codex", "/codex"))
    assert "github.rest.repos.getCollaboratorPermissionLevel" in context_script
    assert '["admin", "maintain", "write"].includes(permission)' in context_script


def test_agent_has_public_network_but_cannot_read_host_credentials():
    restore_script = workflow_step(name="Restore Codex ChatGPT auth")["run"]

    required_fragments = (
        'default_permissions = "codex-employee"',
        'extends = ":workspace"',
        '":root" = "deny"',
        '":minimal" = "read"',
        '":tmpdir" = "deny"',
        '":slash_tmp" = "deny"',
        '[permissions.codex-employee.filesystem.":workspace_roots"]',
        '"." = "write"',
        '".github/workflows" = "read"',
        "[permissions.codex-employee.network.domains]",
        "network_proxy = true",
        "allow_local_binding = true",
        '"*" = "allow"',
        '"localhost" = "allow"',
        '"127.0.0.1" = "allow"',
        '"169.254.169.254" = "deny"',
        '"metadata.google.internal" = "deny"',
        'TMPDIR = "$GITHUB_WORKSPACE/.codex-runtime"',
        "'.codex/tmp/'",
        '"GITHUB_TOKEN"',
        '"CODEX_AUTH_JSON"',
    )
    assert all(fragment in restore_script for fragment in required_fragments)
    assert "allow_local_binding = false" not in restore_script
    assert "--sandbox workspace-write" not in workflow_text()
    assert 'sandbox_mode = "workspace-write"' not in restore_script


def test_sandbox_setup_fails_closed_before_codex_runs():
    setup_script = workflow_step(name="Setup bubblewrap and AppArmor for sandbox")["run"]
    step_names = [step.get("name") for step in codex_job()["steps"]]

    assert "continuing" not in setup_script
    assert "::error::Required AppArmor profile source is missing" in setup_script
    assert "::error::Bubblewrap sandbox self-test failed" in setup_script
    assert "::error::AppArmor profile is not active for bubblewrap" in setup_script
    assert setup_script.count("exit 1") >= 3
    assert step_names.index("Setup bubblewrap and AppArmor for sandbox") < step_names.index("Run Codex")


def test_trusted_assets_follow_the_immutable_workflow_version_and_acknowledge_first():
    context = workflow_step(step_id="context")
    script = context["with"]["script"]

    assert context["env"]["WORKFLOW_SHA"] == "${{ github.workflow_sha }}"
    assert "const workflowSha = process.env.WORKFLOW_SHA;" in script
    assert 'path: ".github/codex/prompts/comment-response.md"' in script
    assert 'path: ".github/codex/scripts/codex_progress_reporter.py"' in script
    assert script.count("ref: workflowSha") == 2
    assert "ref: defaultBranch" not in script
    assert script.index("reactions.createForIssueComment") < script.index("issues.createComment")
    assert script.index("issues.createComment") < script.index('path: ".github/codex/prompts/comment-response.md"')
    assert "github.rest.issues.updateComment" in script
    assert "无法加载受信任的 Codex 运行资源" in script
    assert "const codexPromptTemplate = `${runnerTemp}/codex-comment-response.md`;" in script
    assert 'core.exportVariable("CODEX_PROMPT_TEMPLATE", codexPromptTemplate)' in script
    assert 'core.exportVariable("CODEX_PROGRESS_REPORTER", codexProgressReporter)' in script
    assert 'cat "$CODEX_PROMPT_TEMPLATE"' in workflow_step(name="Build Codex prompt")["run"]
    assert "python3 .github/codex/scripts/codex_progress_reporter.py" not in workflow_text()


def test_request_context_rejects_missing_or_external_pr_head_repositories():
    context_script = workflow_step(step_id="context")["with"]["script"]
    checkout = workflow_step(name="Checkout repository")

    assert 'const headRepoFullName = pr?.head?.repo?.full_name || "";' in context_script
    assert "该 Pull Request 的 head 仓库已不可用。" in context_script
    assert "headRepo: headRepoFullName" in context_script
    assert "sameRepository: headRepoFullName === `${owner}/${repo}`" in context_script
    assert "pr.head.repo.full_name" not in context_script
    assert "github.rest.git.listMatchingRefs" in context_script
    assert "codex/issue-${issueNumber}-" in context_script
    assert "已存在多个 Codex 分支" in context_script
    assert "属于已关闭或已合并的 Pull Request" in context_script
    assert checkout["with"]["ref"] == "${{ steps.context.outputs.target_sha }}"
    assert checkout["with"]["persist-credentials"] is False
    assert "CODEX_PR_DIFF" not in workflow_text()
    assert "CODEX_PR_FILES_JSON" not in workflow_text()


def test_agent_contract_requires_a_validated_publish_decision():
    run_step = workflow_step(step_id="run_codex")
    prompt = prompt_text()

    assert "timeout --signal=TERM --kill-after=30s 20m env -u CODEX_PROGRESS_TOKEN codex exec" in run_step["run"]
    assert "--json" in run_step["run"]
    assert "tee .codex/tmp/codex-events.jsonl" in run_step["run"]
    assert run_step["env"]["CODEX_PROGRESS_TOKEN"] == "${{ steps.interaction_token.outputs.token }}"
    assert all(field in prompt for field in ('"ready_to_publish"', '"feature"', '"commit_message"', '"summary"', '"tests"'))
    assert ".codex-result.json" in prompt
    assert ".github/workflows/" in prompt
    assert "不得自行 commit 或 push" in prompt
    assert "当前 PR head" in prompt
    assert "patch artifact" not in prompt


def test_agent_prompt_and_all_maintainer_facing_output_are_in_chinese():
    prompt = prompt_text()
    response_script = workflow_step(name="Post Codex response")["with"]["script"]

    assert "Talebook Codex 维护者请求" in prompt
    assert "必须使用中文" in prompt
    assert "执行计划、进度说明、结构化摘要和最终答复" in prompt
    assert "必须先使用计划工具创建中文执行计划" in prompt
    assert "及时更新计划状态" in prompt
    assert "本文件不经过 vue-i18n" in prompt
    assert all(text in response_script for text in ("### 验证", "已发布提交", "未发布", "无需提交仓库改动", "恢复补丁"))
    assert all(
        text not in response_script
        for text in (
            "### Validation",
            "Published commit",
            "Not published",
            "No repository changes were required",
            "Recovery patch",
        )
    )


def test_model_and_reasoning_effort_can_be_overridden_without_enabling_fast_mode():
    job_env = codex_job()["env"]
    restore_script = workflow_step(name="Restore Codex ChatGPT auth")["run"]

    assert job_env["CODEX_MODEL"] == "${{ vars.CODEX_MODEL || 'gpt-5.6-sol' }}"
    assert job_env["CODEX_REASONING_EFFORT"] == "${{ vars.CODEX_REASONING_EFFORT || 'high' }}"
    assert 'model = "$CODEX_MODEL"' in restore_script
    assert 'model_reasoning_effort = "$CODEX_REASONING_EFFORT"' in restore_script
    assert 'service_tier = "fast"' not in restore_script
    assert "fast_mode = true" not in restore_script


def test_publish_gate_rejects_incomplete_or_unsafe_changes():
    gate = workflow_step(step_id="publish_gate")
    script = gate["run"]

    assert gate["env"]["RESULT_FILE"] == ".codex-result.json"
    assert ".ready_to_publish == true" in script
    assert 'test("^[a-z0-9]+(-[a-z0-9]+)*$")' in script
    assert "Conventional Commit" in script
    assert "git rev-parse HEAD" in script
    assert "git add -A" in script
    assert "git diff --cached --check" in script
    assert "design -type f -name '*.wip.html'" in script
    assert "^\\.github/workflows/" in script
    assert 'echo "ready=true" >> "$GITHUB_OUTPUT"' in script
    assert 'echo "ready=false" >> "$GITHUB_OUTPUT"' in script


def test_repository_wip_gate_runs_before_no_change_classification():
    script = workflow_step(step_id="publish_gate")["run"]
    wip_gate = "find design -type f -name '*.wip.html'"
    no_change_gate = 'if [ -z "$reason" ] && git diff --cached --quiet; then'

    assert script.index(wip_gate) < script.index(no_change_gate)


def test_controlled_publisher_uses_a_short_lived_app_token_and_fast_forward_push():
    token_step = workflow_step(step_id="app_token")
    publish = workflow_step(step_id="publish")

    assert token_step["uses"] == "actions/create-github-app-token@v3"
    assert token_step["with"] == {
        "client-id": "${{ secrets.CODEX_APP_CLIENT_ID }}",
        "private-key": "${{ secrets.CODEX_APP_PRIVATE_KEY }}",
        "permission-contents": "write",
        "permission-issues": "write",
        "permission-pull-requests": "write",
    }
    assert "steps.publish_gate.outputs.ready == 'true'" in token_step["if"]
    assert "git fetch" in publish["run"]
    assert 'remote_sha="$TARGET_SHA"' in publish["run"]
    assert "Remote branch moved while Codex was running" in publish["run"]
    assert '-H "Authorization: Bearer $APP_TOKEN"' in publish["run"]
    assert 'git commit -m "$COMMIT_MESSAGE"' in publish["run"]
    assert 'git push "$authenticated_remote" "HEAD:refs/heads/$PUBLISH_BRANCH"' in publish["run"]
    assert "--force" not in publish["run"]


def test_all_interactive_github_calls_use_the_low_privilege_app_token():
    interaction_token = workflow_step(step_id="interaction_token")
    steps = codex_job()["steps"]

    assert interaction_token["uses"] == "actions/create-github-app-token@v3"
    assert interaction_token["with"] == {
        "client-id": "${{ secrets.CODEX_APP_CLIENT_ID }}",
        "private-key": "${{ secrets.CODEX_APP_PRIVATE_KEY }}",
        "permission-contents": "read",
        "permission-issues": "write",
        "permission-pull-requests": "write",
    }
    assert "if" not in interaction_token
    assert steps.index(interaction_token) < steps.index(workflow_step(step_id="context"))

    interaction_token_ref = "${{ steps.interaction_token.outputs.token }}"
    assert workflow_step(step_id="context")["with"]["github-token"] == interaction_token_ref
    assert workflow_step(name="Explain unsupported target")["with"]["github-token"] == interaction_token_ref
    assert workflow_step(step_id="run_codex")["env"]["CODEX_PROGRESS_TOKEN"] == interaction_token_ref
    assert workflow_step(name="Post Codex response")["with"]["github-token"] == interaction_token_ref

    github_script_steps = [step for step in steps if step.get("uses", "").startswith("actions/github-script@")]
    assert all(step["with"].get("github-token") for step in github_script_steps)
    assert "${{ github.token }}" not in workflow_text()


def test_first_successful_issue_run_creates_one_draft_pull_request():
    create_pr = workflow_step(step_id="create_issue_pr")
    script = create_pr["with"]["script"]

    assert "steps.context.outputs.is_pr != 'true'" in create_pr["if"]
    assert "steps.context.outputs.existing_issue_pr_number == ''" in create_pr["if"]
    assert create_pr["with"]["github-token"] == "${{ steps.app_token.outputs.token }}"
    assert "github.rest.pulls.create" in script
    assert "draft: true" in script
    assert "head: process.env.PUBLISH_BRANCH" in script
    assert "base: process.env.DEFAULT_BRANCH" in script
    assert "Closes #${process.env.ISSUE_NUMBER}" in script


def test_existing_issue_branch_without_a_pr_can_recover_after_a_partial_publish():
    token_condition = workflow_step(step_id="app_token")["if"]
    final_status = workflow_step(step_id="final_status")["run"]
    response_script = workflow_step(name="Post Codex response")["with"]["script"]

    assert "steps.publish_gate.outputs.no_changes == 'true'" in token_condition
    assert "steps.context.outputs.existing_issue_branch != ''" in token_condition
    assert '[ "$CREATED_PR_OUTCOME" != "success" ]' in final_status
    assert "无法为现有 Issue 分支创建 Draft PR" in response_script


def test_failed_publication_keeps_a_recovery_patch_but_success_does_not():
    diff = workflow_step(step_id="diff")
    upload = workflow_step(name="Upload Codex patch")

    assert diff["env"]["PUBLISH_OUTCOME"] == "${{ steps.publish.outcome }}"
    assert 'if [ "$PUBLISH_OUTCOME" = "success" ]' in diff["run"]
    assert 'git diff --cached --quiet "$TARGET_SHA"' in diff["run"]
    assert 'git diff --cached --binary "$TARGET_SHA" > .codex/tmp/codex.patch' in diff["run"]
    assert upload["if"] == "always() && steps.diff.outputs.has_patch == 'true'"


def test_comment_reports_validated_metadata_and_remote_delivery_result():
    response = workflow_step(name="Post Codex response")
    script = response["with"]["script"]

    assert response["env"]["CODEX_CONTRACT_VALID"] == "${{ steps.publish_gate.outputs.contract_valid }}"
    assert response["env"]["CODEX_RESULT_FILE"] == ".codex-result.json"
    assert "const validatedResult" in script
    assert "validatedResult.summary" in script
    assert "validatedResult.tests.map" in script
    assert "test.command" in script
    assert "test.result" in script
    assert "CODEX_COMMIT_SHA" in response["env"]
    assert "CREATED_PR_URL" in response["env"]
    assert "github.rest.issues.updateComment" in script


def test_one_progress_comment_is_created_then_updated_throughout_the_run():
    context_script = workflow_step(step_id="context")["with"]["script"]
    run_step = workflow_step(step_id="run_codex")
    reporter = progress_reporter_text()

    assert 'core.setOutput("progress_comment_id"' in context_script
    assert "Codex 正在处理" in context_script
    assert run_step["env"]["CODEX_PROGRESS_COMMENT_ID"] == "${{ steps.context.outputs.progress_comment_id }}"
    assert "env -u CODEX_PROGRESS_TOKEN codex exec" in run_step["run"]
    assert "todo_list" in reporter
    assert "UPDATE_INTERVAL_SECONDS = 60" in reporter
    assert "reasoning" not in reporter


def test_actionlint_config_only_ignores_the_confirmed_v3_metadata_mismatch():
    config = yaml.safe_load(ACTIONLINT_CONFIG.read_text(encoding="utf-8"))
    ignores = config["paths"][".github/workflows/codex.yml"]["ignore"]

    assert len(ignores) == 2
    assert any('missing input "app-id"' in pattern for pattern in ignores)
    assert any('input "client-id" is not defined' in pattern for pattern in ignores)
