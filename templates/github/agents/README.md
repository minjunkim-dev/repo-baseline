# 에이전트 권한 예시

하네스 거부 규칙은 보안 경계가 아니다. `gh api`, `gh auth token`과 `curl`, 셸 스크립트, `git -C . push` 같은 다른 표기로 우회된다. 브랜치 보호와 필수 CI도 소유자 `gh` 로그인으로 도는 에이전트의 병합까지는 막지 못한다(POLICY §5). 이 설정은 실수를 줄이는 1차 장치이고, 기계적으로 막으려면 [review-gate 프로필](../../../profiles/review-gate/)을 켠다.

`gh api`는 인자 패턴으로 읽기와 쓰기를 확실히 가를 수 없어서 전부 확인(`ask`)을 받는다. 보호·ruleset 경로는 거부한다. 이슈·PR 댓글은 `gh issue comment`, `gh pr comment`처럼 하위 명령으로 쓴다.

`main` push 거부는 명시적 표기만 잡는다. `main`에 있는 채로 `git push origin`을 하면 통과한다. 그 경우는 서버의 브랜치 보호(PR 필수, `enforce_admins`)가 거절한다. GitHub 프로필을 켜지 않은 저장소에서는 이 구멍이 남는다.

막을 것은 네 가지다: `.env` 읽기, `gh pr merge`, `main`으로의 push, 브랜치 보호·저장소 설정을 쓰는 `gh api`.

확인일: 2026-11-08. 하네스가 바뀌면 링크한 공식 문서를 다시 본다.

## Claude Code

`claude-settings.json`을 프로젝트의 `.claude/settings.json`으로 복사한다. 이미 있으면 `permissions.deny`만 합친다.

- 문법: [Permissions](https://code.claude.com/docs/en/permissions), [Settings](https://code.claude.com/docs/en/settings). `*`는 규칙의 어느 자리에나 올 수 있다. `.env` 예시 `Read(./.env)`, `Read(./.env.*)`는 Settings 문서의 예시와 같다. 하위 폴더의 `.env`는 `**/` 규칙으로 막는다.
- `.env.example`도 막힌다. 필요하면 사람이 내용을 알려 준다.
- `gh api *protection*`은 보호 설정 읽기도 막는다. 감사는 소유자가 `tools/apply_github_settings.py`로 한다.

선택: Matt Pocock 스킬 플러그인을 쓰려면 같은 파일에 아래 두 키를 넣는다.

```json
"extraKnownMarketplaces": {
  "mattpocock": { "source": { "source": "github", "repo": "mattpocock/skills", "ref": "v1.3.2" } }
},
"enabledPlugins": { "mattpocock-skills@mattpocock": true }
```

## Codex

[Rules](https://developers.openai.com/codex/rules)로 명령을 막는다. 프로젝트의 `.codex/rules/default.rules`에 둔다. 프로젝트 `.codex/`를 신뢰한 경우에만 읽힌다. 기능은 실험 단계다.

```python
prefix_rule(pattern = ["gh", "pr", "merge"], decision = "forbidden", justification = "병합은 사람이 한다")
prefix_rule(pattern = ["git", "push"], decision = "prompt", justification = "main으로 push하지 않는다")
prefix_rule(pattern = ["gh", "repo", "edit"], decision = "forbidden", justification = "저장소 설정은 소유자가 바꾼다")
prefix_rule(pattern = ["gh", "api"], decision = "prompt", justification = "보호·설정 쓰기인지 사람이 본다")
```

- 규칙은 정확한 접두사로만 맞춘다. 대상 브랜치(`main`)나 `gh api`의 경로는 가려낼 수 없어서 `git push`와 `gh api`는 `prompt`로 둔다.
- 문서는 규칙이 "샌드박스 밖에서 실행할 명령"을 다룬다고 적는다. 샌드박스 안의 명령에도 적용되는지: 미확인.
- `.env` 같은 파일 읽기를 막는 설정: 미확인.

## Cursor

CLI는 [Permissions](https://cursor.com/docs/cli/reference/permissions)대로 프로젝트의 `.cursor/cli.json`에 둔다. deny가 allow보다 우선한다.

```json
{
  "permissions": {
    "deny": ["Read(.env*)", "Shell(gh:pr merge*)", "Shell(git:push*)", "Shell(gh:api*)"]
  }
}
```

- `Read(.env*)`는 문서 예시 그대로다.
- `Shell(명령:인자)`의 인자 글롭은 문서 예시가 `curl:*`뿐이다. `gh:pr merge*`처럼 공백이 든 인자가 맞는지: 미확인. 적용 뒤 한 번 시험한다.
- IDE(에디터 안 에이전트)에서 같은 파일을 읽는지, 같은 의미의 설정이 무엇인지: 미확인.
