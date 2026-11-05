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

이 기준이 스킬에 더하는 것은 `main`에 들어가는 경계, `POLICY.md` §5의 리뷰 도구, 아래 "역할 분담"의 작성 도구·리뷰 모델, 그 아래 절의 pstack 배치다.

- 모든 변경은 PR로 `main`에 들어가고 필수 CI가 통과해야 한다. 문 유형은 `POLICY.md` §10만 따른다. 양쪽 문은 맡은 에이전트가 병합할 수 있고, 한쪽 문은 사람이 최종 head를 승인한다(셋업 프롬프트 §10은 그 판정의 병합 절차다). 1인 프로필의 게이트 경로 PR은 소유자 댓글 `한쪽 문 승인: <head sha>`가 현재 head와 같고, 필수 체크 `Review status`가 그 댓글을 통과해야 병합된다(`POLICY.md` §5·§10). 팀 프로필은 모든 PR에 다른 팀원의 GitHub 승인이 필요하다(`POLICY.md` §9).
- 리뷰·수정은 셋업 프롬프트 §5와 `POLICY.md` §5를 따른다. Security 리뷰와 외부 리뷰(공개 저장소는 CodeRabbit)를 더할 변경도 거기서 정한다. Standards·Spec의 독립 리뷰 이름은 `/matt-code-review` 하나다. `/implement` 안의 리뷰는 `review/independent`로 세지 않는다.
- 에이전트 환경 개선은 사용자가 `/retro`를 실행할 때 한다(`POLICY.md` §6). 에이전트는 실행을 요청만 한다.

## 역할 분담

코드를 쓰는 곳과 쓰지 않는 곳을 나눈다.

- Grok Bot은 접수, Issue, 작업 분해, 배정, CI와 리뷰 추적, 근거 확인, 보고를 맡는다. 코드를 쓰지 않는다.
- 코드는 Claude Code(Mac)와 Cursor 클라우드 에이전트가 쓴다.
- 비밀 정보는 Mac에만 둔다. Claude Code와 `gh` 토큰이 그렇다. Grok Bot이 쓰는 공유 컴퓨터에는 두지 않는다.

구독은 2026-11-05에 소유자가 정한 둘이다. Claude Code. X 구독으로 쓰는 Cursor와 Grok Bot. 별도의 GPT 구독과 Codex 구독은 없다. Codex 클라우드, ChatGPT, `codex` CLI로는 PR을 쓰거나 리뷰하지 않는다. 아래 런타임 표의 Codex 행은 그 런타임을 썼을 때의 기록이다. 배정과 리뷰의 대상이 아니다. Cursor 모델 목록에 있는 GPT는 Cursor 안에서 쓴다. 그 GPT는 아래 Cursor 쪽이다.

PR을 쓰는 도구는 아래 순서로 정한다.

1. 다음에 하나라도 해당하면 Claude Code(소유자의 Mac)다. `gh` 인증이 필요한 조작. 시뮬레이터 또는 실기기 테스트. 로컬 서버 실행. 그 밖에 소유자의 Mac에만 있는 비밀이 필요한 조작. 소유자가 그 작업을 대화로 따라가겠다고 한 경우.
2. 1에 해당하지 않으면 Cursor 클라우드 에이전트다. 1인지 판단할 정보가 부족할 때도 2다. Grok Bot이 작업을 이슈 하나로 나눈 뒤에 보낸다. 에이전트 하나는 이슈 하나만 맡는다. 이슈가 여럿이면 병렬로 보낸다. 클라우드에서 끝까지 검사할 수 있다는 뜻은, 그 이슈의 검사가 이 저장소의 CI나 클라우드 에이전트의 명령으로 끝나고 1의 조건이 없는 것이다. 1의 조건이 보이면 그 이슈는 1이다. 끝까지 검사할 수 있는지 모르면 2로 보낸다.
3. 2로 보낸 작업이 1의 조건에서 막히면 그 에이전트는 더 커밋하지 않고 남은 작업을 Claude Code로 넘긴다. 클라우드에 비밀을 두거나 막힌 단계를 빼지 않는다. 1의 조건이 아닌 이유로 막히면 더 커밋하지 않고 그 이유를 소유자에게 알린다.

PR 본문에 작성 도구와 작성 모델을 적는다. 둘 중 하나가 없으면 리뷰를 시작하지 않는다.

- `작성 도구:` `Claude Code`, `Cursor 클라우드 에이전트`, `사람` 중 하나.
- `작성 모델:` 도구가 보여주는 모델 이름. `사람`이면 `없음`.

마지막으로 커밋한 도구가 최종 작성 도구다. 넘기기 전에 Cursor 클라우드 에이전트가 커밋했으면 `이전 작성 도구`와 `이전 작성 모델`을 본문에 더 적는다. 이전 모델이 여러 개면 이름을 모두 적는다. Grok Bot은 작성 도구가 아니다. Grok Bot이 PR을 열어도 위 두 줄은 코드를 쓴 도구와 그 모델이다.

작성 도구와 작성 모델의 쪽은 같아야 한다. `Claude Code`의 모델은 아래 Claude Code 쪽(Opus, Sonnet)이다. `Cursor 클라우드 에이전트`의 모델은 아래 Cursor 쪽(Grok, Composer, Gemini, GPT)이다. 쪽이 다르면 리뷰를 시작하지 않고 소유자에게 알린다.

리뷰 모델은 작성 모델의 반대쪽이다. 리뷰 모델의 토큰이 최종 작성 모델 또는 이전 작성 모델의 토큰과 같으면 그 리뷰는 무효다. 토큰은 다음 문단이 정한다.

| 작성 모델의 쪽 | 리뷰하는 쪽 | 그 쪽의 모델 |
| --- | --- | --- |
| Claude Code 쪽 | Cursor | Grok, Gemini, GPT, Composer |
| Cursor 쪽 | Claude Code | Opus, Sonnet |
| `작성 모델`이 `없음` (`작성 도구`는 `사람`) | Claude Code | Opus, Sonnet |

모델 이름은 대소문자를 무시한다. 이름에 `chatgpt` 또는 `codex`가 있으면 무효다. 그 다음 토큰을 센다. 토큰은 `opus`, `sonnet`, `composer`, `grok`, `gemini`, `gpt`다. 이름에 들어 있는 토큰이 하나면 그 모델이다. 없거나 둘 이상이면 무효다. 같은 토큰이면 같은 모델이다. `grok-4.7`과 `cursor-grok-4.6`은 둘 다 Grok이다. 표의 모델은 이 토큰이다. 도구가 보여주는 전체 이름은 토큰이 하나일 때 그 모델로 적는다. 토큰을 더하려면 이 절을 먼저 고친다.

축마다 모델과 effort를 고른다. 어느 축을 돌리는지는 `POLICY.md` §5의 "언제"다. 가벼운 경로(문서, 또는 신뢰 경계가 아닌 설정만 바꾸는 양쪽 문)는 Standards·Spec만 돌린다.

| 축 | 모델 | effort |
| --- | --- | --- |
| 버그 찾기 | 리뷰하는 쪽의 강한 모델 | `high` |
| Security | 리뷰하는 쪽의 강한 모델 | `high` |
| Standards | 리뷰하는 쪽의 가벼운 모델 | 아래 허용 값 중 실제로 쓴 값 |
| Spec | 리뷰하는 쪽의 가벼운 모델 | 아래 허용 값 중 실제로 쓴 값 |

effort 허용 값은 `low`, `medium`, `high`, `xhigh`, `max`, `설정 없음`이다. 이 값은 리뷰 모델의 effort다. Bugbot 설정의 Low·Default·High·Smart와 같지 않고, 그 대응은 이 문서에 없다. Bugbot을 버그 찾기 도구로 쓰는지는 아래 런타임 표가 미확인인 동안 정하지 않는다. 버그 찾기와 Security는 `high`다. effort 설정 자체가 없을 때만 `설정 없음`이다. `high`를 고를 수 있는 제품에서 다른 값만 있으면 그 리뷰는 무효다. `설정 없음`으로 바꾸지 않는다. `low`·`medium`·`xhigh`·`max`로 돌린 버그 찾기·Security는 무효다. Cursor에 모델 effort 설정이 있는지는 확인하지 않았다(2026-11-04 문서). 리뷰 프롬프트에는 `POLICY.md` §10의 문 유형을 적는다.

각 축은 그 순서에서 이전 작성 모델과 같은 토큰을 건너뛴 뒤의 첫 모델을 쓴다. 버그 찾기·Security에서 그 모델이 강한 모델이다. Standards·Spec도 같은 건너뛰기를 한다. 사용 한도로 막히면 같은 순서의 다음 모델을 쓰고, 근거에 `대체: <막힌 모델> → <쓴 모델>, 이유: 사용 한도`를 적는다. 한도 외의 이유로 순서를 바꾸지 않는다. 건너뛸 때는 `건너뜀: <모델>, 이유: 이전 작성 모델`을 적는다. 건너뛴 뒤 남은 모델이 없거나, 순서의 마지막 모델도 사용 한도로 시작하지 못하면 리뷰를 시작하지 않고 소유자에게 알린다. 반대쪽 모델로 바꾸지 않는다.

| 쪽 | 축 | 순서 |
| --- | --- | --- |
| Claude Code | 버그 찾기, Security | Opus → Sonnet |
| Claude Code | Standards, Spec | Sonnet → Opus |
| Cursor | 버그 찾기, Security | Grok → Gemini → GPT → Composer |
| Cursor | Standards, Spec | Composer → Grok → Gemini → GPT |

이 순서는 2026-11-05에 소유자가 적은 이름이다. 가벼운 모델로 같이 적은 Sonnet과 Composer가 각 쪽 Standards·Spec 순서의 첫 칸이다. 이전 작성 모델과 같으면 그 칸을 건너뛴다. Cursor 버그 찾기·Security는 Grok, Gemini, GPT 순이다. Composer는 이전 작성 모델이 아니고, Grok·Gemini·GPT가 이전 작성 모델로 건너뛰었거나 사용 한도로 막혀 앞에 남은 모델이 없을 때만 쓴다. Composer도 이전 작성 모델이면 건너뛴다. 그때 남은 모델이 없으면 리뷰를 시작하지 않는다. Claude Code 버그 찾기·Security의 강한 모델은 Opus다.

버그 찾기나 Security를 그 축 순서의 첫 모델(이전 작성 모델이라 건너뛴 경우는 그 다음 모델)이 아닌 모델만으로 끝냈으면, 그 축은 병합 가능이 아니다. 막힌 모델의 한도가 풀린 뒤 그 강한 모델과 effort `high`로 같은 head를 다시 돌린다. 그 전에 병합 가능이라고 하지 않는다. 다시 돌린 결과가 그 축의 결과다. 앞의 약한 모델 결과는 근거에 남기되 그 축의 통과로 세지 않는다. 이 다시 돌리기는 `POLICY.md` §5의 두 번째 의견이 아니다. Standards·Spec을 순서의 다음 모델로 대체한 경우는 다시 돌리지 않는다.

돌리지 않는 축은 아래 근거 표에 둔다. 모델 칸은 `해당 없음: <이유>`다. effort 칸은 `해당 없음`이다. P0·P1·P2는 0이다. 빈 칸으로 두지 않는다. 코드 diff가 없으면 버그 찾기의 이유는 `코드 diff 없음`이다. 신뢰 경계 변경이 아니면 Security의 이유는 `신뢰 경계 변경 아님`이다.

리뷰 근거는 PR 본문의 표다. 열은 축, 모델, effort, head SHA, P0, P1, P2다. head SHA는 그 표를 쓸 때의 PR head 전체 SHA다. 모델은 그 축에 실제로 쓴 모델 이름이다. P0·P1·P2는 그 축의 지적 수다. 지적이 없으면 0이다. 리뷰가 시작하지 못한 축은 모델·effort·P0·P1·P2가 `미실행`이다. `미실행`은 0이 아니다. 그 축이 하나라도 있으면 병합 가능이 아니다. 한도 대체와 이전 작성 모델 건너뛰기는 표 아래에 적는다.

P0와 P1은 지적마다 아래 셋 중 하나로 끝낸다. 어느 것도 아닌 P0·P1이 있으면 병합 가능이 아니다. 셋업 프롬프트의 "P0/P1은 해결"은 이 셋을 말한다.

- 수정. 그 지적을 고친 커밋의 전체 SHA를 적는다.
- 기각. 오탐인 이유를 적는다. 파일과 줄, 또는 지적이 인용한 문장을 포함한다.
- 한계로 수용. 수용하는 범위와 근거를 적는다. 저장소 소유자 댓글이 `한계 수용: <현재 head의 전체 SHA>`로 시작하고, 같은 댓글에 축과 그 지적 한 줄이 있어야 한다. 그 댓글이 없으면 수용이 아니다. 에이전트는 이 댓글을 쓰지 않는다.

이 PR 범위 밖의 Pre-existing P0·P1은 셋업 프롬프트 §5대로 후속 Issue로 넘긴다. 그 지적은 위 셋이 없어도 된다. 넘긴 뒤 본문에 Issue 번호를 적는다. Security 지적의 Pre-existing은 그렇게 넘기지 않는다. 수정 또는 기각이 있거나, 소유자가 한계로 수용해야 병합한다.

P2는 이 절에서 병합을 막지 않는다. P2의 처리 방식은 셋업 프롬프트 §5를 따른다.

`review/independent`와 `review/security`를 누가 남기는지는 아래 "리뷰 status를 남기는 사람"을 따른다. 근거 표를 쓴 에이전트는 그 status를 찍지 않는다. status description의 도구·모델·지적 수는 `POLICY.md` §5를 따른다.

PR이 열린 뒤의 루프는 Grok Bot이 맡는다. 사람이 연 세션이 같은 일을 해도 된다. 일정을 이 저장소에 두지 않는다(`POLICY.md` §8). 별도 상시 감시 서비스를 이 저장소에 만들었다고 보고하지 않는다. 주간 점검(`prompts/weekly-check.md`)은 읽기 전용이다. 점검으로 고칠 것이 생기면 코드를 쓰는 쪽이 PR로 반영한다.

맡는 일:

- Dependabot PR을 매주 처리한다(`POLICY.md` §2). 문 유형은 `POLICY.md` §10, 리뷰는 §5를 따른다.
- 외부 리뷰 대상 PR은 CodeRabbit 리뷰가 끝날 때까지 기다린다. 병합 전에 달린 CodeRabbit 스레드는 PR 종류와 관계없이 답하고 해결한다. 병합 뒤에 달린 지적은 후속 PR로 처리한다. CodeRabbit check가 SKIPPED이거나 `Review paused`이면 외부 리뷰는 끝나지 않았고, `@coderabbitai full review`를 요청한다. 예외는, CodeRabbit 리뷰가 끝난 head와 견줘 바뀐 것이 이미 리뷰된 PR들 사이의 충돌을 푼 main 병합뿐인 head다. 소유자는 그 사실을 승인에 적고 외부 리뷰를 다시 받지 않고 승인할 수 있다.
- 1인 프로필에서 `review/independent`와 `review/security`는 아래 "리뷰 status를 남기는 사람"대로 소유자가 남긴 뒤에 `Review status`를 다시 돌린다. 서버 절차 전에는 Mac의 `gh`이고, 그 다음에는 서버의 앱이다. 에이전트는 자기 PR에 그 status를 찍지 않는다. 1인 한쪽 문은 소유자 댓글 뒤에 그 job이 다시 성공하는지 본다. 기준 브랜치 갱신으로 멈춘 PR과, 병합 뒤의 main CI를 확인한다.
- 병합 가능이라고 알리기 전에 근거를 본다. 테스트 결과가 요청한 검사와 맞는지, UI를 바꾼 PR이면 전후 스크린샷이 요청한 화면과 맞는지를 본다. 안 맞으면 병합 가능이라고 하지 않고 그 에이전트에게 돌려보낸다.

## pstack을 함께 쓸 때

[pstack](https://github.com/cursor/plugins/tree/main/pstack)이 설치돼 있으면 Matt Pocock 스킬이 다루지 않는 단계에만 쓴다. pstack 스킬은 사람이 부른다. 에이전트는 아래 경우에 실행을 제안만 한다. 설치되지 않았으면 이 절을 건너뛴다.

pstack이 Cursor 클라우드 에이전트에서 실행되는지는 확인하지 않았다. 아래 런타임은 Claude Code다.

| 단계 | pstack 스킬 | 언제 | 실행 |
| --- | --- | --- | --- |
| 설계 결정 | `interrogate` | `POLICY.md` §10의 한쪽 문을 설계할 때. 외부 리뷰로 세지 않는 추가 의견이다(`POLICY.md` §5) | Claude Code |
| 한쪽 문 PR 전 | `blast-radius` | 한쪽 문 PR을 열기 전, 영향이 diff 밖으로 번질 수 있을 때 | Claude Code |
| 구현과 검증 중 | `create-verification-skill` | 앱을 사용자처럼 실행해 증거를 남기는 방법이 프로젝트에 없을 때. 프로젝트당 한 번 | Claude Code |
| 구현과 검증 중 | `correct` | `retro`로 고른 개선을 `POLICY.md` §6 순서로 막을 때 | Claude Code |

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

리뷰가 보는 것과 남기는 것은 런타임과 상관없이 같다.

- 본다: 그 PR의 diff, 기준 커밋(PR base SHA), `POLICY.md` §5의 언제와 신뢰 경계. 문 유형은 §10만 정한다.
- 남긴다: 지적 목록과 결과(통과 또는 열린 지적). PR 본문의 근거 표 열은 "역할 분담"을 따른다. 그 기록의 status 이름은 `review/independent`이고, Security를 실행했으면 `review/security`다. 누가 그 status를 쓰는지는 아래 "리뷰 status를 남기는 사람"이 정한다. 리뷰를 돌린 에이전트가 통과를 찍는 것이 아니다. status description의 도구·모델·지적 수는 `POLICY.md` §5를 따른다.

런타임 표는 그 기준을 각 런타임에서 어떻게 돌리는지만 적는다. 칸을 확인됨으로 바꾸려면 그 런타임으로 실제 PR을 한 번 돌린 뒤, 확인한 날짜와 그 PR 링크를 이 표 아래에 적는다. 문서로만 읽은 기능은 확인됨이 아니다.

| 런타임 | Standards·Spec | 버그 찾기 | Security |
| --- | --- | --- | --- |
| Claude Code | `/matt-code-review`(`.claude/skills/`) | 내장 `/code-review` | 내장 `/security-review` |
| Codex | `matt-code-review`(`.agents/skills/`) | 미확인 | 미확인 |
| Cursor | `matt-code-review`(`.agents/skills/`) | 미확인 | 미확인 |

Cursor 공식 문서(2026-11-04 읽음, 이 저장소 PR에서 실행하지 않음): 채팅의 모델 선택은 입력창 위 모델 목록이거나 Cmd+/이고, 기본 모델은 Cursor Settings > Models다([Prompting agents](https://cursor.com/docs/agent/prompting)). Cloud Agent 모델은 실행할 때 고르거나, 지정하지 않으면 Cloud Agents 설정의 Default model이다([Cloud Agents](https://cursor.com/docs/cloud-agent), [설정](https://cursor.com/docs/cloud-agent/settings)). PR 리뷰 기능으로 Bugbot이 diff에 댓글을 남기고, 수동 실행은 PR 댓글 `cursor review` 또는 `bugbot run`이다. 에이전트 안에서는 `/review` 또는 `/review-bugbot`이다([Bugbot](https://cursor.com/docs/bugbot)). Automations에는 Bugbot과 Security Agents가 있다([Automations](https://cursor.com/docs/cloud-agent/automations)). 이 기능들로 이 저장소 PR의 버그 찾기·Security를 돌려 본 기록은 없으므로 위 칸은 미확인이다.

모델을 고르는 규칙은 "역할 분담"이다. 위 칸이 미확인이어도 그 규칙을 Claude Code 명령으로 되돌리지 않는다. 칸을 확인됨으로 바꿀 때만 날짜와 PR 링크를 이 표 아래에 적는다.

이미 문서로 정한 한계는 다시 구현하지 않는다. 신뢰 경계의 내용 신호는 검사기가 보지 않고 리뷰어가 판단한다(`POLICY.md` §5). 신뢰하는 작성자를 덜 읽고 승인하는 경로는 없다(§9). hotfix 비율은 병합 조건이 아니다(§8). 사람 시간을 재는 항목은 §8에 없다.

## 리뷰 status를 남기는 사람

1인 프로필에서 `review/independent`와 `review/security`는 Grok Bot이 근거를 확인한 뒤에 소유자가 남긴다. 서버 절차를 마치기 전에는 Mac의 `gh`이고, 마치면 그 서버의 앱이다. 근거는 리뷰 결과, 리뷰한 모델 이름, 그 status를 남길 head SHA다. 팀 프로필에서는 그 PR을 구현하지 않은 사람이 남긴다. 코드를 쓴 에이전트는 자기 PR에 통과를 찍지 않는다. `Review status` workflow는 이 status를 쓰지 않고, 그 head에 있는지만 읽는다(`POLICY.md` §5).

## Mac Studio에서 팀으로 옮길 때

서버가 생기기 전에는 이 절차를 실행하지 않는다. 생기면 아래 순서만 따른다. Linear와 Slack 연동은 나중 일이다.

1. GitHub App을 개인 계정에 등록한다. 권한은 저장소의 Commit statuses 쓰기만 켠다. 다른 권한과 webhook은 켜지 않는다. 직접 등록하는 앱은 Marketplace의 유료 플랜이 아니다([앱 등록](https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/registering-a-github-app), [Commit statuses](https://docs.github.com/en/rest/authentication/permissions-required-for-github-apps)). 이 계정에서 요금을 실제로 청구해 보지는 않았다.
2. 비밀키(private key)는 Mac Studio 서버에만 둔다. Mac의 개발용 `gh` 토큰, Grok Bot의 공유 컴퓨터, 저장소에는 두지 않는다.
3. 키를 바꿀 때: 앱 설정에서 새 키를 만들고 서버에 넣은 뒤, 이전 키를 지운다. 폐기할 때: 서버에서 키 파일을 지우고 GitHub에서 그 키와, 필요하면 앱 설치를 제거한다. 폐기 뒤에는 아래 되돌리기대로 Mac의 `gh`가 다시 status를 남긴다.
4. 옮기는 순서: 앱을 저장소에 설치한다. 시험 커밋은 어떤 PR의 커밋 목록에도 없는, 기본 브랜치 밖의 버린 브랜치 커밋으로 한다. 그 커밋에 `review/independent` success를 남겨 앱 이름으로 보이는지 확인하고, 같은 단계에서 바로 그 SHA에 `failure`를 덮는다. 그 다음에 1인 프로필의 기록 수단만 서버 앱으로 바꾼다. 남기는 주체는 소유자다. Mac의 `gh`로는 더 이상 이 status를 남기지 않는다.
5. 되돌리기: 서버 앱으로 status를 남기는 일을 멈추고, 소유자가 Mac의 `gh`로 다시 남긴다. 앱 설치를 제거해도 이미 남은 status는 지워지지 않는다. 잘못된 status는 그 SHA에 같은 context로 새 상태를 덮어 고친다.
6. 팀 프로필로 바꿀 때 같이 바꾼다. `AGENTS.md`에 `프로필: 팀` 한 줄을 넣는다. `templates/repository-settings.json`을 복사한 값에서 `required_approving_review_count` 1, `require_code_owner_reviews` true, `require_last_push_approval` true로 두고 `templates/CODEOWNERS`로 `.github/CODEOWNERS`를 둔다(`POLICY.md` §9). 이 설정 쓰기는 소유자 승인 뒤에 `tools/apply_github_settings.py`로 한다.
