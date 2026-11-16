# GitHub 프로필

코어(`templates/core/`)를 적용한 프로젝트를 GitHub에 올릴 때 쓴다. 기본 경계는 브랜치 보호 + 필수 CI + 소유자가 정하는 병합이다(POLICY §5).

저장소는 조직이 소유한 공개 저장소여야 한다. 머지 큐 ruleset을 그런 저장소에서만 쓸 수 있기 때문이다(POLICY §5). 조직 단위 설정은 아래 「조직 설정」을 따른다. `ci.yml`은 `merge_group` 이벤트에서도 돈다. 필수 체크인 workflow는 모두 `merge_group`에서도 돌아야 한다. 아니면 큐에 넣은 PR이 병합되지 않는다. `merge_group` 실행에는 `github.event.pull_request`와 `github.head_ref`가 없다.

| 파일 | 복사할 곳 | 메모 |
| --- | --- | --- |
| `ci.yml` | `.github/workflows/ci.yml` | `check`·`test` 단계를 `AGENTS.md`의 명령으로 바꾼다. 바꾸기 전에는 실패한다 |
| `dependabot.yml` | `.github/dependabot.yml` | 패키지 관리자마다 `dependabot-ecosystem.yml`의 블록을 붙인다 |
| `repository-settings.json` | `.github/repository-settings.json` | `REPLACE` 값을 채운다 |
| `SECURITY.md` | 저장소 루트 | GitHub은 `.github/`, 루트, `docs/` 순서로 이 파일을 찾는다. 셋 중 하나에 이미 있으면 그 파일에 합친다. `OWNER/REPO`를 채운다. 비공개 취약점 보고를 켠 뒤 이 파일을 병합한다 |
| `agents/` | 에이전트 도구별 | `agents/README.md` |

## 조직 설정

저장소를 조직으로 옮기기 전에 소유자가 조직 설정을 한 번 맞춘다. `apply_github_settings.py`는 저장소 설정만 다루고 조직 설정은 쓰지 않는다. 조직은 무료 플랜이면 된다. 아래 값은 2026-11-16에 `minjunkim-labs`에서 화면으로 맞춘 것이다.

| 화면 | 값 | 이유 |
| --- | --- | --- |
| Settings → Advanced Security → Configurations | 새 구성 하나: 시크릿 스캔과 push 보호, CodeQL default setup, Dependency graph, Dependabot 알림과 보안 업데이트, 비공개 취약점 보고를 Enabled로 둔다. 「Use as default for newly created repositories」는 Public, 「Enforce configuration」은 Don't enforce로 둔다. 기존 저장소에는 적용하지 않는다 | 조직에서 새로 만든 저장소가 처음부터 보안 기능을 갖는다. 강제하면 `apply_github_settings.py`가 설정을 바꾸지 못하고, 자체 CodeQL workflow를 쓰는 저장소와 default setup이 부딪친다 |
| Settings → Member privileges | 저장소 만들기(Public, Private), 공개 여부 변경, 삭제와 이전, 저장소 관리자의 GitHub App 설치, 팀 만들기를 모두 끈다. 기본 권한은 Read로 둔다 | 초대한 멤버가 저장소, 규칙, 연결된 App을 바꾸지 못하게 소유자만 한다. Public은 Private을 끈 뒤에야 끌 수 있다 |
| Settings → Actions → General | 외부 기여자 workflow 승인은 Require approval for all external contributors, Workflow permissions는 Read, Allow GitHub Actions to create and approve pull requests는 끈다 | 새 저장소가 물려받는 값을 저장소 기준값(`fork_policy`, `workflow_token`)과 맞춘다 |
| Settings → Authentication security | Require two-factor authentication을 켠다 | 켜기 전에 People → Outside collaborators를 본다. 2FA가 없는 외부 협력자는 조직에서 빠진다 |
| People | 소유자의 멤버십을 Public으로 둔다 | 개인 프로필에 조직이 보인다 |

저장소를 조직으로 옮기면 그 저장소의 시크릿 스캔, push 보호, CodeQL default setup이 꺼진다(2026-11-16 확인). 저장소 이름이 바뀌므로 `repository-settings.json`의 `repository`를 새 이름으로 바꾸는 PR을 먼저 병합하고, 그 뒤 「적용 순서」의 4·5로 다시 켠다. `repository_id`는 바뀌지 않는다. 옛 소유자 이름을 확인하는 workflow나 스크립트(`github.repository == '...'`)도 찾아 바꾼다.

멤버 권한과 2FA는 `read:org` 권한으로 읽어 확인한다. 나머지 조직 설정은 `admin:org` 권한이 필요해 화면에서 본다.

```sh
gh api orgs/<조직> --jq '{members_can_create_public_repositories, members_can_create_private_repositories, members_can_change_repo_visibility, members_can_delete_repositories, members_can_create_teams, two_factor_requirement_enabled}'
```

## 적용 순서

1. 위 파일을 복사하고 `ci.yml`의 두 단계를 채운다.
2. PR 하나를 열어 `ci` job이 실제로 성공하는 것을 본다.
3. `repository-settings.json`의 `repository`, `repository_id`(`gh api repos/OWNER/NAME --jq .id`), 필수 체크 `context`(2의 job 이름, 기본 `ci`), `patterns_allowed`를 채워 병합한다.
4. 소유자가 자기 기기에서 계획을 본다. 읽기만 한다.

   ```sh
   python3 <repo-baseline>/tools/apply_github_settings.py <project>
   ```

5. 계획을 승인하면 `--apply`를 붙여 다시 실행하고, 출력이 `PASS`인지 본다.

에이전트는 4·5를 실행하지 않는다. 도구는 소유자의 `gh` 로그인으로 `gh api`를 부른다.

## `apply_github_settings.py`

- 기본 실행은 다른 항목마다 `DIFF: 경로: 현재 값 -> 기준값`과 쓰기 요청 `PLAN`을 출력한다. 바꿀 것이 있으면 종료 코드 1이다.
- `--apply`는 다시 조회해 그때 다른 항목만 쓰고 같은 검사기로 감사한다. 쓰기는 항목 단위다.
- 남은 `REPLACE` 값, schema·저장소 이름·브랜치 오류는 조회 전에 멈춘다. 403 같은 오류는 아무것도 쓰지 않고 실패한다. 쓰기가 중간에 실패하면 쓴 요청을 출력하고 멈춘다. 계획을 다시 실행해 현재 상태를 본다.
- ruleset은 이름으로 맞춘다. 없으면 만들고, 다르면 통째로 바꾼다. 기준선에 없는 ruleset은 지우지 않고 `MANUAL`로 보고한다.
- 공개 여부·CodeQL workflow 파일, 기준선이 관리하지 않는 브랜치 보호(서명 커밋·push 제한 등)는 쓰지 않고 `MANUAL`로 보고한다. `MANUAL`이 남으면 종료 코드 1이다.
- CodeQL default setup은 비동기로 켜지므로 최대 2분 기다린 뒤 감사한다.

| 결과 | 종료 코드 | 뜻 |
| --- | --- | --- |
| `PASS` | 0 | 모든 기대값을 조회했고 일치함 |
| `LIMITED` | 0 | 확인한 항목은 일치하나 선언한 예외는 검사 밖. 보호 완료가 아님 |
| `DRIFT` | 1 | 기대값과 실제 값이 다르거나 필드가 없음 |
| `UNVERIFIED` | 2 | 기준선 오류·권한 부족·API 오류로 검증 못 함 |

## 예외

요금제·공개 여부·언어 때문에 적용할 수 없는 항목만 `exceptions`에 적고 `expected`에서 뺀다. 권한 부족이나 원인 불명은 예외가 아니다. 근거에는 공식 문서 URL과 확인 날짜를 적는다.

```json
"exceptions": {
  "codeql": {
    "status": "not_applicable",
    "reason": "CodeQL 지원 언어가 없음",
    "evidence": "https://codeql.github.com/docs/codeql-overview/supported-languages-and-frameworks/ (확인일)"
  }
}
```

- `status`는 `unsupported`(기능 미지원) 또는 `not_applicable`(이 프로젝트에 해당 없음)이다.
- 예외로 쓸 수 있는 항목은 `protection`, `rulesets`, `actions`, `allowed_actions`, `workflow_token`, `fork_policy`, `immutable_releases`, `private_vulnerability_reporting`, `dependabot_alerts`, `codeql`, `actions.sha_pinning_required`, `repository.security_and_analysis.<기능>.status`다. 저장소 ID·이름·기본 브랜치·공개 여부·병합 정책은 뺄 수 없다.
- 같은 항목을 기대값과 예외에 함께 두면 스키마 오류다.
- 비공개 저장소는 지원 범위 밖이다(POLICY §5). 머지 큐와 비공개 취약점 보고를 쓸 수 없어서, 예외로 빼면 병합 규칙이 성립하지 않는다. `apply_github_settings.py`는 비공개 취약점 보고가 404이면 아무것도 쓰지 않고 멈춘다.
