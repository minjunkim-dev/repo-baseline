# ops 프로필

배포해서 사람이 쓰는 앱(웹, 서버, 모바일, 게임)이면 기본으로 켠다. 배포하지 않는 저장소(라이브러리, 도구, 문서)에는 켜지 않는다. 소비 레포에 복사할 파일은 없다. 앱 코드와 배포 대상이 스택마다 달라서다. 붙었는지는 repo-baseline 클론의 `tools/check_ops.py`로 확인한다.

이 프로필은 도구를 고르는 일과 설정하는 곳을 정한다. 도구마다 설정하는 곳은 아래 표의 「설정하는 곳」 열에 적는다.

## 기본값과 예외

- 표의 도구를 모두 쓴다. 저장소마다 도구를 다시 고르지 않는다.
- 빼는 도구만 그 저장소 `AGENTS.md`의 ops 블록 끝에 `뺀 도구: <도구> — <이유>` 한 줄로 적고, 그 도구가 나오는 줄을 지운다(「켜기」). 예: `뺀 도구: Cloudflare — 웹 도메인이 없는 데스크톱 게임`. 이 줄이 없으면 모두 쓴다.
- Grafana Cloud와 Infisical은 표의 조건이 생기면 켠다. 조건이 없을 때 켜지 않은 것은 예외가 아니다.
- ops 절은 저장소를 만들 때 넣는다. SDK 설치와 감시 등록은 처음 배포하는 PR에서 한다. 보낼 에러와 사용자가 생기는 때이고, SDK PR은 되돌리기 어려움이라 소유자가 diff를 읽기 때문이다.
- 이미 배포한 앱에 처음 켜면 ops 절을 붙이는 PR이 병합된 뒤 SDK 설치와 감시 등록만 하는 PR을 따로 연다. 판 올리기에서도 같다.

## 도구

| 분야 | 도구 | 설정하는 곳 |
| --- | --- | --- |
| 코드·의존성 보안 | GitHub secret scanning, push protection, Dependabot, CodeQL | 조직 한 번 + [github 프로필](../../templates/github/)의 저장소 설정 검사 |
| 비밀값 유출 검사 | GitGuardian | 조직 한 번(GitHub App) |
| 에러 추적 | Sentry | 조직 한 번(계정, GitHub 연동) + 소비 레포마다(SDK, 프로젝트) |
| 제품 분석 | PostHog | 조직 한 번(계정) + 소비 레포마다(SDK, 프로젝트) |
| 서버 감시·알림 | UptimeRobot | 배포한 URL마다 |
| 웹 보안·CDN | Cloudflare | 도메인마다 |
| 로그·지표 | Grafana Cloud | 서버를 직접 운영할 때만 |
| 비밀값 관리 | Infisical | 비밀값이 세 곳 넘게 퍼지면. 그 전에는 GitHub secrets와 로컬 `.env` |

무료 한도와 요금은 자주 바뀐다. 켜기 전에 각 서비스의 요금 페이지를 확인한다. 이 표는 무료 플랜으로 시작하는 것을 전제로 한다.

## 조직에서 한 번

소유자가 한다. 저장소 파일을 바꾸지 않는다.

1. GitHub 조직의 Code security 설정에서 secret scanning, push protection, Dependabot alerts·security updates, CodeQL default setup을 켠 구성을 새 저장소의 기본값으로 정한다. 그러면 새 저장소가 [github 프로필](../../templates/github/)의 `repository-settings.json` 가운데 `security_and_analysis` 항목을 처음부터 맞춘다. 병합 설정, 브랜치 보호, 머지 큐는 github 프로필 절차로 따로 켠다. CodeQL을 고급 설정 workflow로 돌리는 저장소는 default setup을 끈 채로 둔다(두 설정은 함께 켤 수 없다).
2. GitGuardian GitHub App을 조직의 모든 저장소에 설치한다.
3. Sentry와 PostHog 조직 계정을 하나씩 만든다. Sentry의 GitHub 연동을 조직에 설치한다(커밋과 릴리스를 에러에 잇는다).

## 소비 레포마다

배포하는 앱 하나마다 처음 배포할 때 한다. 이미 배포한 앱이면 ops 블록을 붙인 뒤 따로 여는 PR에서 한다. 에이전트가 해도 된다. `뺀 도구:` 줄에 있는 도구는 건너뛴다.

1. Sentry 프로젝트를 만들고 그 앱의 SDK를 설치한다. 설치 방법은 Sentry 공식 문서의 그 스택 페이지를 따른다.
2. PostHog 프로젝트를 만들고 SDK를 설치한다. 개인 정보(이메일, 이름, 입력값)는 이벤트 속성에 넣지 않는다. 세션 녹화를 켜면 입력 필드와 개인 정보를 보여 주는 화면 요소를 가린다. 일반 화면 텍스트는 기본으로 녹화될 수 있다.
3. 소유자가 배포한 URL을 UptimeRobot에 등록한다. 알림은 소유자에게 간다.
4. 도메인이 있으면 Cloudflare에 연결한다. DNS를 옮기는 일이라서 소유자가 한다.
5. `.env.example`에 아래 이름의 빈 칸을 더한다. 값은 커밋하지 않는다. 그 PR에서 `python3 <repo-baseline 클론>/tools/check_ops.py --sdk`가 `ops: 통과`를 출력해야 한다.
6. 서버를 직접 운영하게 되면 Grafana Cloud에 로그와 지표를 보낸다. 비밀값을 두는 곳이 GitHub secrets와 로컬 `.env`를 더해 세 곳을 넘으면 Infisical로 옮긴다. 둘 다 소유자에게 먼저 알린다.

## 비밀값 이름

소비 레포는 이 이름을 그대로 쓴다. 프레임워크가 접두를 요구하면(예: Next.js `NEXT_PUBLIC_`) 접두만 붙인다.

| 이름 | 무엇 | 비밀값인가 |
| --- | --- | --- |
| `SENTRY_DSN` | 에러를 보낼 주소. SDK 초기화에 넘긴다 | 아니다. 클라이언트 코드에 들어간다 |
| `SENTRY_AUTH_TOKEN` | CI가 소스맵·릴리스를 올리는 토큰 | 그렇다. GitHub secrets에만 둔다 |
| `POSTHOG_KEY` | PostHog 프로젝트 키 | 아니다. 클라이언트 코드에 들어간다 |
| `POSTHOG_HOST` | PostHog 지역 주소 | 아니다 |

## 켜기

소비 레포 `AGENTS.md` 「작업 방식」 끝에 아래 블록을 표시 줄(`<!-- repo-baseline:ops -->`, `<!-- /repo-baseline:ops -->`)까지 그대로 붙인다. 규칙을 그대로 옮기므로 repo-baseline 클론이 없는 세션도 읽는다. 블록 안은 손으로 고치지 않는다. 빼는 도구가 있으면 그 도구 이름(또는 그 도구의 비밀값 이름)이 나오는 줄을 지우고, 끝 표시 줄 바로 앞에 `- 뺀 도구: <도구> — <이유>` 줄을 더한다. 줄마다 도구가 하나뿐이라 이 두 가지 말고는 바꿀 것이 없다. hash-copy manifest의 `blocks`에 적으면 도구가 이 일을 한다(`profiles/hash-copy/README.md`).

```markdown
<!-- repo-baseline:ops -->
### ops

- repo-baseline ops 프로필의 도구를 모두 쓴다. 빼는 도구는 이 블록 끝에 `뺀 도구: 도구 — 이유` 한 줄로 적고 그 도구의 줄을 지운다. 다른 도구를 더하려면 먼저 소유자에게 묻는다.
- 코드·의존성 보안(GitHub secret scanning, push protection, Dependabot, CodeQL)은 켜져 있다. CodeQL은 기본 설정을 먼저 쓰고, 기본 설정으로 분석이 안 될 때만 고급 설정 workflow를 쓴다. 그 이유는 저장소 문서에 적는다. secret scanning, push protection, Dependabot은 조직 기본값으로 켜고, 기존 저장소는 github 프로필 절차로 맞춘다. 저장소에서 끄지 않는다.
- GitGuardian은 조직에 설치한 GitHub App으로 돈다. 저장소에서 끄지 않는다.
- 에러 추적은 Sentry다.
- 제품 분석은 PostHog다.
- SDK는 처음 배포하는 PR에서 붙인다. 이미 배포한 앱이면 이 블록을 붙인 뒤 따로 여는 PR에서 붙인다.
- 배포한 URL은 UptimeRobot에 소유자가 등록한다.
- 도메인은 Cloudflare에 소유자가 연결한다. DNS와 Cloudflare 설정 변경도 소유자가 한다.
- 서버를 직접 운영하게 되면 Grafana Cloud를 켠다. 켜기 전에 소유자에게 알린다.
- 비밀값이 세 곳을 넘으면 Infisical을 켠다. 켜기 전에 소유자에게 알린다.
- Sentry 비밀값 이름은 `SENTRY_DSN`, `SENTRY_AUTH_TOKEN`이다. `.env.example`에 빈 칸으로 둔다. `SENTRY_AUTH_TOKEN`은 GitHub secrets에만 둔다.
- PostHog 비밀값 이름은 `POSTHOG_KEY`, `POSTHOG_HOST`다. `.env.example`에 빈 칸으로 둔다.
- 개인 정보는 분석 이벤트에 넣지 않는다. 세션 녹화를 켜면 입력 필드와 개인 정보를 보여 주는 화면 요소를 가린다.
- SDK를 처음 붙이거나 보내는 데이터를 넓히는 PR은 되돌리기 어려움이다(POLICY §4 다른 사람 데이터의 노출).
- 감시 대상 변경은 소유자가 한다.
<!-- /repo-baseline:ops -->
```

붙인 뒤 소비 레포에서 `python3 <repo-baseline 클론>/tools/check_ops.py`를 돌린다. 이 스크립트는 표시 줄 사이가 위 블록에서 뺀 도구의 줄만 지우고 `뺀 도구:` 줄을 더한 결과와 글자까지 같은지 본다. `--sdk`를 붙이면 `.env.example`에 비밀값 이름이 빈 칸으로 있는지도 본다(「소비 레포마다」 5번). 파일을 바꾸거나 서비스에 접속하지 않는다. README의 이 블록이 바뀌면 판 올리기 때 블록을 새 문구로 바꿔야 통과한다. hash-copy를 쓰는 소비 레포는 `tools/sync_consumers.py`가 그 PR을 연다.

SDK를 처음 붙이거나 보내는 데이터를 넓히는 PR은 사용자 데이터를 외부 서비스로 보낸다. POLICY §4의 「다른 사람 데이터의 노출」에 해당하므로 되돌리기 어려움이고, 소유자가 diff를 읽고 병합한다.
