# pr-conventions 프로필

선택 프로필이다. PR 제목·브랜치 이름·본문 섹션을 CI에서 검사한다. 게이트가 아니다. 병합 조건은 기본값(브랜치 보호 + 필수 CI + 사람 병합)이 정한다.

## 언제 켜는가

- 여러 사람이나 여러 에이전트가 PR을 열어서 제목·브랜치 형식이 자꾸 어긋날 때.
- 릴리스 노트나 변경 로그를 Conventional Commits 제목에서 뽑을 때.
- 미완성 기능을 꺼진 피처 플래그 뒤에 두는 규칙(`config/feature-flags.json`)을 기계로 확인하고 싶을 때.

혼자 작은 PR을 squash로 병합하면 켜지 않아도 된다.

## 검사하는 것

- 제목: Conventional Commits, 소문자 또는 한글 설명, 72자 이하, 끝에 마침표 없음.
- 브랜치: `<type>/<issue>-<slug>`. `docs`·`build`·`ci`·`chore`는 이슈 번호를 생략할 수 있다. 에이전트 접두사(`claude/`, `codex/` 등)는 설정으로 허용한다.
- 본문: `## Summary`, `## Evidence`, `## Merge Danger`, `Door:` 한 줄, `Author: <도구> / <모델>` 한 줄. 도구 이름은 아무것이나 된다.
- `feat`·`fix`·`refactor`·`perf`·`test`·`revert`는 `Refs #N`, `Closes #N`, 또는 트래커 ID(`Fixes ENG-123`)가 있어야 한다.
- 기본값으로 `AGENTS.md`가 있어야 한다. `CLAUDE.md`는 없거나 `@AGENTS.md` 한 줄이어야 한다. 다른 내용이 있으면 실패한다. 둘 다 있으면 Claude Code는 `CLAUDE.md`만 읽어서 지침이 갈라지기 때문이다. `CLAUDE.md`를 아예 두지 않으려면 아래 설정에서 `"reject_claude_md": true`를 둔다. `"require_agents_md": false`면 `CLAUDE.md` 내용도 보지 않는다.
- 피처 플래그 파일이 있으면 그 형식과 `remove_by` 날짜.

## 켜는 법

1. 소비 레포의 `scripts/`에 `workflow_policy.py`, `test_workflow_policy.py`, `pr_author.py`를 복사한다.
2. `pr-policy.yml`을 `.github/workflows/pr-policy.yml`로 복사한다. 트리거는 `main`을 base로 하는 PR만 본다.
3. 기본값을 바꿀 때만 `.github/workflow-policy.json`을 둔다. 예:

```json
{"feature_flags": false, "bot_branch_prefixes": ["claude", "codex", "cursor", "dependabot"]}
```

4. 필수 체크로 만들지는 프로젝트가 정한다. `pull_request` 이벤트라 PR이 이 workflow 파일을 고쳐 검사를 빼 버릴 수 있다.
