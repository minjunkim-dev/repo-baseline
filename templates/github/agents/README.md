# 에이전트 권한 예시

하네스 거부 규칙은 보안 경계가 아니다. `gh api`, `gh auth token`과 `curl`, 셸 스크립트, `git -C . push` 같은 다른 표기로 우회된다. 브랜치 보호와 필수 CI도 소유자 `gh` 로그인으로 도는 에이전트의 병합까지는 막지 못한다(POLICY §5). 이 설정은 실수를 줄이는 장치다. 기계적으로 막아야 하면 에이전트를 별도 OS 사용자와 GitHub 계정으로 돌린다.

`gh api`는 인자 패턴으로 읽기와 쓰기를 확실히 가를 수 없어서 전부 확인(`ask`)을 받는다. 보호·ruleset 경로는 거부한다. 이슈·PR 댓글은 `gh issue comment`, `gh pr comment`처럼 하위 명령으로 쓴다.

`main` push 거부는 명시적 표기만 잡는다. `main`에 있는 채로 `git push origin`을 하면 통과한다. 그 경우는 서버의 브랜치 보호(PR 필수, `enforce_admins`)가 거절한다. GitHub 프로필을 켜지 않은 저장소에서는 이 구멍이 남는다.

막을 것은 세 가지다: `.env` 읽기, `main`으로의 push, 브랜치 보호·저장소 설정을 쓰는 `gh api`. `gh pr merge`는 막지 않고 매번 확인을 받는다. 되돌리기 쉬움 PR은 소유자가 지시하면 에이전트가 병합할 수 있기 때문이다(POLICY §5). 확인 창에서 PR 번호와 `--match-head-commit`이 붙었는지 본다.

확인일: 2026-11-08. 하네스가 바뀌면 링크한 공식 문서를 다시 본다.

## Claude Code

`claude-settings.json`을 프로젝트의 `.claude/settings.json`으로 복사한다. 이미 있으면 `permissions.deny`와 `permissions.ask`를 합친다. 예전 예시에서 가져온 `gh pr merge` deny 항목은 지운다. deny가 ask보다 먼저 걸려서 남아 있으면 병합이 계속 막힌다.

- 문법: [Permissions](https://code.claude.com/docs/en/permissions), [Settings](https://code.claude.com/docs/en/settings). `*`는 규칙의 어느 자리에나 올 수 있다. `.env` 예시 `Read(./.env)`, `Read(./.env.*)`는 Settings 문서의 예시와 같다. 하위 폴더의 `.env`는 `**/` 규칙으로 막는다.
- 지침 파일은 `AGENTS.md` 하나다. Claude Code는 작업 폴더와 그 위 폴더에 `CLAUDE.md`·`.claude/CLAUDE.md`·`CLAUDE.local.md`가 없을 때 `AGENTS.md`를 읽는다([Memory](https://code.claude.com/docs/en/memory), 확인일 2026-11-09). 개인용 `CLAUDE.local.md`를 하나 두기만 해도 `AGENTS.md`를 읽지 않으므로 만들지 않는다. 꼭 써야 하면 사용자 설정 `~/.claude/settings.json`에서 `pluginConfigs."cc-plugin-agents-md@builtin".options.instructionFiles`를 `"claude-md-and-agents-md"`로 둔다. 이 설정은 프로젝트의 `.claude/settings.json`에 두면 무시된다.
- `.env.example`도 막힌다. 필요하면 사람이 내용을 알려 준다.
- `gh api *protection*`은 보호 설정 읽기도 막는다. 감사는 소유자가 `tools/apply_github_settings.py`로 한다.
- Claude 프로젝트의 클라우드 스레드는 저장소의 `.claude/settings.json`을 읽지 않는다([Claude projects](https://code.claude.com/docs/en/claude-projects), 확인일 2026-11-08). 그 스레드에는 이 거부 규칙이 없다. 그 환경에는 비밀값을 두지 않고, 병합 권한 없는 토큰만 준다(POLICY §5·§7).

선택: Matt Pocock 스킬 플러그인을 쓰려면 같은 파일에 아래 두 키를 넣는다.

```json
"extraKnownMarketplaces": {
  "mattpocock": { "source": { "source": "github", "repo": "mattpocock/skills", "ref": "v1.3.2" } }
},
"enabledPlugins": { "mattpocock-skills@mattpocock": true }
```

이 두 키는 로컬 세션에서만 플러그인을 설치한다. 클라우드 세션은 저장소 설정에 적은 플러그인을 설치하지 않는다([Cloud environments](https://code.claude.com/docs/en/cloud-environments#what-carries-over-from-your-setup), 확인일 2026-11-08). 클라우드에서도 써야 하면 쓰는 스킬만 저장소에 커밋한다(Claude `.claude/skills/`, Codex·Cursor `.agents/skills/`). Claude 프로젝트의 클라우드 스레드는 저장소 스킬도 읽지 않는다. 그때는 [Claude projects](https://code.claude.com/docs/en/claude-projects#get-skills-plugins-connectors-and-tools-into-threads)를 따른다. 코어는 플러그인 없이 돈다.

플러그인·스킬은 같은 작업을 켤 때와 끌 때 한 번씩 돌려 보고, 결과가 나아진 것만 켠다.

Matt 스킬의 기본 동작 중 [POLICY.md](../../../POLICY.md)와 어긋나는 것:

- `/implement`는 끝에 같은 세션에서 `/code-review`를 부른다. 하위 에이전트는 새 컨텍스트지만, 기준을 고르고 결과를 받아들이는 쪽이 구현 세션이라서 POLICY §3의 리뷰가 아니다. 리뷰는 [prompts/review.md](../../../prompts/review.md)로 따로 한다. 되돌리기 쉬움이면 구현 대화를 물려받지 않는 하위 에이전트 하나에게 그 파일 경로와 PR 링크만 주어 맡겨도 되고, 어려움이면 새 세션에서 부른다(POLICY §3). spec으로는 PR 본문 Summary의 완료 기준을, 기준 문서로는 `REVIEW.md`를 따로 지정한다. 라운드 상한과 직접 수정 규칙은 `REVIEW.md`에 있다.
- `/retro`는 기본으로 지금 세션 하나를 보고, 규칙을 `CODING_STANDARDS.md`에 넣자고 제안한다. 이 저장소의 회고는 같은 지적이 반복되거나 사람이 원할 때 [prompts/retro.md](../../../prompts/retro.md)로 한다. 제안 중 사람이 고른 것만 반영한다(POLICY §6).
- `/pr`이 만든 본문은 `.github/pull_request_template.md`의 칸에 맞춘다.

코어 기준에 없는 것을 이 스킬로 채울 수 있다. 둘 다 사람이 부를 때만 돈다(`disable-model-invocation`, [v1.3.2](https://github.com/mattpocock/skills/tree/v1.3.2/skills), 확인일 2026-11-10).

- 깊은 모듈: `/improve-codebase-architecture`가 최근 자주 바뀐 영역에서 얕은 모듈을 찾아 HTML 보고서로 보여 주고, 고른 후보를 질문으로 다듬는다. 회고에서 테스트가 구현에 묶인다는 지적이 반복될 때 쓴다([prompts/retro.md](../../../prompts/retro.md) 7번). 용어는 `codebase-design`, 도메인 이름은 `GLOSSARY.md`를 따른다.
- TypeScript 저장소는 `/setup-ts-deep-modules`로 패키지 경계(진입 파일만 import)를 dependency-cruiser 검사로 만들 수 있다. 리뷰가 아니라 check 층에 들어간다. 이 스킬은 v1.3.2 플러그인에 들어 있지 않다(`skills/in-progress/`).

Claude Code에는 같은 이름의 내장 `/code-review`가 있다. Matt 플러그인으로 설치했으면 `/mattpocock-skills:code-review`처럼 플러그인 이름을 붙여 부른다.

## Codex

[Rules](https://developers.openai.com/codex/rules)로 명령을 막는다. 프로젝트의 `.codex/rules/default.rules`에 둔다. 프로젝트 `.codex/`를 신뢰한 경우에만 읽힌다. 기능은 실험 단계다.

```python
prefix_rule(pattern = ["gh", "pr", "merge"], decision = "prompt", justification = "지시받은 되돌리기 쉬움 PR인지 사람이 본다")
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
- 문서의 규칙 종류는 allow와 deny뿐이라 병합에 확인을 받는 설정이 없다. 그래서 `gh pr merge`를 deny로 둔다. Cursor로 POLICY §5의 에이전트 병합을 쓰려면 이 항목을 빼고, 병합 명령마다 PR 번호와 `--match-head-commit`을 사람이 본다. 승인하지 않은 명령을 Cursor가 실행 전에 묻는지는 미확인이다.
- `Shell(명령:인자)`의 인자 글롭은 문서 예시가 `curl:*`뿐이다. `gh:pr merge*`처럼 공백이 든 인자가 맞는지: 미확인. 적용 뒤 한 번 시험한다.
- IDE(에디터 안 에이전트)에서 같은 파일을 읽는지, 같은 의미의 설정이 무엇인지: 미확인.
