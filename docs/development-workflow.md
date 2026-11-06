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

이 기준이 스킬에 더하는 것은 `main`에 들어가는 경계, `POLICY.md` §5의 리뷰 도구, 아래 "역할 분담"의 누가·어디서·어느 모델, 그 아래 절의 pstack 배치다.

- 모든 변경은 PR로 `main`에 들어가고 필수 CI가 통과해야 한다. 문 유형은 `POLICY.md` §10만 따른다. `review/gate`가 필수로 적용된 저장소에서는 Dependabot 버전 전용 PR을 뺀 모든 PR(되돌리기 쉬움 포함)에 `review/independent`가 필요하다. 1인 프로필에서 status는 소유자만 올린다는 규칙이다. 에이전트가 status를 올리는 것은 금지지만 GitHub가 기술적으로 막지는 않는다. 1인 프로필에서 검사기는 `creator.login`이 저장소 소유자이거나 `STATUS_ACTORS`(지금은 비어 있음)인 status만 success로 센다(#34). 적용 전인 프로젝트의 되돌리기 쉬움(two-way door: 되돌리기 쉬운 결정)은 필수 CI·리뷰 뒤 맡은 에이전트가 병합할 수 있다. 되돌리기 어려움(one-way door: 되돌리기 어려운 결정)은 사람이 최종 head를 승인한다(셋업 프롬프트 §10은 그 판정의 병합 절차다). 1인 프로필의 게이트 경로 PR은 소유자 댓글이 `되돌리기 어려움 승인: <head sha>` 또는 deprecated인 `한쪽 문 승인: <head sha>`로 시작하고, 그 SHA가 현재 head와 같아야 한다. 편집한 댓글은 무효다. `updated_at`이 `created_at`과 같고 `lastEditedAt`이 null이어야 한다. 같은 초 편집도 무효라 새 댓글을 단다. `Review status` job이 그 댓글을 검사한다. 그 job은 필수 체크가 아니다. 병합은 그 댓글과 그 head의 전용 앱 `review/gate` success가 있어야 한다(`POLICY.md` §5·§10, `docs/review-gate-app.md`). 팀 프로필은 모든 PR에 다른 팀원의 GitHub 승인이 필요하다(`POLICY.md` §9).
- 리뷰·수정은 셋업 프롬프트 §5와 `POLICY.md` §5를 따른다. Security 리뷰와 외부 리뷰(공개 저장소는 CodeRabbit)를 더할 변경도 거기서 정한다. Standards·Spec의 독립 리뷰 이름은 `/matt-code-review` 하나다. `/implement` 안의 리뷰는 `review/independent`로 세지 않는다.
- 에이전트 환경 개선은 사용자가 `/retro`를 실행할 때 한다(`POLICY.md` §6). 에이전트는 실행을 요청만 한다.

## 역할 분담

누가 코드를 쓰는지, 어느 머신에서 쓰는지, 어느 모델로 리뷰하는지를 정한다. PR 안의 작성 절차는 Matt Pocock 스킬이 맡는다. 이 절은 그 절차를 약하게 하지 않는다. 시작은 사용자가 `/ask-matt`를 실행하는 것이다. 이어서 `/grill-with-docs`, `/to-spec`, `/to-tickets`, `/implement`다. Standards·Spec의 독립 리뷰 호출은 `/matt-code-review`다. pstack은 그 스킬이 비우는 칸만 쓴다. 칸은 `interrogate`, `blast-radius`, `create-verification-skill`, `correct`다. 배치는 아래 "pstack을 함께 쓸 때"다.

- Grok Bot은 접수, Issue, 작업 분해, 배정, CI와 리뷰 추적, 근거 확인, 보고를 맡는다. 코드를 쓰지 않는다. 작성 도구가 아니다. Grok Bot이 PR을 열어도 `작성 도구`와 `작성 모델`은 코드를 쓴 쪽이다.
- 코드는 Claude Code와 Cursor가 쓴다. 둘 다 작성 도구다.
- 리뷰 모델의 패밀리는 작성 모델의 패밀리와 달라야 한다. 항상 그렇다. 플랫폼은 보지 않는다. Cursor 안의 Claude도 Claude다. 최종 작성 모델 또는 이전 작성 모델과 패밀리가 같으면 그 리뷰는 무효다.

머신은 Claude Code와 Cursor 둘 다 클라우드가 기본이다. 같은 모델의 사용량은 로컬과 클라우드가 같다. 머신은 그 작업에 필요한 능력으로 고른다. 비용으로 고르지 않는다.

- Claude Code 클라우드의 진입은 `claude --cloud` 또는 claude.ai/code다. 작성 도구 값은 `Claude Code`다.
- Cursor 클라우드 에이전트의 작성 도구 값은 `Cursor 클라우드 에이전트`다.
- Mac은 다음 중 하나라도 필요할 때만 쓴다. iOS 시뮬레이터 또는 Xcode. 실기기. Keychain. 장기 비밀. 장기 비밀은 `gh`, review-gate pem, Claude 로그인이다.
- 장기 비밀은 Mac에만 둔다. Cursor의 AWS VM, Claude의 Anthropic VM, Grok Bot이 쓰는 공유 컴퓨터에 두지 않는다.
- 넘기기는 양방향이다. 클라우드 작업이 시뮬레이터·실기기·Keychain·장기 비밀에서 막히면 남은 작업을 Mac으로 넘긴다. 비밀을 클라우드에 커밋하지 않고, 막힌 단계를 빼지 않는다. Mac 작업을 병렬이나 백그라운드로 옮길 때는 클라우드로 넘긴다.
- 소유자가 그 자리에서 고치겠다면 Mac의 Cursor IDE도 작성 경로다. 작성 도구 값은 `Cursor`다. `Cursor`와 `Cursor 클라우드 에이전트`는 다른 경로다.

구독은 2026-11-06에 소유자가 정한 둘이다. Claude Code Pro. X 구독 $30으로 쓰는 Cursor와 Grok Bot. Cursor 선불 크레딧은 쓰지 않는다. 그 크레딧으로만 고르는 Cursor 호스트 Claude, GPT, Codex, Gemini는 작성과 리뷰의 활성 로스터가 아니다. GPT는 Cursor 안에서 선불 크레딧으로만 고를 수 있다. 이 소유자는 그 크레딧을 쓰지 않으므로 GPT는 활성 로스터가 아니다. Codex 클라우드, ChatGPT, `codex` CLI로도 PR을 쓰거나 리뷰하지 않는다. 아래 런타임 표의 Codex 행은 그 런타임을 썼을 때의 기록이다. 배정과 리뷰의 대상이 아니다. 플랫폼은 패밀리를 바꾸지 않는다. Cursor 호스트 Claude를 쓰면 패밀리는 Claude다. 그 모델은 이 소유자의 활성 로스터에 없다.

활성 작성 모델은 아래다. Haiku는 리뷰에 쓰지 않는다.

| 모델 | 패밀리 | 맡는 일 |
| --- | --- | --- |
| Haiku | Claude | 트리아지, 초안, 작은 문서 |
| Sonnet | Claude | 일상 구현. 작성 패밀리가 Claude가 아닐 때, 되돌리기 어려움의 수정 라운드 뒤 델타 재리뷰 |
| Opus | Claude | 어려운 설계·구현. 작성 패밀리가 Claude가 아닐 때, 되돌리기 어려움의 첫 버그 찾기·Security |
| Grok | Grok | Cursor 주간 풀의 무거운 구현. Composer가 부족한 되돌리기 어려움의 다음 라운드 |
| Composer | Composer | Cursor 주간 풀의 작은 수정, 테스트, 문서. 작성 패밀리가 Claude일 때의 Standards·Spec |

effort는 각 모델의 제품 기본값만 쓴다. 설정에서 effort를 고정하지 않는다. 근거에 적는 허용 값은 `low`, `medium`, `high`, `xhigh`, `max`, `설정 없음`이다. 제품에 effort 설정이 없으면 `설정 없음`이다. 이 값은 리뷰 모델의 effort다. Bugbot 설정의 Low·Default·High·Smart와 같지 않고, 그 대응은 이 문서에 없다. Bugbot을 버그 찾기 도구로 쓰는지는 아래 런타임 표가 미확인인 동안 정하지 않는다. Cursor에 모델 effort 설정이 있는지는 확인하지 않았다(2026-11-04 문서).

PR을 쓰는 곳은 아래 순서로 정한다. Grok Bot이 작업을 이슈 하나로 나눈 뒤에 보낸다. 에이전트 하나는 이슈 하나만 맡는다. 이슈가 여럿이면 병렬로 보낸다.

1. 시뮬레이터, Xcode, 실기기, Keychain, 장기 비밀 중 하나라도 필요하면 Mac이다. 작성 도구는 Claude Code 또는 Cursor IDE다.
2. 1이 아니면 클라우드가 기본이다. Claude Code 클라우드 또는 Cursor 클라우드 에이전트다. 맞는 작성 패밀리와 남은 한도를 보고 고른다. 둘 다 유효하다. 비밀이 없고 1의 조건인지도 아직 모르면 두 클라우드 중 어느 쪽에서 시작해도 된다. 그 이유로 Cursor 클라우드 에이전트만 고르거나, 작성 모델을 Grok으로 고정하지 않는다.
3. 클라우드 작업이 1에서 막히면 더 커밋하지 않는다. 비밀을 클라우드에 넣지 않고 남은 작업을 Mac으로 넘긴다. 이미 커밋한 도구와 모델은 `이전 작성 도구`와 `이전 작성 모델`에 적는다.
4. 1이 아닌 이유로 막히면 더 커밋하지 않고 그 이유를 소유자에게 알린다.

PR 본문에 `작성 도구`와 `작성 모델`이 없으면 리뷰를 시작하지 않는다.

- `작성 도구:` `Claude Code`, `Cursor`, `Cursor 클라우드 에이전트`, `사람` 중 하나. `Cursor`는 Mac의 Cursor IDE다. `Cursor 클라우드 에이전트`는 클라우드다. `Claude Code`는 Mac과 클라우드가 같은 값이다.
- `작성 모델:` 도구가 보여주는 모델 이름. `사람`이면 `없음`. Haiku를 적을 때 이름에 `claude`가 있어야 아래 인식 표가 Claude로 센다. `haiku`만 있는 이름은 그 표에 없다.
- `머신:` `Mac` 또는 `클라우드`. `사람`이면 `해당 없음`. 검사기는 이 줄을 읽지 않는다. Claude Code가 Mac인지 클라우드인지는 이 줄로 확인한다.
- 마지막으로 커밋한 도구와 모델이 최종 작성이다. 그 전에 커밋한 모델이 있으면 도구가 같아도 `이전 작성 모델`에 이름을 모두 적는다. 빠지면 검사기는 그 모델을 작성 패밀리로 보지 않아, 그 모델이 독립 리뷰를 할 수 있다. 도구가 바뀌었으면 `이전 작성 도구`도 적는다. 검사기는 `이전 작성 도구`를 읽지 않는다. 사람이 이전에 커밋했으면 `이전 작성 도구`는 `사람`이다. `이전 작성 모델`에는 그 사람을 적지 않고 `없음`도 넣지 않는다. `없음`은 패밀리가 없어 근거 검사가 거절한다. 클라우드에서 Mac으로 넘긴 경우와 Mac에서 클라우드로 넘긴 경우가 둘 다 해당한다.

패밀리는 대소문자를 무시하고 이름에서 고른다. `chatgpt` 또는 `codex`가 있으면 리뷰 모델이 아니다. 그 다음 아래 단어가 가리키는 패밀리를 모은다. 패밀리가 하나면 그 패밀리다. 없거나 둘 이상이면 무효다. 이 표는 인식 이름이다. CI 별칭과 같다. 이 변경은 그 검사 코드를 바꾸지 않는다.

| 이름에 있는 단어 | 패밀리 |
| --- | --- |
| `opus`, `sonnet`, `claude` | Claude |
| `grok` | Grok |
| `composer` | Composer |
| `gemini` | Gemini |
| `gpt` | GPT |

`opus`와 `sonnet`은 한 패밀리다. Haiku는 이름에 `claude`가 있으면 Claude다. `grok-4.7`과 `cursor-grok-4.6`은 Grok이다. `claude-opus`는 Claude다. 표에 없는 패밀리를 쓰려면 이 표를 먼저 고친다. Gemini 행과 GPT 행은 인식 이름이다. 활성 리뷰 후보가 아니다. 이 소유자의 활성 리뷰 패밀리는 Composer, Grok, Claude뿐이다. 작성 패밀리의 반대쪽을 고른다. 작성 패밀리가 Claude이면 Composer다. 작성 패밀리가 Grok 또는 Composer이면 Claude다. Gemini나 GPT를 기본 리뷰 후보로 두지 않는다. 작성 기본을 Grok으로, 리뷰 기본을 Claude로 두지 않는다. 필수 조건은 패밀리가 다른 것이다.

문 유형은 `POLICY.md` §10이다. 이 절은 그 문 유형을 바꾸지 않는다. 리뷰 프롬프트에 그 문 유형을 적는다. Standards·Spec의 호출은 아래 런타임 표 그대로 `/matt-code-review`다.

- 되돌리기 쉬움: Standards, Spec, 버그 찾기를 작성 패밀리와 다른 모델 하나로 하면 된다. 세 축의 모델이 같아도 된다. Security는 신뢰 경계를 건드릴 때, 또는 사람이 Security를 더 요청할 때 한다(`POLICY.md` §5). 그 요청은 첫 패스 뒤에도 같다. 그 모델의 패밀리는 작성 패밀리와 다르다. 그 하나의 모델은 활성 로스터에서 최종 작성 모델과 `이전 작성 모델`의 패밀리를 뺀 반대쪽이다. 그 패밀리가 Claude뿐이면 Composer다. 그 기록에 Composer가 있으면 Grok이다. 그 합이 Claude와 Grok이면 Composer다. 그 패밀리가 Grok 또는 Composer뿐이면 Sonnet이다. 활성 로스터에 그 합 밖의 패밀리가 없으면 그 축은 `미실행`이고 병합을 기다린다. Haiku로 그 셋을 보지 않는다.
- 되돌리기 어려움은 `POLICY.md` §10이 정한다. 거기에는 CI, 게이트, 보안 경계가 들어 있다. 돈·migration·권한처럼 §10이 되돌리기 어려움이라고 한 다른 변경도 되돌리기 어려움이다. 버그 찾기와 Security에 패밀리 둘을 요구하지 않는다. Opus와 Gemini를 한 쌍으로 요구하지 않는다.

이 소유자의 활성 순서는 Opus, Sonnet, Composer, Grok이다. Gemini와 GPT는 이 순서에 없다. 최종 작성 모델과 `이전 작성 모델`의 패밀리를 모두 뺀다. 아래의 작성 패밀리는 그 합이다. 검사기도 그 패밀리를 작성으로 본다. 되돌리기 어려움의 첫 버그 찾기는 그 순서에서 지금 쓸 수 있는 첫 모델이다. Opus를 쓸 수 있으면 Sonnet은 그 첫 모델이 아니다. 작성 패밀리가 Grok이거나 Composer이면 그 첫 모델은 Opus(Claude Code)다. 그 패스는 버그 찾기를 본다. 신뢰 경계를 건드리면 같은 패스가 Security도 본다. 건드리지 않고 사람의 요청도 없으면 Security는 `해당 없음: 신뢰 경계 변경 아님`이고, 그 패스가 Security를 열지 않는다. 사람이 요청하면 그 패스 또는 그 다음 패스가 그 축을 연다. Standards·Spec도 그 Opus의 `/matt-code-review`다. 작성 패밀리가 Claude뿐이면 Opus와 Sonnet은 리뷰가 아니다. 그 첫 모델은 Composer다. 그 합에 Composer가 있으면 Composer는 건너뛰고 첫 모델은 Grok이다. 그 합이 Claude와 Grok이면 첫 모델은 Composer다.

수정 라운드 뒤의 델타 재리뷰는 한 번이다. 그 한 번은 버그 찾기를 본다. 델타 전에 고친 뒤의 diff로 신뢰 경계를 다시 본다. 첫 패스가 Security를 실행했거나 사람이 그 축을 요청했으면 그 축도 같은 한 번에 본다. 수정이 외부 입력이나 권한 변경을 더하면, 첫 패스가 `해당 없음`이었고 사람의 요청이 없어도 Security를 그 한 번에 넣는다(`POLICY.md` §5). 검사기는 그 내용 기준을 보지 않는다. 고친 diff가 신뢰 경계를 더하지 않고 Security가 `해당 없음`이며 사람의 요청도 없으면 델타도 그 축을 열지 않는다. 델타 모델의 패밀리가 작성 패밀리에 있으면 그 모델은 건너뛴다. 첫 모델이 Opus이면 델타는 Sonnet이다. Opus가 한도라 첫 모델이 Sonnet이면 델타는 활성 순서에서 그 다음이며 작성 패밀리와 다른 모델이다. 작성 패밀리가 Grok이면 Composer이고, 작성 패밀리가 Composer이면 Grok이다. 첫 모델이 Composer이면 같은 모델을 다시 쓰지 않는다. 델타는 Grok 한 번이고, 근거에 `보강: Composer → Grok, 이유: 되돌리기 어려움`을 적는다. Grok도 작성 패밀리면 그 델타는 없고 병합을 기다린다. 그 Grok 다음에 다른 델타를 요구하지 않는다.

지정 모델이 사용 한도면 활성 순서의 다음 모델 가운데 작성 패밀리와 다른 것을 쓴다. Opus가 한도면 작성 패밀리가 Claude가 아닐 때의 다음은 Sonnet이다. Opus와 Sonnet이 둘 다 한도면 작성 패밀리가 Grok일 때 Composer, 작성 패밀리가 Composer일 때 Grok이다. 작성 패밀리가 Claude이고 Composer가 한도면 Grok이다. 근거에 `대체: <막힌 모델> → <쓴 모델>, 이유: 사용 한도`를 적는다. 다른 패밀리를 우선한다. 작성 패밀리와 리뷰 패밀리는 다르다. 한도로 다른 패밀리가 없으면 먼저 병합을 기다린다. 같은 패밀리의 다른 모델은 마지막 수단이고, 기다릴 수 있으면 그 리뷰보다 기다린다. 그 마지막 수단은 Opus와 Sonnet뿐이다. 작성 패밀리가 Claude가 아니면 Opus와 Sonnet은 다른 패밀리 리뷰다. 같은 모델이 그 축을 다시 보는 것은 금지다. 예: 작성 패밀리가 Composer이고 첫 모델이 Opus이며 Sonnet과 Grok이 한도면 Opus를 다시 쓰지 않는다. Sonnet이나 Grok이 풀릴 때까지 기다린다. 작성 패밀리가 Claude이고 Composer와 Grok이 둘 다 한도면 그 축은 `미실행`이고 병합을 기다린다. 그때만, 작성에 쓰지 않았고 그 축을 아직 보지 않은 Opus 또는 Sonnet을 마지막 수단으로 고를 수 있다. 근거에 `대체: <막힌 모델> → <쓴 모델>, 이유: 사용 한도, 마지막 수단`을 적는다. 검사기는 작성 패밀리와 같은 리뷰를 거절한다. 이 변경은 그 검사를 바꾸지 않는다. 그래서 그 마지막 수단은 병합을 열지 못한다. 다른 패밀리가 남아 있으면 기다리는 동안 그 축을 `미실행`으로 적지 않는다. 리뷰가 없으면 병합은 그 리뷰를 기다린다. 다른 패밀리로 대체했으면 한도 때문에 병합을 멈추지 않는다. Gemini와 GPT로 그 빈자리를 채우지 않는다. 되돌리기 어려움에서 더 강한 모델로 다시 보는 일은 후속 Issue에 적는다. 그 재리뷰를 할지는 소유자가 정한다. 실행한 리뷰의 근거가 있으면 그 Issue가 없어도 병합을 막지 않는다.

돌리지 않는 축은 근거 표에 둔다. 모델 칸은 `해당 없음: <이유>`다. effort 칸은 `해당 없음`이다. P0·P1·P2는 0이다. 빈 칸으로 두지 않는다. 신뢰 경계를 건드리지 않고 사람의 Security 요청도 없으면 Security의 이유는 `신뢰 경계 변경 아님`이다. 리뷰가 시작하지 못한 축은 모델·effort·P0·P1·P2가 `미실행`이다. `미실행`은 0이 아니다. 한도로 다른 패밀리를 쓴 축은 `미실행`이 아니다.

리뷰 근거는 PR 본문의 표다. 열은 축, 모델, effort, head SHA, P0, P1, P2다. head SHA는 그 표를 쓸 때의 PR head 전체 SHA다. 모델은 그 축에 실제로 쓴 모델 이름이다. P0·P1·P2는 그 축의 지적 수다. 지적이 없으면 0이다. 한도 대체는 표 아래에 적는다.

검사의 나눔은 이렇다. CI는 리뷰 패밀리와 작성 패밀리가 같으면 실패한다. 그 검사는 #25가 넣는다. 이 변경은 그 검사 코드를 바꾸지 않는다. 관리자(Grok Bot)는 모델 이름이 실제로 돌린 모델과 같은지, P0·P1·P2 수가 지적 목록과 같은지, P1 기각 이유가 그 지적과 맞는지를 본다. CI는 그 사실 여부를 보지 않는다.

P0와 P1은 지적마다 아래 셋 중 하나로 끝낸다. 어느 것도 아닌 P0·P1이 있으면 병합 가능이 아니다. 셋업 프롬프트의 "P0/P1은 해결"은 이 셋을 말한다.

- 수정. 그 지적을 고친 커밋의 전체 SHA를 적는다.
- 기각. 오탐인 이유를 적는다. 파일과 줄, 또는 지적이 인용한 문장을 포함한다.
- 한계로 수용. 수용하는 범위와 근거를 적는다. 저장소 소유자 댓글이 `한계 수용: <현재 head의 전체 SHA>`로 시작하고, 같은 댓글에 축과 그 지적 한 줄이 있어야 한다. 그 댓글이 없으면 수용이 아니다. 에이전트는 이 댓글을 쓰지 않는다.

이 PR 범위 밖의 Pre-existing P0·P1은 셋업 프롬프트 §5대로 후속 Issue로 넘긴다. 그 지적은 위 셋이 없어도 된다. 넘긴 뒤 본문에 Issue 번호를 적는다. Security 지적의 Pre-existing은 그렇게 넘기지 않는다. 수정 또는 기각이 있거나, 소유자가 한계로 수용해야 병합한다.

P2는 이 절에서 병합을 막지 않는다. P2의 처리 방식은 셋업 프롬프트 §5를 따른다.

`review/independent`와 `review/security`를 누가 남기는지는 아래 "리뷰 status를 남기는 사람"을 따른다. 근거 표를 쓴 에이전트는 그 status를 찍지 않는다. status description의 도구·모델·지적 수는 `POLICY.md` §5를 따른다.

PR이 열린 뒤의 루프는 Grok Bot이 맡는다. 사람이 연 세션이 같은 일을 해도 된다. 일정을 이 저장소에 두지 않는다(`POLICY.md` §8). 별도 상시 감시 서비스를 이 저장소에 만들었다고 보고하지 않는다. 주간 점검(`prompts/weekly-check.md`)은 읽기 전용이다. 점검으로 고칠 것이 생기면 코드를 쓰는 쪽이 PR로 반영한다.

맡는 일:

- 관리자(Grok Bot)는 근거 표의 모델 이름, P0·P1·P2 수, P1 기각 이유가 사실인지를 본다. CI는 패밀리가 같은지만 실패시킨다(#25).
- Dependabot PR을 매주 처리한다(`POLICY.md` §2). 문 유형은 `POLICY.md` §10, 리뷰는 §5를 따른다.
- 외부 리뷰 대상 PR은 CodeRabbit 리뷰가 끝날 때까지 기다린다. 병합 전에 달린 CodeRabbit 스레드는 PR 종류와 관계없이 답하고 해결한다. 병합 뒤에 달린 지적은 후속 PR로 처리한다. CodeRabbit check가 SKIPPED이거나 `Review paused`이면 외부 리뷰는 끝나지 않았고, `@coderabbitai full review`를 요청한다. 예외는, CodeRabbit 리뷰가 끝난 head와 견줘 바뀐 것이 이미 리뷰된 PR들 사이의 충돌을 푼 main 병합뿐인 head다. 소유자는 그 사실을 승인에 적고 외부 리뷰를 다시 받지 않고 승인할 수 있다.
- 1인 프로필에서 `review/independent`와 `review/security`는 아래 "리뷰 status를 남기는 사람"대로 소유자가 남긴 뒤에 `Review status`를 다시 돌린다. 수단은 Mac의 `gh`다. 서버의 앱은 `review/gate`만 올린다. 에이전트는 자기 PR에 그 status를 찍지 않는다. 1인 되돌리기 어려움은 소유자 댓글 뒤에 그 job이 다시 성공하는지 본다. 편집한 댓글은 무효다. 같은 초에 고쳐 `updated_at`이 같아도 `lastEditedAt`이 있으면 무효라 새 댓글을 단다. 기준 브랜치 갱신으로 멈춘 PR과, 병합 뒤의 main CI를 확인한다.
- 병합 가능이라고 알리기 전에 근거를 본다. 테스트 결과가 요청한 검사와 맞는지, UI를 바꾼 PR이면 전후 스크린샷이 요청한 화면과 맞는지를 본다. 안 맞으면 병합 가능이라고 하지 않고 그 에이전트에게 돌려보낸다.

## pstack을 함께 쓸 때

[pstack](https://github.com/cursor/plugins/tree/main/pstack)이 설치돼 있으면 Matt Pocock 스킬이 다루지 않는 단계에만 쓴다. pstack 스킬은 사람이 부른다. 에이전트는 아래 경우에 실행을 제안만 한다. 설치되지 않았으면 이 절을 건너뛴다.

pstack이 Cursor 클라우드 에이전트에서 실행되는지는 확인하지 않았다. 아래 런타임은 Claude Code다.

| 단계 | pstack 스킬 | 언제 | 실행 |
| --- | --- | --- | --- |
| 설계 결정 | `interrogate` | `POLICY.md` §10의 되돌리기 어려움을 설계할 때. 외부 리뷰로 세지 않는 추가 의견이다(`POLICY.md` §5) | Claude Code |
| 되돌리기 어려움 PR 전 | `blast-radius` | 되돌리기 어려움 PR을 열기 전, 영향이 diff 밖으로 번질 수 있을 때 | Claude Code |
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

1인 프로필에서 `review/independent`와 `review/security`는 Grok Bot이 근거를 확인한 뒤에 소유자가 남긴다. 수단은 Mac의 `gh`다. 서버의 앱은 `review/gate`만 올리고 이 status는 올리지 않는다. 근거는 리뷰 결과, 리뷰한 모델 이름, 그 status를 남길 head SHA다. 팀 프로필에서는 그 PR을 구현하지 않은 사람이 남긴다. 코드를 쓴 에이전트는 자기 PR에 통과를 찍지 않는다. `Review status` workflow는 이 status를 쓰지 않고, 그 head에 있는지만 읽는다(`POLICY.md` §5). 이 저장소의 `.github/repository-settings.json`은 `Review status`를 필수 체크로 두지 않는다. 필수 체크는 Baseline checks 둘과 `review/gate`(`app_id` 5641238)다. 이 파일의 PR은 branch protection을 쓰지 않는다. 병합 뒤 소유자가 Mac에서 적용한다. 적용되면 Dependabot 버전 전용 PR을 뺀 모든 PR(되돌리기 쉬움 포함)이 그 status 없이 병합되지 않는다. status는 소유자만 올린다는 규칙이다. 에이전트가 status를 올리는 것은 금지지만 GitHub가 기술적으로 막지는 않는다. smallnext, BGLike, mobile-runtime은 repo-baseline에 보호 규칙을 적용하고, 카나리 시험(같은 이름 체크 위장, 이전 실패 run이 남은 head의 병합 가능 여부, Dependabot 예외)을 통과하고, status 작성자·편집된 승인 댓글 검사기 수정이 병합·재적용된 뒤에 카나리 결과는 Issue #32 댓글 하나에 적는다. 그 기록이 없으면 멈춘다. 이 PR은 그 세 저장소의 `.github/repository-settings.json`을 바꾸지 않는다. `Review status`를 필수로 넣지 않는다. 그 세 저장소의 `Review status` workflow는 그대로 둔다. 검사기는 `creator.login`이 저장소 소유자이거나 `scripts/check_review_status.py`의 `STATUS_ACTORS`에 있을 때만 그 status를 success로 센다. `STATUS_ACTORS`는 이 저장소에서만 바꾼 뒤 다시 복사한다. 소비 프로젝트의 복사본을 직접 고치지 않는다. 지금은 비어 있다. 다른 작성자의 status는 실패다. 다른 SHA의 success도 이 head의 근거가 아니다. 팀 프로필은 작성자를 보지 않는다. 1인 프로필의 승인 댓글은 편집하면 무효다. `lastEditedAt`이 null이 아니면 새 댓글을 단다. 그 다음 단계가 `review/gate`다. 권장: **게이트 전용 읽기 `GH_TOKEN` + Keychain에서 꺼낸 PEM + `origin/main`의 깨끗한 checkout**에서 `tools/post_review_gate.py`를 실행한다(상세는 `docs/review-gate-app.md`). 예전 **봉인 사본·reviewgate 전용 계정**은 레거시다. 먼저 `--dry-run`이다. 이 명령만 commit status `review/gate`를 올린다. 같은 UID에서 에이전트가 돌면 임시 PEM이 있는 순간 키가 노출될 수 있다. 저장소와 Actions에 두지 않는다. 에이전트는 이 명령을 실행하지 않는다. `Review status` 체크가 초록이어도 그 결론을 게이트의 근거로 쓰지 않는다.

## Mac Studio에서 팀으로 옮길 때

서버가 생기기 전에는 키를 소유자의 Mac에만 둔다. 앱 등록, 설치 저장소, 0600 경로, 키 교체와 폐기, 서버로 옮기는 순서는 `docs/review-gate-app.md`다. 그 앱은 `review/gate`만 올린다. `review/independent`와 `review/security`는 사람 계정의 `gh`로 남긴다. `STATUS_ACTORS`에 앱 로그인을 넣지 않는다. 팀 프로필의 승인 수와 CODEOWNERS는 `POLICY.md` §9이고, 키를 옮기는 작업과 한 PR에 섞지 않는다.
