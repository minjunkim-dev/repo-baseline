# 변경 기록

## 2026-11-05 — 리뷰는 패밀리가 다르면 된다

- `docs/development-workflow.md` 역할 분담: 필수 조건은 리뷰 패밀리가 작성 패밀리와 다른 것이다. 플랫폼은 보지 않는다. Claude는 Opus와 Sonnet을 한 패밀리로 두고, Cursor 안의 Claude도 Claude다. Grok이 쓴 PR은 Composer, Gemini, Claude, GPT가 볼 수 있다. Claude가 쓴 PR은 Grok, Composer, Gemini, GPT가 볼 수 있다.
- 양쪽 문은 Standards·Spec·버그 찾기를 다른 패밀리 모델 하나로 한다. Security는 신뢰 경계만. 한쪽 문(CI, 게이트, 보안 경계)의 버그 찾기·Security는 지금 쓸 수 있는 가장 강한 다른 패밀리다. 가능하면 패밀리 둘이다. 작성 패밀리가 Grok일 때의 예는 Opus와 Gemini다.
- 가장 강한 모델이 한도면 다음 다른 패밀리를 쓰고 근거에 적는다. 병합을 그 한도로 멈추지 않는다. 한쪽 문의 더 강한 모델 재리뷰는 후속 Issue이고, 할지는 소유자가 정한다.
- 작성 기본은 Grok(Cursor 클라우드 에이전트)이고 리뷰 기본은 Claude다. Claude Code로 직접 만든 PR의 기본 리뷰는 Cursor 모델이다.
- CI는 패밀리가 같으면 실패한다. 그 검사는 #25가 넣는다. 관리자(Grok Bot)는 모델 이름, 지적 수, P1 기각 이유가 사실인지를 본다.
- `POLICY.md` §5·§10과 셋업 프롬프트 §5의 모델 문장은 이 규칙을 가리킨다. Claude 리뷰를 필수로 두던 문장은 뺐다. 게이트 파일과 CI workflow는 안 바꿨다.

## 2026-11-05 — PR 본문 양식

- `.github/pull_request_template.md`: Summary, Evidence, Merge Danger, `Author: <tool> / <model>`, 리뷰 근거 표를 둔다. 축은 Standards, Spec, 버그 찾기, Security다. tool은 Claude Code, Cursor, Cursor 클라우드 에이전트, 사람이다. `작성 도구`와 `작성 모델` 두 줄도 같은 기록이다. 검사기는 아직 이 양식을 강제하지 않는다.
- `templates/repo-baseline.json`이 그 파일을 `.github/pull_request_template.md`로 복사한다.
- 다시 적용할 프로젝트: Smallnext·BGLike·Runstir. `tools/apply_baseline.py`로 양식을 복사한다.

## 2026-11-05 — 작성 도구와 리뷰 모델

- `docs/development-workflow.md` 역할 분담: 구독은 Claude Code와 X 구독(Cursor, Grok Bot)뿐이다. 별도의 GPT·Codex 구독은 없다. Cursor 안의 GPT는 쓸 수 있다. PR을 쓰는 도구는 로컬·비밀·대화로 따라가는 작업이면 Claude Code(Mac)이고, 이슈 하나로 클라우드에서 끝까지 검사되면 Cursor 클라우드 에이전트다. 애매하면 Cursor 클라우드 에이전트이고, 로컬·비밀에서 막히면 Claude Code로 넘긴다. PR 본문에 작성 도구와 작성 모델을 적는다.
- 리뷰 모델은 작성 모델의 반대쪽이다. Claude Code가 쓰면 Cursor 모델(Grok, Gemini, GPT, Composer)이 리뷰한다. Cursor 모델이 쓰면 Claude Code 모델(Opus, Sonnet)이 리뷰한다. 버그 찾기·Security는 그 쪽의 강한 모델과 effort `high`(Claude Code 쪽은 Opus)다. Standards·Spec은 가벼운 모델(Sonnet, Composer)로 충분하다. 사용 한도로 막히면 같은 쪽의 다음 모델로 대체하고 근거에 적는다. 버그 찾기·Security를 약한 모델만으로 끝냈으면 한도가 풀린 뒤 강한 모델로 다시 돌리기 전에는 병합 가능이 아니다.
- 근거 표의 열은 축, 모델, effort, head SHA, P0, P1, P2다. P0·P1은 수정, 기각, 또는 소유자가 한계로 수용한다.
- `POLICY.md` §5·§10과 셋업 프롬프트 §5: 모델·effort·근거 표·P0·P1 처리는 위 절을 따른다. 예전의 양쪽 문 `low`·한쪽 문 `high` 깊이 문장은 뺐다. 게이트 파일과 CI workflow는 안 바꿨다. 소비 프로젝트 재적용은 필요 없다.

## 2026-11-05 — 이벤트 정책 glob과 승인 댓글 재실행

- README의 이벤트 정책 판별은 `workflow_path` glob을 본다. `*`는 `/`를 넘지 않고 `**`는 넘는다. 그 파일에 맞는 glob이 `pull_request_target`만 허용하면 설치를 멈추고 POST하지 않는다. 패턴을 판별할 수 없어도 POST하지 않는다.
- `templates/review-status.yml`: 소유자 승인 댓글이 생기거나, 수정되거나, 삭제되면 그 head의 `pull_request_target` 실행을 `head_sha`로 찾는다. 목록의 `pull_requests`는 비어 있을 수 있어 그 배열의 head만 보면 이전 실행을 고를 수 있다. 최근 50개로 끊지 않고 페이지당 100개, 최대 20페이지까지 찾는다. 실행을 끝까지 찾지 못하면 그 head에 실패하는 `Review status` 체크를 남겨 이전 성공이 최신 결과가 아니게 한다. `review/independent`와 `review/security`는 쓰지 않는다. 재실행 job은 기본 브랜치만 checkout하고 댓글 본문을 읽지 않는다. 권한에 `checks: write`가 더해진다.
- `scripts/check_review_status.py`: `review/independent`와 `review/security`는 열린 PR의 현재 파일·커밋 목록이 아니라 그 head의 `compare`로 정한다. 이전 head는 커밋 시각과 force-push 시각으로 정렬해, 더 최근 failure를 건너뛰고 이전 success를 잇지 않는다. 같은 head의 status 목록은 가장 최근 상태가 앞선다. `uses:` 줄의 주 버전은 `# vN`·`@vN`만 보고, 해시 안의 숫자는 주 버전이 아니다. 버전 표식이 없는 pin은 주 버전을 모르는 것으로 본다.
- 댓글 재실행은 run의 `head_sha`만 고른다. `pull_requests[].head.sha`는 현재 head로 바뀔 수 있어 이전 실행을 다시 돌리지 않는다.
- 다시 적용할 프로젝트: Smallnext·BGLike·Runstir. workflow 템플릿을 `.github/workflows/review-status.yml`로 다시 복사한다. `scripts/check_review_status.py`, `scripts/test_review_status.py`, `scripts/rerun_review_status.py`를 `tools/apply_baseline.py`로 다시 복사한다. 이벤트 정책 조회는 이 저장소 루트의 `tools/review_status_policy.py`를 쓴다.

## 2026-11-04 — 동결 전 역할과 리뷰 기록

- `docs/development-workflow.md`: Grok Bot은 코드를 쓰지 않고 접수·추적·근거 확인·보고를 맡는다. 코드는 Claude Code(Mac)와 Cursor 클라우드 에이전트가 쓴다. 1인 프로필의 `review/independent`·`review/security`는 소유자가 남긴다. 서버 절차 전에는 Mac의 `gh`이고, 마치면 서버의 앱이다. 구현 에이전트와 `Review status` workflow는 쓰지 않는다. Cursor·Codex의 버그 찾기와 Security는 실제 PR로 확인하기 전까지 미확인이다. 템플릿과 검사기는 안 바뀌어 소비 프로젝트 재적용은 필요 없다.

## 2026-11-04 — Review status workflow 설치

- `.github/workflows/review-status.yml`: `templates/review-status.yml`을 그대로 복사했다. 다른 workflow와 합치지 않았고 이벤트를 더하지 않았다. 필수 체크 등록은 이 병합 뒤 소유자 승인으로 따로 한다. 템플릿은 안 바뀌어 소비 프로젝트 재적용은 필요 없다.

## 2026-11-04 — 한쪽 문 승인 댓글을 검사기가 요구

- `scripts/check_review_status.py`: 1인 프로필에서 §10 표의 게이트 경로를 바꾼 PR은 저장소 소유자의 이슈 댓글 `한쪽 문 승인: <현재 head의 전체 SHA>`가 있어야 `Review status`가 통과한다. 실패 이름은 `review/owner-approval`이다. commit status로 올리지 않는다. 그 이름의 status가 있어도 댓글을 대신하지 않는다. 다른 SHA, 다른 작성자, 댓글 없음은 실패다. 새 head는 이전 댓글을 잇지 않는다. 양쪽 문과 Dependabot 버전 전용 예외는 통과한다. 파일 목록이 잘리면 댓글을 요구한다. 기준 브랜치 `AGENTS.md`의 한 줄이 `프로필: 팀`이면 팀 프로필이라 이 댓글을 요구하지 않는다. 그 줄을 더하거나 빼는 diff는 기준 브랜치가 아직 1인이면 댓글을 요구한다. 판정은 그 head의 `compare`로 하고, 열린 PR의 최신 파일 목록으로 하지 않는다. 주 버전과 표 밖의 한쪽 문은 판정하지 않는다.
- `templates/review-status.yml`: `issue_comment`의 생성·수정·삭제가 열린 PR의 댓글이고 작성자가 저장소 소유자이면, PR 코드를 checkout하지 않고 댓글 본문을 실행하지 않은 채 그 head의 `pull_request_target` 실행을 다시 돌린다. 다른 사람의 댓글은 다시 돌리지 않는다. 같은 PR의 이전 재실행은 취소한다. `issue_comment` 실행은 PR 체크가 아니기 때문이다. 평가하는 job의 권한은 읽기다. 재실행 job만 `actions: write`다.
- 승인 댓글의 첫 줄은 CRLF여도 SHA를 읽는다.
- 게이트 경로의 Action 주 버전 변경과, `# vN`·`@vN`이 없어 주 번호를 모르는 `uses:`는 승인 댓글 예외가 아니다. 리뷰 status 면제는 그대로다.
- 댓글 재실행은 `pull_request_target` 실행을 head SHA로 찾지 않는다. 그 이벤트는 실행을 base 커밋에 적는다. 실행의 `pull_requests`에서 PR 번호와 head SHA가 같은 것만 다시 돌린다.
- 1인 승인 댓글의 작성자는 저장소 `owner.login`이다. 재실행도 그 로그인만 본다. 조직 소유 저장소는 그 로그인이 조직 이름이라 1인 프로필을 쓰지 않고 팀 프로필을 쓴다.
- 이벤트 정책 분류는 `workflow_path.exclude`에 `review-status.yml`이 있으면 그 정책을 대상으로 보지 않는다.
- `templates/review-status-policy.json`: 허용 이벤트는 `issue_comment`와 `pull_request_target`뿐이다.
- `POLICY.md` §9: 이 저장소도 `Review status`를 둔다. 예전 게이트 예외 문장은 뺐다. 순서는 이벤트 정책, workflow 파일, 그 다음 필수 체크 `Review status`다. 검사기를 바꾸는 PR은 정책·workflow 설치·필수 체크 등록을 하지 않는다.
- `POLICY.md` §10: 1인 승인 댓글은 필수 체크 `Review status`가 검사한다.
- 다시 적용할 프로젝트: Smallnext·BGLike·Runstir. `scripts/check_review_status.py`와 `scripts/test_review_status.py`를 `tools/apply_baseline.py`로 다시 복사한다. workflow 템플릿은 프로젝트의 `.github/workflows/review-status.yml`로 다시 복사한다. 그 파일을 병합하기 전에 이벤트 정책을 두 이벤트로 고친다. `pull_request_target`만 허용하는 정책이 있으면 PUT으로 고치고, 그 위에 POST로 더하지 않는다.

## 2026-11-04 — Issue #13 후속

- 주간 점검: 한쪽 문 승인 댓글의 `updated_at`이 병합 시각보다 늦으면 병합 뒤에 고친 것으로 보고 승인으로 세지 않는다.
- `scripts/check_review_status.py`: Dependabot 버전 전용 면제는 받은 커밋 수가 PR의 `commits`와 같을 때만 준다. 250개 상한으로 목록이 잘리면 면제하지 않는다.
- 이어받기 테스트 가운데 상태·diff를 보려는 경우는 `force_pushes=[]`로 이력을 읽은 뒤 그 경로까지 간다.
- `POLICY.md` §5: 한 라운드는 작성자의 수정 push 한 번이고, 그 push의 CodeRabbit 증분 리뷰는 같은 라운드다. check가 SKIPPED이거나 `Review paused`이면 외부 리뷰는 끝나지 않아 `@coderabbitai full review`를 요청한다. 이미 리뷰된 PR들의 충돌만 main에서 푼 head는 소유자가 재리뷰 없이 승인할 수 있다. 상한에 닿으면 남은 CodeRabbit 지적은 답하고 해결한 뒤 후속 Issue에 적고, 병합 뒤 후속 PR에서 고친다. 상한을 넘는 라운드는 소유자만 승인한다.
- 다시 적용할 프로젝트: Smallnext·BGLike·Runstir. `scripts/check_review_status.py`와 `scripts/test_review_status.py`를 `tools/apply_baseline.py`로 다시 복사한다.

## 2026-11-04 — 문 판정, 이벤트 정책 절차, 리뷰 호출

- `POLICY.md` §10(새 절): 문 판정의 단일 기준. 판정 질문은 "망가지면 사용자가 무엇을 잃나"다. Matt `/pr`의 되돌리기 비용 문장은 원문 그대로 두고(vendor에는 `matt-code-review`만 있다) Door 값만 이 절을 따른다. CI workflow와 리뷰 게이트 파일(`.github/workflows/**`, `templates/review-status.yml`, `scripts/check_review_status.py`, `templates/review-status-policy.json`, repository-settings)은 한쪽 문이다. Security 리뷰만으로 병합하지 않는다. Dependabot의 버전·해시·Action SHA만 바꾼 PR은 그 경로여도 사람 한쪽 문 승인에서 뺀다(§5와 같은 버전 전용 조건). 주 버전 변경(버전 주석·태그의 첫 숫자, 모르면 한쪽 문)과 `scripts/check_review_status.py` 변경(작성자 무관)은 빼지 않는다. 1인 프로필의 한쪽 문 승인은 저장소 소유자의 PR 댓글 `한쪽 문 승인: <head sha>`로 남긴 뒤에만 `--match-head-commit`으로 병합한다. auto-merge는 §9 ②를 마친 프로젝트의 양쪽 문 가운데 외부 리뷰 대상이 아닌 PR만 예약한다.
- `POLICY.md` §5: 병합 전에 달린 CodeRabbit 스레드는 PR 종류와 관계없이 답하고 해결한다. 병합 뒤에 달린 지적은 후속 PR로 처리한다. 외부 리뷰 대상 PR은 auto-merge를 예약하지 않는다. `interrogate` 같은 추가 의견은 외부 리뷰로 세지 않는다. Standards·Spec은 `/matt-code-review`만 부르고, `/implement` 안의 `code-review`는 `review/independent`로 세지 않는다.
- `POLICY.md` §9: 이 저장소는 `Review status` 게이트의 예외다. 검사기 원본을 바꾸는 PR은 §10의 한쪽 문으로 사람이 최종 head를 승인한다. 소비 프로젝트의 ①②는 그대로다.
- README 새 프로젝트 절차: 공개 저장소는 `review-status.yml`을 병합하기 전에 `templates/review-status-policy.json`으로 Actions 이벤트 정책을 만든다. 정책 조회가 실패하면 만들지 않는다. 주간 점검의 1인 한쪽 문 승인 댓글은 모든 페이지를 보고, 팀 프로필의 리뷰도 모든 페이지를 본다. 병합 시각보다 늦은 승인 댓글·리뷰는 세지 않는다.
- `docs/development-workflow.md`: `disable-model-invocation: true`인 Matt 스킬은 사용자가 실행한다. PR 담당자(Dependabot 주간 처리, CodeRabbit 대기, 병합 뒤 후속)를 정의했다. 필수 리뷰는 Claude Code에서 돌린다.
- 셋업 프롬프트 §5: 최종 전체 diff 리뷰를 건너뛰는 조건은 전체 diff로 리뷰한 SHA가 현재 head와 같을 때뿐이다. 바뀐 diff만 본 SHA는 그 조건에 들어가지 않는다. `/matt-code-review`에는 고정점(PR base SHA), spec 위치(Issue 또는 없음), 기준 브랜치의 표준 문서 경로를 넘긴다.
- 문서만 바뀌어 소비 프로젝트 재적용은 필요 없다.

## 2026-11-04 — 같은 diff의 리뷰 status 이어받기

- `scripts/check_review_status.py`: 새 head에 그 context가 없고 diff identity가 이미 `success`인 status와 같으면 `Review status`가 그 status로 통과한다. 기준 브랜치 갱신만이 아니다. 커밋 목록이나 force-push 이력을 읽지 못하면 이어받지 않는다. 받은 커밋 수가 PR의 `commits`보다 적거나, force-push 이전 SHA가 없으면 이어받지 않는다. identity는 경로, 파일 모드, rename·copy, 추가·삭제한 줄, 바이너리 blob SHA다. 줄 번호와 주변 줄은 보지 않는다. 공백이 다르거나 diff를 읽지 못하면 이어받지 않는다. 이 head에 `failure`가 있으면 이전 성공으로 덮지 않는다. rebase로 커밋 목록에서 빠진 SHA는 pull request의 force-push 이전 head에서 찾는다. `git patch-id`는 공백을 지워서 쓰지 않았다. 이어받기는 절차 기록이고 보안 경계가 아니다. 이 검사기는 주 버전과 문 유형을 판정하지 않는다.
- Dependabot이 버전·해시·Action SHA만 바꾼 PR은 `review/independent`도 면제한다. 조건은 기존 `review/security` 예외와 같다. 이 면제는 리뷰 status(`review/security`, `review/independent`)와 외부 리뷰를 뺀다. 그 head에 리뷰 status가 있으면 `success`여야 한다. 사람 한쪽 문 승인은 빼지 않는다. 주 버전 변경과 `scripts/check_review_status.py` 변경은 그 승인에서 빼지 않는다.
- `POLICY.md` §8·`prompts/weekly-check.md`: 공개 저장소에 `review-status.yml`이 있으면 Actions 이벤트 정책이 그 파일의 `pull_request_target`만 허용하는지 본다.
- 다시 적용할 프로젝트: Smallnext·BGLike·Runstir. `tools/apply_baseline.py`로 `scripts/check_review_status.py`와 `scripts/test_review_status.py`를 다시 복사한다. 각 프로젝트의 ②(필수 체크) 전에는 이 검사기가 기본 브랜치에 있어야 이어받기가 동작한다.

## 2026-11-04 — 1인·팀 프로필, 리뷰 기록, 도구 층

- `POLICY.md` §9(새 절): 1인(기본)과 팀(2~6명) 프로필. 팀 프로필은 GitHub 필수 승인 1명·코드 소유자 리뷰·마지막 push 승인을 켜고 `templates/CODEOWNERS`로 신뢰 경계 경로의 소유자를 둔다. PR 책임자(에이전트를 시킨 사람 포함)와 에이전트·봇의 승인은 세지 않는다. 에이전트는 PR을 승인하지 않는다. 가벼운 승인 경로는 두지 않는다. 양쪽 문은 승인·CI·리뷰 뒤 에이전트가, 한쪽 문은 승인한 사람이나 PR 책임자가 병합한다. 조직 소유 저장소의 ruleset(조직 ruleset은 Team·Enterprise)·merge queue·우회 목록 지원 범위와 비공개 팀 저장소의 CodeRabbit 비용을 공식 문서로 확인해 적었다. 프로젝트는 `AGENTS.md`에 프로필을 한 줄로 적는다.
- `POLICY.md` §5: 리뷰 표에 "언제"·외부 리뷰·정기 Security 감사(Cloudflare `security-audit`)·회고를 넣었다. 버그 찾기는 코드가 바뀐 PR에만 한다. 문서·신뢰 경계가 아닌 설정만 바꾸는 양쪽 문은 Standards·Spec 하나만 받는다(가벼운 경로). 역할마다 결정적 검사와 LLM 리뷰를 하나씩만 둔다. 공통 신뢰 경계 경로에 `.github/actions/**`, `.github/dependabot.yml`, `.github/dependabot.yaml`, `.github/CODEOWNERS`, `.github/repo-baseline.json`, `.github/trust-boundary-paths`, `scripts/check_*.py`, `.claude/settings.json`, `.claude/hooks/**`, `.claude/agents/**`, `.claude/commands/**`, `.agents/skills/**`, `.claude/skills/**`, `.mcp.json`을 더했다. `tools/test_distribution.py`가 POLICY·CODEOWNERS·검사기의 목록이 같은지 본다. 앞으로 baseline을 다시 적용하는 PR은 Security 리뷰 대상이다.
- 리뷰 기록(두 프로필): 리뷰를 마치면 리뷰한 head SHA에 commit status(`review/independent`, Security를 실행했으면 `review/security`)를 남긴다. 새 `Review status` CI job(`scripts/check_review_status.py`, `templates/review-status.yml`)이 바뀐 파일 경로로 필요한 status를 정하고 그 head에 없으면 실패한다. `pull_request_target`으로 기본 브랜치의 코드만 실행하므로(PR 대상이 다른 브랜치여도 같다) PR이 이 job의 코드를 고칠 수 없다. 같은 이름의 job을 더하는 경우는 Security 리뷰에서 본다. 내용 기준은 리뷰어 판단으로 남긴다. Dependabot 예외는 `POLICY.md` §5대로 적용한다. 이름에 붙은 숫자는 버전으로 보지 않아, 패키지 이름을 바꾸는 줄과 npm·yarn lockfile의 `resolved` URL은 Security 리뷰를 받는다. 두 단계로 도입한다. ① job을 두고 에이전트가 status를 남기기 시작하고 ② 프로젝트마다 승인받아 필수 체크로 등록한다. **1인 프로필의 기본값이 바뀐다**: ② 이후 필수 체크가 하나(`Review status`) 더 생긴다. 같은 계정의 status는 사람과 에이전트를 구분하지 못하는 절차 기록이다. CodeRabbit은 외부 리뷰 대상 PR에서만 기다린다.
- GitHub auto-merge: ②를 마친 프로젝트의 양쪽 문에만 쓴다. revert 없는 기간은 조건으로 두지 않는다. 주간 점검의 hotfix 비율은 참고용이다.
- 셋업 프롬프트 §5: 마지막으로 리뷰한 head SHA가 그대로면 최종 전체 diff 리뷰를 다시 하지 않는다. 기준 브랜치 갱신만으로 head가 바뀌면 그 뒤 바뀐 diff만 재리뷰하고 새 SHA에 status를 남긴다.
- 도구 층(`POLICY.md` §7, `docs/development-workflow.md`): 저장소·계정·로컬 층으로 나눴다. 리뷰 관문 스킬은 저장소에 커밋한다. `vendor/mattpocock-skills/matt-code-review`(Matt Pocock `code-review` v1.3.2, MIT, 이름만 `matt-code-review`로 바꿈. 내장 `/code-review`와 겹치지 않게)를 manifest대로 `.agents/skills/`와 `.claude/skills/`에 복사한다. `@AGENTS.md` 한 줄만 있는 `CLAUDE.md`를 허용한다(내용 복제는 계속 금지).
- `templates/claude-settings.json`(두 프로필 공통): `.env` 읽기를 막고, 로컬 편의로 Matt Pocock 플러그인을 태그로 고정해 켠다. 설정 파일은 지침 파일이 아니다.
- `scripts/check_repo_baseline.py`: 커밋한 `.mcp.json`의 `env`·`headers` 값은 `${VAR}` 참조만 허용한다(앞의 `Bearer `·`Basic `·`Token `은 허용). `${VAR:-기본값}`과 고정값은 실패한다. 비밀이 아닌 고정값도 환경 변수로 옮긴다.
- `POLICY.md` §8·주간 점검: `Review status`가 성공하지 않은 병합 PR, 정기 감사 지연, 마켓플레이스 태그가 가리키는 commit의 변경을 표시한다.
- 다시 적용할 프로젝트: Smallnext·BGLike·Runstir.
  1. `.github/repo-baseline.json`에 `templates/repo-baseline.json`의 `matt-code-review` 여섯 항목과 `scripts/check_review_status.py`·`scripts/test_review_status.py`를 더하고 `tools/apply_baseline.py`로 다시 적용한다.
  2. `.claude/settings.json`을 `templates/claude-settings.json`으로 둔다. 기존 파일이 있으면 합친다. `.mcp.json`이 있으면 `env`·`headers` 값을 기본값 없는 `${VAR}` 참조로 바꾼다(앞의 `Bearer ` 등은 허용).
  3. `AGENTS.md`에 프로필 한 줄(1인)을 적는다. `@AGENTS.md` 한 줄만 있는 `CLAUDE.md`(Smallnext·BGLike)는 그대로 둔다. 프로젝트 신뢰 경계 경로를 `.github/trust-boundary-paths`에 적는다. 기존 프로젝트 리뷰 문서의 경로를 옮기고 문서에서 연결한다.
  4. 공개 저장소는 먼저 `templates/review-status-policy.json`으로 Actions 이벤트 정책을 만든다. 없으면 2026-12-02부터 job이 막힌다(`POLICY.md` §9). 그 뒤 `templates/review-status.yml`을 별도 파일 `.github/workflows/review-status.yml`로 두어 병합하고(기본 브랜치에 있어야 돈다. 다른 이벤트를 더하면 정책이 막는다) 에이전트가 리뷰 status를 남기기 시작한다.
  5. 실제 PR에서 status 없이 job의 실패를, status를 남기고 다시 돌려 성공을 확인한 뒤 프로젝트마다 승인받아 `.github/repository-settings.json`의 `checks`에 `Review status`(`app_id: 15368`)를 더하고 `tools/apply_github_settings.py`로 등록한다. 그 뒤부터 양쪽 문에 auto-merge를 쓸 수 있다.

## 2026-11-03 — 리뷰 수렴과 위험 판정

- 근거: [How the Claude Code team does code review](https://claude.dev/blog/solving-code-review-at-anthropic/)(2026-10-15).
- 셋업 프롬프트 §5: 수정 뒤의 재리뷰 라운드는 바뀐 diff만 보고(병합 전 최종 head 전체 리뷰는 유지), 지적은 결함 유형으로 남기고 반복하지 않는다. 스타일만의 지적은 버리고, P0/P1/P2에 더해 Pre-existing을 표시한다. 라운드 상한(`POLICY.md` §5, 3)을 넘으면 접근 방식을 다시 검토해 사용자에게 보고한다.
- 셋업 프롬프트 §6: 리뷰 근거는 `file:line`, 보고는 지적 개수로 시작한다. 리뷰 문서에 영역별 실패 정의·P2 상한·건너뛸 경로·사용자가 승인한 "배운 규칙"을 둔다.
- 셋업 프롬프트 §10·§5, `POLICY.md` §5, README 요청문: 위험 등급은 변경 내용으로 정하고 판정 질문("망가지면 사용자가 무엇을 잃나")을 적었다. 위험 변경에도 외부 리뷰를 받는다. 같은 모델의 별도 컨텍스트 리뷰는 외부 리뷰로 세지 않는다.
- `POLICY.md` §5·셋업 프롬프트 §5: 리뷰는 Standards·Spec·버그 찾기를 실행하고 신뢰 경계 변경에 Security를 더한다. 도구는 POLICY §5 표에 둔다. Standards·Spec은 Matt Pocock `code-review`, 버그 찾기는 내장 `/code-review`(양쪽 문 `low`, 한쪽 문·위험 변경 `high`), Security는 내장 `/security-review`(열린 지적이 있으면 병합하지 않음).
- `POLICY.md` §5: 신뢰 경계 변경을 한 곳에 정의했다. 작성자 판단이 아니라 diff의 공통 경로·프로젝트 경로·내용 기준으로 정하고, 애매하면 신뢰 경계로 본다. POLICY와 셋업 프롬프트에서 서로 달랐던 목록을 이 정의로 바꿨다. PR 본문 Merge Danger에 걸린 기준을 적는다. Dependabot이 버전·해시·Action SHA만 바꾼 PR은 경로 기준의 유일한 예외로 신뢰 경계로 보지 않는다(다른 줄이 바뀌거나 다른 사람이 커밋을 더하면 예외가 아님). 신뢰 경계 변경은 Security 리뷰 대상일 뿐이고, 사람 승인이 필요한 위험 변경은 셋업 프롬프트 §10으로 따로 판정한다(§10의 "신뢰 경계"는 "권한을 넓히는 변경"으로 좁혔다).
- 문서만 바뀌어 소비 프로젝트 재적용은 필요 없다.

## 2026-11-03 — 개선 반영 순서와 pstack 배치

- `POLICY.md` §6: 개선은 코드 구조·타입 → 결정적 검사 → 지침 → 사람 리뷰 순으로 가장 앞 단계에 반영한다. revert·hotfix PR 본문에 원래 PR과 놓친 단계를 적고 회고 후보로 둔다.
- `POLICY.md` §7·`docs/development-workflow.md`: pstack 스킬을 제안할 단계(`create-verification-skill`, `blast-radius`, `interrogate`, `correct`)와 쓰지 않을 중복을 적었다. 검증 스킬은 `AGENTS.md`만 쓰는 규칙의 유일한 예외로 셋업 프롬프트 §3에 적었다.
- 문서만 바뀌어 소비 프로젝트 재적용은 필요 없다.

## 2026-11-03 — 주간 점검

- `POLICY.md` §8·`prompts/weekly-check.md`: 선택적 주간 읽기 전용 점검을 추가했다. 기간과 기준값은 §8 표에 둔다.
- 문서만 바뀌어 소비 프로젝트 재적용은 필요 없다.

## 2026-10-27 — GitHub 설정 적용 도구

- `tools/apply_github_settings.py`를 추가했다. 프로젝트의 `.github/repository-settings.json`(감사 도구와 같은 기준선)을 읽어 다른 항목만 쓴다. 기본 실행은 현재 값과 기준값, 쓰기 요청을 출력만 하고, `--apply`는 쓴 뒤 다시 감사한다. 공개 여부·ruleset·workflow 파일과, 기준선 밖 설정이 켜진 브랜치 보호는 쓰지 않는다. 기준선 오류와 404 외의 조회 오류는 쓰기 전에 멈춘다.
- 새 프로젝트의 기준선 시작점 `templates/repository-settings.json`(채울 값은 `REPLACE`로 표시)과 이 저장소 자신의 `.github/repository-settings.json`을 두었다. 정책 값이 서로 어긋나면 `tools` 테스트가 실패한다.
- GitHub 설정 프롬프트 §3 표에 기준선이 이미 쓰던 값(기존 승인 무효화 On, 코드 소유자 리뷰 Off, 마지막 push 승인 Off, 브랜치 잠금 Off, Release 불변성 On)을 적었다.
- `scripts/check_github_settings.py`의 schema·저장소 이름·브랜치 검사를 `validate_target()`으로 분리했다. 동작은 같아 소비 프로젝트 재적용은 필요 없다. 다음에 다시 맞출 때 함께 복사된다.

## 2026-10-27 — Matt Pocock 스킬 사용법을 다시 적지 않음

- 개발 절차 문서·PR/CI 셋업 프롬프트·POLICY·README에서 스킬의 단계(셋업 세부, 작업 크기별 진입 표, 명세→티켓→구현, 스킬 선택, retro 단계)를 옮겨 적던 부분을 뺐다. 옮겨 적은 내용이 원문과 어긋나 있었다(원문은 변경마다 grilling을 권하지만 문서는 불확실할 때만으로 바꿔 적음). 스킬은 설치된 원문대로 쓰고, 시작점은 `/ask-matt`에 묻는다.
- 남긴 것은 스킬이 정하지 않는 이 기준의 선택이다. `AGENTS.md`만 쓰기(셋업 스킬 전에 `CLAUDE.md`를 옮김), 모든 변경은 PR·필수 CI·위험별 병합(셋업 프롬프트 §10), 리뷰 정책(§5), 회고 정책(§6).
- README의 재적용 순서를 고쳤다. squash 병합과 병합 후 브랜치 삭제를 쓰므로 PR을 병합한 뒤 최신 `main`에서 적용한다.
- 공통 검사기·템플릿은 바뀌지 않아 소비 프로젝트 재적용은 필요 없다.
- 권한·Secret·workflow·저장소 설정·dependency 정책 PR의 추가 리뷰를 "다른 모델"에서 "작성자 세션 밖의 외부 리뷰"로 바꾸고, 공개 저장소는 CodeRabbit 무료 플랜으로 충족한다고 적었다. CodeRabbit은 참고용이며 필수 체크·자동 수정은 쓰지 않는다. GitHub 설정 프롬프트 §7도 CodeRabbit을 정리 대상에서 뺐다.
- CodeRabbit 리뷰 반영: 라벨 문서는 `triage`가 설치됐을 때만 완료 조건에 넣는다(셋업 스킬이 그때만 라벨 단계를 진행). Claude Code 플러그인에서는 `/mattpocock-skills:<이름>`처럼 플러그인 이름을 붙여 부른다.

## 2026-10-27 — 이 저장소에도 Dependabot 버전 업데이트 적용

- `.github/dependabot.yml`을 두었다. 생태계가 GitHub Actions뿐이라 `templates/dependabot.yml`을 그대로 쓴다. SHA로 고정한 `check.yml`의 action은 보안 알림이 생기지 않으므로 이 정기 업데이트로만 갱신된다(`POLICY.md` §2).
- 이 저장소에는 manifest가 없어 `apply_baseline.py`로 생성하지 않는다. 첫 줄을 사본이라는 설명으로 바꾸고, 나머지가 템플릿과 어긋나면 `tools` 테스트가 실패하게 했다.

## 2026-10-27 — 지침 파일을 AGENTS.md로 통일

- 초기 설정 6단계가 `## Agent skills` 블록을 `AGENTS.md`에만 둔다. 파일이 없으면 만든다. PR/CI 셋업 프롬프트 §3도 canonical 파일 선택 대신 `AGENTS.md`로 정리하게 맞췄다.
- 공통 검사기·템플릿은 바뀌지 않아 소비 프로젝트 재적용은 필요 없다. 기존 프로젝트의 `CLAUDE.md`는 다시 맞출 때 고유 규칙을 `AGENTS.md`로 옮기고 지운다.

## 2026-10-26 — 공개 저장소 전환

- 현재 파일·Git refs의 전체 이력·GitHub PR/댓글/실행 자료를 민감정보 점검한 뒤 public으로 전환했다. 기존 clone과 복사 기반 배포 방식은 유지한다.
- README에서 원본이 비공개라는 제약을 갱신했다. 공통 검사기·템플릿은 바뀌지 않아 소비 프로젝트 재적용은 필요 없다.

## 2026-10-26 — 초기 설정·작업 진입·원본 검증 보완

- 공식 Matt Pocock 초기 설정과 tracker·라벨·도메인 문서 연결을 추가했다. 작은 수정과 명세 → 의존성 티켓 → 준비된 작업 → 통합 검증 경로를 구분한다.
- 설정 검사기에 근거 있는 기능 미지원·비해당 예외와 LIMITED 결과를 추가했다. 기존 schema version 1은 유지하며, 예외가 없는 403·404·누락은 계속 검증 실패다.
- 원본 단위 테스트의 소비 프로젝트 의존성을 없앴다. 임시 Git 원본에서 실제 복사·프로젝트 테스트·출처·drift·복구·CodeQL pin 실패를 검사하고 읽기 전용 자체 CI에 연결했다.
- 복사본 해시 검사는 프로젝트 CI에서 별도 명령으로 실행한다. 다시 적용할 프로젝트: smallnext, BGLike, mobile-runtime. 기존 프로젝트·서버 설정은 이 변경으로 갱신되지 않는다.

## 2026-10-26 — 자체 리뷰와 선택적 회고

- 두 셋업 프롬프트·정책·README에서 Bugbot 전용 셋업·규칙 예산·서버 시험 요구를 제거했다. 자체 Standards·Spec 리뷰와 확실한 결함의 직접 수정·커밋을 기본으로 한다.
- 공통 manifest에서 Bugbot 검사기·테스트·규칙 목록을 제거하고 해당 원본 파일을 삭제했다. 기존 프로젝트의 CI 호출·manifest·복사본 정리 순서는 README의 전환 절차를 따른다. 고유 코딩 규칙은 보존한다.
- Matt Pocock `mattpocock-skills:retro`의 출처·사용자 요청·기록 기반 제안·선택한 개선의 반영·검증 절차를 추가했다.
- 다시 적용할 프로젝트: smallnext, BGLike, mobile-runtime. 서버 비활성화·계정 연결 해제와 기존 프로젝트 반영은 이 원본 변경으로 실행되지 않는다.

## 2026-10-18 — Grouped security updates

- `POLICY.md` §2: Grouped security updates를 공통값으로 켠다. 계정 기본값과 smallnext·BGLike·mobile-runtime에 적용했다. API로 감사할 수 없어 화면 확인 항목으로 남긴다.

## 2026-10-18 — Dependabot 설정 생성·추적

- `.github/dependabot.yml`을 `templates/dependabot.yml`과 `templates/dependabot-ecosystem.yml`로 생성한다. 프로젝트별 생태계는 manifest의 `ecosystems`에 적는다.
- 생성한 파일도 해시로 추적한다. 프로젝트에서 Dependabot 값을 바꾸면 CI가 실패한다.
- 다시 적용할 프로젝트: smallnext, BGLike, mobile-runtime.

## 2026-10-18 — 독립 리뷰 6차 반영

- `check_github_settings.py`: `github/codeql-action` 이름을 대소문자 구분 없이 찾는다. GitHub는 owner/repo 이름의 대소문자를 구분하지 않는다.
- 이스케이프·줄 연결로 이름을 숨기는 표기는 보류했다. 후속 Issue로 추적한다.
- 다시 적용할 프로젝트: smallnext, BGLike, mobile-runtime.

## 2026-10-18 — 독립 리뷰 5차 반영

- `check_github_settings.py`: 따옴표 밖의 `#`만 주석으로 지운다. 블록 경계를 블록을 가진 키의 열로 계산한다. 따옴표 안의 `: |`는 블록 헤더로 보지 않는다.
- 남은 한계(이스케이프·줄 연결로 이름 숨기기)는 위협 모델 밖으로 `POLICY.md` §3에 기록했다.
- 다시 적용할 프로젝트: smallnext, BGLike, mobile-runtime.

## 2026-10-18 — 독립 리뷰 4차 반영

- `check_github_settings.py`: step 구조 해석을 없앴다. 주석과 블록 본문을 뺀 모든 `github/codeql-action/` 참조를 비교한다. 단독 `-`, 여러 줄 flow 표기로도 참조를 숨길 수 없다.
- 다시 적용할 프로젝트: smallnext, BGLike, mobile-runtime.

## 2026-10-18 — 독립 리뷰 3차 반영

- `check_github_settings.py`: step 수준에서 읽지 못한 `github/codeql-action/` 표기는 실패로 처리한다(fail-closed). `-   name:`처럼 공백이 많은 목록 표기도 읽는다.
- `test_apply_baseline.py`: 테스트가 직접 만든 임시 폴더만 지운다.
- 다시 적용할 프로젝트: smallnext, BGLike, mobile-runtime.

## 2026-10-18 — 독립 리뷰 2차 반영

- `apply_baseline.py`: `git --literal-pathspecs`로 추적 여부를 확인한다. `:(exclude)…` 같은 이름이 다른 파일과 매칭되지 않는다.
- `check_github_settings.py`: step 단위 `uses:` 키만 읽는다. `run:` 블록 본문과 `with:` 입력은 무시한다. 접힌 값은 고정으로 보지 않는다.
- `test_github_settings.py`: CodeQL 테스트가 프로젝트의 setup 종류와 무관한 fixture를 쓴다. default setup 프로젝트에서도 통과한다.
- 다시 적용할 프로젝트: smallnext, BGLike, mobile-runtime.

## 2026-10-18 — 독립 리뷰 반영

- `apply_baseline.py`: 추적된 저장소 내부 파일만 원본으로 허용한다. manifest와 대상의 symlink·외부 경로를 거부한다.
- `check_github_settings.py`: CodeQL 참조를 실제 `uses:` 줄에서만 읽는다. 대소문자를 정규화하고 태그 참조도 불일치로 본다. default setup 기준선을 지원한다.
- 다시 적용할 프로젝트: smallnext, BGLike, mobile-runtime.

## 2026-10-18 — 첫 버전

- 세 프로젝트(smallnext, BGLike, mobile-runtime)의 공통 검사기를 모았다.
  - `check_github_settings.py`: CodeQL `init`·`analyze` commit 불일치 검사를 추가했다.
  - `check_bugbot_rules.py`: 필수 규칙 목록을 `.github/repo-baseline.json`의 `bugbot_rules`에서 읽는다.
  - `check_repo_baseline.py`: 복사본 해시 검사를 새로 추가했다.
- Dependabot 공통값을 `POLICY.md`와 `templates/dependabot.yml`에 고정했다. 상한은 GitHub 기본값 5를 쓴다.
- 프롬프트 v4를 v5로 고쳤다. 값은 이 저장소를 참조한다.
- 다시 적용할 프로젝트: smallnext, BGLike, mobile-runtime.
