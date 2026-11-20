# pr-conventions 프로필

선택 프로필이다. PR 제목·브랜치 이름·본문 섹션을 CI에서 검사한다. 게이트가 아니다. 병합 조건은 기본값(브랜치 보호 + 필수 CI + 소유자가 정하는 병합)이 정한다.

## 언제 켜는가

- 여러 사람이나 여러 에이전트가 PR을 열어서 제목·브랜치 형식이 자꾸 어긋날 때.
- 릴리스 노트나 변경 로그를 Conventional Commits 제목에서 뽑을 때.
- 미완성 기능을 꺼진 피처 플래그 뒤에 두는 규칙(`config/feature-flags.json`)을 기계로 확인하고 싶을 때.

혼자 작은 PR을 squash로 병합하면 켜지 않아도 된다.

## 검사하는 것

- 제목: Conventional Commits, 소문자 또는 한글 설명, 72자 이하, 끝에 마침표 없음.
- 브랜치: `<type>/<issue>-<slug>`. `docs`·`build`·`ci`·`chore`는 이슈 번호를 생략할 수 있다. 에이전트 접두사(`claude/`, `codex/` 등)는 설정으로 허용한다.
- 본문: `## Summary`, `## Evidence`, `## Merge Danger`, `되돌리기: 쉬움` 또는 `되돌리기: 어려움` 한 줄(옛 `Door:` 줄도 받는다), `Author: <도구> / <모델>` 한 줄. 도구 이름은 아무것이나 된다.
- `feat`·`fix`·`refactor`·`perf`·`test`·`revert`는 `Refs #N`, `Closes #N`, 또는 트래커 ID(`Fixes ENG-123`)가 있어야 한다.
- 기본값으로 `AGENTS.md`가 있어야 한다. `CLAUDE.md`·`CLAUDE.local.md`는 없거나 `@AGENTS.md` 한 줄, `.claude/CLAUDE.md`는 없거나 `@../AGENTS.md` 한 줄이어야 한다(import는 그 파일 기준 상대 경로다). 다른 내용이 있으면 실패한다. 이 중 하나라도 있으면 Claude Code는 기본 설정에서 `AGENTS.md`를 읽지 않아 지침이 갈라지기 때문이다. 이 파일들을 아예 두지 않으려면 아래 설정에서 `"reject_claude_md": true`를 둔다. `"require_agents_md": false`면 내용도 보지 않는다.
- 피처 플래그 파일이 있으면 그 형식과 `remove_by` 날짜.

## 켜는 법

1. 소비 레포의 `scripts/`에 `workflow_policy.py`, `test_workflow_policy.py`, `pr_author.py`를 복사한다.
2. `pr-policy.yml`을 `.github/workflows/pr-policy.yml`로 복사한다. 트리거는 `main`을 base로 하는 PR만 본다.
3. 기본값을 바꿀 때만 `.github/workflow-policy.json`을 둔다. 예:

```json
{"feature_flags": false, "bot_branch_prefixes": ["claude", "codex", "cursor", "dependabot"]}
```

4. 이미 쓰던 레포가 검사기를 올릴 때: workflow는 base 커밋의 검사기를 돌린다. 기본 설정에서 `CLAUDE.md`를 새로 더하려면 검사기 PR을 먼저 병합하고 다음 PR에서 더한다. `reject_claude_md: false`로 내용 있는 `CLAUDE.md`를 두던 레포는 검사기를 올리는 같은 PR에서 내용을 `AGENTS.md`로 옮기고 `CLAUDE.md`를 지우거나 `@AGENTS.md` 한 줄로 바꾼다(옛 검사기는 이 PR을 통과시킨다).
5. 필수 체크로 만들지 않는다. 이 workflow는 `pull_request`에서만 돌고 `github.event.pull_request`를 읽는다. 머지 큐의 `merge_group` 실행에서는 돌지 않으므로, 필수 체크로 두면 큐에 넣은 PR이 병합되지 않는다(POLICY §5). 또 `pull_request` 이벤트라 PR이 이 workflow 파일을 고쳐 검사를 빼 버릴 수 있다.

## 머지 큐의 리뷰한 head 검사

`reviewed_head.py`는 위 검사와 따로 쓸 수 있다. 큐에 들어간 PR head가 PR 본문 Review 칸의 마지막 「리뷰한 head와 되돌리기:」 SHA와 같은지 `merge_group`에서 확인한다(POLICY §5 "그 뒤 push가 있으면 다시 리뷰한다"). 리뷰 뒤 커밋이 올라간 채 병합되는 일을 막는다. 본문은 PR을 고칠 수 있는 누구나 바꿀 수 있으므로 실수를 잡는 검사이지 보안 경계가 아니다.

- 통과: SHA가 같다. Dependabot PR(큐 커밋 작성자 이메일로 판정). repo-baseline 동기화 PR(Author 줄이 `tools/sync_consumers.py`이고, base에 manifest가 있고, 바뀐 경로가 모두 manifest와 base manifest가 기록한 경로. 이전 PR은 리뷰를 거친다).
- 실패: SHA가 다르다. 「리뷰한 head와 되돌리기:」 줄에 40자 SHA가 없다. 큐 브랜치 이름을 읽지 못했다.

켜는 법:

1. 소비 레포의 `scripts/`에 `reviewed_head.py`, `test_reviewed_head.py`를 복사한다(hash-copy를 쓰면 manifest에 더한다).
2. 필수 체크에 묶인 `merge_group` job에 단계를 더한다. job에는 `fetch-depth: 0` 체크아웃과 `pull-requests: read` 권한이 있어야 한다.

```yaml
      - name: Reviewed head
        if: github.event_name == 'merge_group'
        env:
          GH_TOKEN: ${{ github.token }}
          QUEUE_REF: ${{ github.event.merge_group.head_ref }}
          QUEUE_AUTHOR: ${{ github.event.merge_group.head_commit.author.email }}
          BASE_SHA: ${{ github.event.merge_group.base_sha }}
        run: python3 scripts/reviewed_head.py
```

3. 켜기 전에 열린 PR의 Review 칸이 `prompts/review.md` 「보고」 형식인지 본다. 짧은 SHA나 다른 문장으로 적은 PR은 큐에서 빠진다.
