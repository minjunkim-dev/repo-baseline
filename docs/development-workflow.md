# 프로젝트 초기 설정과 일상 개발

이 문서는 셋업 프롬프트를 적용한 프로젝트에서 읽는다. 개발 절차는 [Matt Pocock 스킬](https://github.com/mattpocock/skills)이 맡는다. 이 문서는 스킬이 정하지 않는 이 기준의 선택만 적고, 스킬의 사용법은 옮겨 적지 않는다. 사용법은 설치된 스킬 원문을 따른다.

아래 스킬 이름은 짧게 적는다. Claude Code 플러그인으로 설치했으면 같은 이름의 다른 스킬과 섞이지 않게 `/mattpocock-skills:ask-matt`처럼 플러그인 이름을 붙여 부른다. 다른 런타임은 설치된 원문의 호출 문법을 따른다.

## 처음 한 번

1. Matt Pocock 스킬을 설치한다. Claude Code는 아래 "도구 설치와 확인"대로 프로젝트 설정으로 선언한다. 다른 런타임은 그 저장소 README의 Installation을 따른다. 설치와 유료 서비스 활성화는 별도 승인 범위다.
2. 기존 `CLAUDE.md`가 있으면 고유 규칙을 `AGENTS.md`로 옮기고 `CLAUDE.md`는 지운다. `@AGENTS.md` 한 줄만 있는 `CLAUDE.md`도 이 단계에서 잠시 지운다. 개인·전역 지침은 건드리지 않는다. 셋업 스킬은 `CLAUDE.md`가 있으면 그 파일을 고치므로 이 단계를 먼저 한다.
3. 사용자가 `/setup-matt-pocock-skills`를 실행한다. 에이전트는 실행을 요청만 한다. 지침 파일을 물으면 사용자가 `AGENTS.md`를 고른다. tracker·도메인 문서(`triage`가 설치돼 있으면 라벨도)는 사용자가 스킬의 질문에 답해 정한다. 기존 프로젝트의 관례가 있으면 사용자가 그것을 고른다.
4. 사용하는 런타임이 `AGENTS.md`를 읽는지 확인한다. Claude Code가 `AGENTS.md`를 읽지 못하는 환경이 있으면(버전·세션 종류) `@AGENTS.md` 한 줄만 있는 `CLAUDE.md`를 둔다. 셋업 스킬을 다시 실행할 때는 2단계처럼 이 파일을 잠시 지우고 끝난 뒤 되돌린다. 내용을 복제한 블록·shim·symlink는 만들지 않는다.

완료 조건: `AGENTS.md`의 `## Agent skills` 블록에서 tracker·도메인 문서에 도달할 수 있다. `triage`가 설치돼 있으면 라벨 문서도 포함한다. 이미 설정된 프로젝트는 바뀐 항목만 갱신한다. 초기 셋업을 이유로 제품 기능 구현을 새로 시작하지 않는다.

## 일상 개발

어떤 스킬로 시작할지는 사용자가 `/ask-matt`를 실행해 정한다. `disable-model-invocation: true`인 Matt 스킬은 사용자가 실행한다. 에이전트는 실행을 요청만 하고, 스킬의 질문에는 사용자가 답한다. v1.3.2에서 이 플래그가 있는 스킬은 `/ask-matt`, `/setup-matt-pocock-skills`, `/grill-with-docs`, `/to-spec`, `/to-tickets`, `/triage`, `/implement`, `/retro`, `/wayfinder`다. 태그를 올리면 플래그를 다시 보고 이 목록을 고친다. 각 스킬의 단계는 설치된 원문대로 따른다.

이 기준이 스킬에 더하는 것은 `main`에 들어가는 경계, `POLICY.md` §5의 리뷰 도구, 아래 절의 pstack 배치다.

- 모든 변경은 PR로 `main`에 들어가고 필수 CI가 통과해야 한다. 문 유형은 `POLICY.md` §10만 따른다. 양쪽 문은 맡은 에이전트가 병합할 수 있고, 한쪽 문은 사람이 최종 head를 승인한다(셋업 프롬프트 §10은 그 판정의 병합 절차다). 팀 프로필은 모든 PR에 다른 팀원의 GitHub 승인이 필요하다(`POLICY.md` §9).
- 리뷰·수정은 셋업 프롬프트 §5와 `POLICY.md` §5를 따른다. Security 리뷰와 외부 리뷰(공개 저장소는 CodeRabbit)를 더할 변경도 거기서 정한다. Standards·Spec의 독립 리뷰 이름은 `/matt-code-review` 하나다. `/implement` 안의 리뷰는 `review/independent`로 세지 않는다.
- 에이전트 환경 개선은 사용자가 `/retro`를 실행할 때 한다(`POLICY.md` §6). 에이전트는 실행을 요청만 한다.

## PR 담당자

PR이 열린 뒤의 루프는 PR 담당자가 맡는다. 실행 주체는 저장소 밖의 매니저 봇이거나, 사람이 연 세션이다. 일정을 이 저장소에 두지 않는다(`POLICY.md` §8). 별도 상시 감시 서비스를 이 저장소에 만들었다고 보고하지 않는다. 주간 점검(`prompts/weekly-check.md`)은 읽기 전용이다. 점검으로 고칠 것이 생기면 담당자가 PR로 반영한다.

맡는 일:

- Dependabot PR을 매주 처리한다(`POLICY.md` §2). 문 유형은 `POLICY.md` §10, 리뷰는 §5를 따른다.
- 외부 리뷰 대상 PR은 CodeRabbit 리뷰가 끝날 때까지 기다린다. 병합 전에 달린 CodeRabbit 스레드는 PR 종류와 관계없이 답하고 해결한다. 병합 뒤에 달린 지적은 후속 PR로 처리한다.
- 리뷰 status를 남긴 뒤 `Review status`를 다시 돌린다. 기준 브랜치 갱신으로 멈춘 PR과, 병합 뒤의 main CI를 확인한다.

## pstack을 함께 쓸 때

[pstack](https://github.com/cursor/plugins/tree/main/pstack)이 설치돼 있으면 Matt Pocock 스킬이 다루지 않는 단계에만 쓴다. pstack 스킬은 사람이 부른다. 에이전트는 아래 경우에 실행을 제안만 한다. 설치되지 않았으면 이 절을 건너뛴다.

| 단계 | pstack 스킬 | 제안할 때 |
| --- | --- | --- |
| 자기 검증 | `create-verification-skill` | 앱을 사용자처럼 실행해 증거를 남기는 방법이 프로젝트에 없을 때. 프로젝트당 한 번 |
| PR 전 리뷰 | `blast-radius` | 영향이 diff 밖으로 번질 수 있는 변경 |
| 위험 변경 | `interrogate` | `POLICY.md` §10의 한쪽 문. 외부 리뷰로 세지 않는 추가 의견이다(`POLICY.md` §5) |
| 개선 반영 | `correct` | `retro`로 고른 개선을 `POLICY.md` §6 순서로 막을 때 |

- 같은 일을 하는 pstack `tdd`·`reflect`·`teach`는 쓰지 않는다. `retro`는 다른 회고 스킬로 바꾸지 않는다(`POLICY.md` §6).
- 검증 스킬은 지침 파일을 `AGENTS.md` 하나로 두는 규칙(셋업 프롬프트 §3)의 유일한 예외다. `.claude/settings.json` 같은 런타임 설정 파일은 지침 파일이 아니다. 주로 쓰는 런타임의 프로젝트 스킬 경로에 하나만 두고 `AGENTS.md`에서 경로를 연결한다. 생성 기본 경로(`.cursor/skills/`)가 그 런타임과 다르면 옮긴다. 다른 런타임용 사본이나 symlink는 만들지 않는다. `tools/apply_baseline.py`가 복사한 스킬(`.github/repo-baseline.json`에 있는 `matt-code-review` 등)은 이 저장소가 관리하는 파일이라 이 규칙의 대상이 아니다. 지우거나 하나로 합치지 않는다.

## 도구 설치와 확인

필수 리뷰 도구는 `POLICY.md` §5의 표가 정한다. 이 절은 도구를 어느 층에 두는지(`POLICY.md` §7), 설치와 확인 방법, 선택 도구만 다룬다.

| 층 | 무엇 | 닿는 곳 |
| --- | --- | --- |
| 저장소 | `AGENTS.md`, `@AGENTS.md`만 있는 `CLAUDE.md`, `.agents/skills/`, `.claude/skills/`, 비밀값 없는 `.mcp.json`(`claude mcp add --scope project`), `.claude/settings.json` | 모든 팀원과 클라우드 세션 |
| 계정 | 클라우드 환경 설정·setup script·Secret·커넥터, 계정에 켠 스킬 | 그 사람의 클라우드 세션 |
| 로컬 | `~/.agents/skills`, `~/.claude`의 스킬·플러그인·MCP | 그 컴퓨터의 세션만 |

- 클라우드에 닿는 범위(공식 문서, 2026-11-04 확인):
  - Claude Code 클라우드 세션: 저장소의 `CLAUDE.md`·`.claude/skills/`·`.mcp.json`(저장소 하나인 세션)·`.claude/settings.json`을 읽는다. `~/.claude`의 스킬·플러그인·MCP와, 저장소 `.claude/settings.json`이 켠 플러그인은 읽지 않는다.
  - Codex: 저장소의 `.agents/skills/`를 읽는다. 클라우드 작업에서도 읽는지는 문서에 없다(미확인).
  - Cursor: `.agents/skills/`·`.cursor/skills/`와 호환용 `.claude/skills/`를 읽는다. Cloud Agent의 MCP와 Secret은 저장소 파일이 아니라 팀 대시보드에서 정한다.
- 계정 층은 저장소에서 설치할 수 없다. 사람마다 등록할 것(클라우드별 커넥터 URL, Secret 이름, setup script 내용)을 프로젝트 작업 문서에 적는다. 비밀값은 적지 않는다.
- 확인(doctor): 저장소 층은 `python3 scripts/check_repo_baseline.py`가 복사한 스킬·검사기의 해시와 `.mcp.json`의 비밀값을 검사한다(필수 CI). 로컬 층은 아래 각 도구의 확인 명령으로 따로 본다.

- Claude Code: `repo-baseline`의 `templates/claude-settings.json`을 프로젝트의 `.claude/settings.json`으로 둔다(두 프로필 공통).
  - 리뷰 관문 스킬 `matt-code-review`는 저장소에 커밋돼 있으므로 플러그인 없이도 `/matt-code-review`로 부른다. 플러그인은 나머지 Matt Pocock 스킬을 쓰기 위한 로컬 편의다.
  - Matt Pocock 마켓플레이스를 태그(`ref`)로 고정해 등록하고 `mattpocock-skills`를 켠다. 등록은 각자 그 폴더를 신뢰한 뒤에 적용된다. 프로젝트 설정의 마켓플레이스 source는 `sha`를 받지 않으므로 태그로만 고정한다. 태그는 옮겨질 수 있어 주간 점검이 commit을 대조한다. 태그를 올리는 PR은 신뢰 경계 변경(`POLICY.md` §5)으로 리뷰한다.
  - 같은 스킬을 다른 마켓플레이스에서도 켜지 않는다. 이름이 겹친다.
  - `.env*`(`.env.example` 제외) 읽기를 막는다. Claude의 파일 도구와 `cat` 같은 인식되는 셸 명령에만 적용된다. 파일을 직접 여는 스크립트는 막지 못한다. 모든 프로세스를 막으려면 sandbox를 쓴다.
  - 확인: `claude plugin list`에 `mattpocock-skills@mattpocock`가 켜져 있다. 고정한 태그는 `.claude/settings.json`의 `ref`다.
- Semgrep CLI(선택): 설치돼 있으면 Security 리뷰에서 함께 실행한다. 확인: `semgrep --version`.
- 정기 Security 감사: Cloudflare `security-audit`를 `npx skills add https://github.com/cloudflare/security-audit-skill --skill security-audit`로 설치한다. 개인 경로의 사본을 쓰지 않는다. 이 저장소는 release가 없어 버전으로 고정할 수 없으므로 설치한 commit을 감사 기록에 적는다. 확인: 설치 경로에 `security-audit/SKILL.md`가 있고, `node --version`이 나온다(검증기에 필요). 설치 commit은 감사 기록에 적는다.
  - 실행 시점은 `POLICY.md` §5의 표를 따른다. 전체 감사 대신 마지막 기록의 `source_ref` 이후 diff로 범위를 좁혀도 된다.
  - OS 수준 sandbox가 없으면 대상 코드를 실행하지 않는 정적 감사만 한다. 결과 폴더 기본값은 저장소 밖(`~/security-audit-skill/<repo>/run-N`)이다.
  - 기록은 `POLICY.md` §5대로 `security-audit` 라벨의 Issue에 날짜·`source_ref`·설치 commit·지적 수만 남긴다. 공개 저장소의 지적 내용은 비공개 security advisory에 둔다.
  - Strix는 쓰지 않는다. Docker·LLM 키·쓰기 가능한 마운트와 실제 공격 실행이 필요하다.
- `/simplify`(선택): 코드가 바뀐 PR에서만 쓴다. 정리는 필수 리뷰 역할이 아니다. 스타일만의 지적은 셋업 프롬프트 §5대로 버린다.

런타임별 같은 역할의 도구:

| 런타임 | Standards·Spec | 버그 찾기 | Security |
| --- | --- | --- | --- |
| Claude Code | `/matt-code-review`(`.claude/skills/`) | 내장 `/code-review` | 내장 `/security-review` |
| Codex | `matt-code-review`(`.agents/skills/`) | 미확인 | 미확인 |
| Cursor | `matt-code-review`(`.agents/skills/`) | 미확인 | 미확인 |

필수 리뷰는 Claude Code에서 돌린다. 미확인 칸은 Claude Code가 없을 때만 `POLICY.md` §5의 대체 규칙을 쓰고, 무엇을 썼는지 리뷰 기록에 남긴다.
