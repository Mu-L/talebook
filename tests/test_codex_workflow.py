from pathlib import Path


ROOT = Path(__file__).parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "codex.yml"
PROMPT = ROOT / ".github" / "codex" / "prompts" / "comment-response.md"


def workflow_text():
    return WORKFLOW.read_text(encoding="utf-8")


def prompt_text():
    return PROMPT.read_text(encoding="utf-8")


def test_employee_job_is_bounded_and_serialized_per_request_target():
    workflow = workflow_text()

    assert "timeout-minutes: 20" in workflow
    assert (
        "group: codex-${{ github.repository }}-${{ github.event.issue.number || github.event.pull_request.number }}"
        in workflow
    )
    assert "cancel-in-progress: false" in workflow


def test_only_repository_writers_can_trigger_the_employee():
    workflow = workflow_text()

    assert "github.actor != 'github-actions[bot]'" in workflow
    assert "OWNER" in workflow
    assert "MEMBER" in workflow
    assert "COLLABORATOR" in workflow
    assert "github.rest.repos.getCollaboratorPermissionLevel" in workflow
    assert '["admin", "maintain", "write"].includes(permission)' in workflow
    assert "@codex" in workflow
    assert "/codex" in workflow


def test_agent_has_public_network_but_cannot_read_host_credentials():
    workflow = workflow_text()

    assert 'default_permissions = "codex-employee"' in workflow
    assert 'extends = ":workspace"' in workflow
    assert '":root" = "deny"' in workflow
    assert '":minimal" = "read"' in workflow
    assert '":tmpdir" = "deny"' in workflow
    assert '":slash_tmp" = "deny"' in workflow
    assert '[permissions.codex-employee.filesystem.":workspace_roots"]' in workflow
    assert '"." = "write"' in workflow
    assert '".github/workflows" = "read"' in workflow
    assert "[permissions.codex-employee.network.domains]" in workflow
    assert "network_proxy = true" in workflow
    assert "allow_local_binding = false" in workflow
    assert '"*" = "allow"' in workflow
    assert '"localhost" = "allow"' in workflow
    assert '"127.0.0.1" = "allow"' in workflow
    assert 'TMPDIR = "$GITHUB_WORKSPACE/.codex-runtime"' in workflow
    assert "'.codex/tmp/'" in workflow
    assert '"GITHUB_TOKEN"' in workflow
    assert '"CODEX_AUTH_JSON"' in workflow
    assert "--sandbox workspace-write" not in workflow
    assert 'sandbox_mode = "workspace-write"' not in workflow


def test_agent_prompt_is_loaded_from_the_trusted_default_branch():
    workflow = workflow_text()

    assert "const codexPromptTemplate = `${runnerTemp}/codex-comment-response.md`;" in workflow
    assert 'path: ".github/codex/prompts/comment-response.md"' in workflow
    assert "ref: defaultBranch" in workflow
    assert 'core.exportVariable("CODEX_PROMPT_TEMPLATE", codexPromptTemplate)' in workflow
    assert 'cat "$CODEX_PROMPT_TEMPLATE"' in workflow
    assert "cat .github/codex/prompts/comment-response.md" not in workflow


def test_request_context_selects_a_writable_pr_or_issue_target():
    workflow = workflow_text()

    assert "github.rest.git.listMatchingRefs" in workflow
    assert "codex/issue-${issueNumber}-" in workflow
    assert 'core.setOutput("supported_target"' in workflow
    assert 'core.setOutput("target_ref"' in workflow
    assert 'core.setOutput("target_sha"' in workflow
    assert 'core.setOutput("existing_issue_branch"' in workflow
    assert "pr.head.repo.full_name === `${owner}/${repo}`" in workflow
    assert "Multiple Codex branches already exist" in workflow
    assert "a closed or merged pull request" in workflow
    assert "ref: ${{ steps.context.outputs.target_sha }}" in workflow
    assert "ref: master" not in workflow
    assert "persist-credentials: false" in workflow
    assert "CODEX_PR_DIFF" not in workflow
    assert "CODEX_PR_FILES_JSON" not in workflow


def test_agent_contract_requires_a_validated_publish_decision():
    workflow = workflow_text()
    prompt = prompt_text()

    assert "timeout --signal=TERM --kill-after=30s 15m codex exec" in workflow
    assert ".codex-result.json" in prompt
    assert '"ready_to_publish"' in prompt
    assert '"feature"' in prompt
    assert '"commit_message"' in prompt
    assert '"summary"' in prompt
    assert '"tests"' in prompt
    assert ".github/workflows/" in prompt
    assert "Do not commit or push" in prompt
    assert "pull request head" in prompt
    assert "patch artifact" not in prompt


def test_publish_gate_rejects_incomplete_or_unsafe_changes():
    workflow = workflow_text()

    assert "id: publish_gate" in workflow
    assert "RESULT_FILE: .codex-result.json" in workflow
    assert ".ready_to_publish == true" in workflow
    assert 'test("^[a-z0-9]+(-[a-z0-9]+)*$")' in workflow
    assert "Conventional Commit" in workflow
    assert "git rev-parse HEAD" in workflow
    assert "git add -A" in workflow
    assert "git diff --cached --check" in workflow
    assert "design -type f -name '*.wip.html'" in workflow
    assert "^\\.github/workflows/" in workflow
    assert 'echo "ready=true" >> "$GITHUB_OUTPUT"' in workflow
    assert 'echo "ready=false" >> "$GITHUB_OUTPUT"' in workflow


def test_controlled_publisher_uses_a_short_lived_app_token_and_fast_forward_push():
    workflow = workflow_text()

    assert "uses: actions/create-github-app-token@v3" in workflow
    assert "client-id: ${{ secrets.CODEX_APP_CLIENT_ID }}" in workflow
    assert "vars.CODEX_APP_CLIENT_ID" not in workflow
    assert "app-id:" not in workflow
    assert "private-key: ${{ secrets.CODEX_APP_PRIVATE_KEY }}" in workflow
    assert "permission-contents: write" in workflow
    assert "steps.publish_gate.outputs.ready == 'true'" in workflow
    assert "git fetch" in workflow
    assert 'remote_sha="$TARGET_SHA"' in workflow
    assert "Remote branch moved while Codex was running" in workflow
    assert '-H "Authorization: Bearer $APP_TOKEN"' in workflow
    assert 'git commit -m "$COMMIT_MESSAGE"' in workflow
    assert 'git push "$authenticated_remote" "HEAD:refs/heads/$PUBLISH_BRANCH"' in workflow
    assert "--force" not in workflow
    assert 'echo "commit_sha=$(git rev-parse HEAD)" >> "$GITHUB_OUTPUT"' in workflow


def test_first_successful_issue_run_creates_one_draft_pull_request():
    workflow = workflow_text()

    assert 'core.setOutput("default_branch", defaultBranch)' in workflow
    assert "id: create_issue_pr" in workflow
    assert "steps.context.outputs.is_pr != 'true'" in workflow
    assert "steps.context.outputs.existing_issue_pr_number == ''" in workflow
    assert "github-token: ${{ steps.app_token.outputs.token }}" in workflow
    assert "github.rest.pulls.create" in workflow
    assert "draft: true" in workflow
    assert "head: process.env.PUBLISH_BRANCH" in workflow
    assert "base: process.env.DEFAULT_BRANCH" in workflow
    assert "Closes #${process.env.ISSUE_NUMBER}" in workflow
    assert 'core.setOutput("pull_request_url", result.data.html_url)' in workflow


def test_existing_issue_branch_without_a_pr_can_recover_after_a_partial_publish():
    workflow = workflow_text()

    assert 'echo "contract_valid=true" >> "$GITHUB_OUTPUT"' in workflow
    assert "steps.publish_gate.outputs.contract_valid == 'true'" in workflow
    assert "steps.publish_gate.outputs.no_changes == 'true'" in workflow
    assert "steps.context.outputs.existing_issue_branch != ''" in workflow
    assert '[ "$CREATED_PR_OUTCOME" != "success" ]' in workflow
    assert "Draft PR creation failed" in workflow


def test_failed_publication_keeps_a_recovery_patch_but_success_does_not():
    workflow = workflow_text()

    assert "PUBLISH_OUTCOME: ${{ steps.publish.outcome }}" in workflow
    assert 'if [ "$PUBLISH_OUTCOME" = "success" ]' in workflow
    assert 'git diff --cached --quiet "$TARGET_SHA"' in workflow
    assert 'git diff --cached --binary "$TARGET_SHA" > .codex/tmp/codex.patch' in workflow
    assert "if: always() && steps.diff.outputs.has_patch == 'true'" in workflow


def test_comment_reports_the_remote_delivery_result_and_job_fails_closed():
    workflow = workflow_text()

    assert "CODEX_PUBLISH_OUTCOME: ${{ steps.publish.outcome }}" in workflow
    assert "CODEX_PUBLISH_BRANCH: ${{ steps.publish_gate.outputs.publish_branch }}" in workflow
    assert "CODEX_COMMIT_SHA: ${{ steps.publish.outputs.commit_sha }}" in workflow
    assert "CREATED_PR_URL: ${{ steps.create_issue_pr.outputs.pull_request_url }}" in workflow
    assert "Published commit" in workflow
    assert "Not published" in workflow
    assert "No repository changes were required" in workflow
    assert "id: final_status" in workflow
    assert 'if [ "$GATE_READY" != "true" ]' in workflow
    assert 'if [ "$PUBLISH_OUTCOME" != "success" ]' in workflow
