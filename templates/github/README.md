# GitHub 프로필

코어(`templates/core/`)를 적용한 프로젝트를 GitHub에 올릴 때 쓴다. 기본 경계는 브랜치 보호 + 필수 CI + 소유자가 정하는 병합이다(POLICY §5).

저장소는 조직이 소유한 공개 저장소여야 한다. 머지 큐 ruleset을 그런 저장소에서만 쓸 수 있기 때문이다(POLICY §5). 새 저장소는 「(a) 새 저장소 셋업」, 이미 쓰던 저장소는 「(b) 기존 저장소 옮기기」를 순서대로 따른다. 이 문서만 따라가도 누가 하든 같은 결과가 나와야 한다. 단계마다 하는 사람(에이전트·소유자), 명령, 성공을 확인하는 출력을 적었다.

| 파일 | 복사할 곳 | 메모 |
| --- | --- | --- |
| `ci.yml` | `.github/workflows/ci.yml` | `check`·`test` 단계를 `AGENTS.md`의 명령으로 바꾼다. 바꾸기 전에는 실패한다 |
| `dependabot.yml` | `.github/dependabot.yml` | 패키지 관리자마다 `dependabot-ecosystem.yml`의 블록을 붙인다 |
| `repository-settings.json` | 복사하지 않는다 | `.github/repository-settings.json`에는 저장소마다 다른 값만 쓴다. 「저장소 설정 파일」 |
| `SECURITY.md` | 저장소 루트 | GitHub은 `.github/`, 루트, `docs/` 순서로 이 파일을 찾는다. 셋 중 하나에 이미 있으면 그 파일에 합친다. `OWNER/REPO`를 채운다. 비공개 취약점 보고를 켠 뒤 이 파일을 병합한다 |
| `agents/` | 에이전트 도구별 | `agents/README.md` |
| `.coderabbit.yaml` | 저장소 루트 | CodeRabbit 리뷰 언어(한국어). 저장소마다 다른 값이 없는 공통 파일이다. 루트에 없으면 그대로 복사하고 고치지 않는다. 이미 있으면 `language` 줄만 합친다. 「CodeRabbit 설정」 |

## 계약 값

모든 저장소가 같은 값을 쓴다. 이 표가 정본이다. 다른 문서는 값을 다시 적지 않고 이 표를 가리킨다. 저장소 설정 값은 도구가 [repository-settings.json](repository-settings.json)에서 읽고, 테스트(`tools/test_distribution.py`)가 이 표와 그 파일이 같은지 본다.

| 항목 | 값 | 어디에 있나 |
| --- | --- | --- |
| 필수 체크 | 판정(gate) job 하나. 이름 `ci`, GitHub Actions(`app_id=15368`) | 저장소 파일 `protection.required_status_checks.checks` |
| CI 트리거 | `pull_request`와 `merge_group`. 판정 job과 세부 job 모두. `ci.yml` 템플릿은 `push: main`에서도 돈다. PR 실행은 main에서 만든 캐시를 읽고, `merge_group` 실행이 만든 캐시는 그 큐 브랜치만 읽는다([문서](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching#restrictions-for-accessing-a-cache), 2026-11-17 확인) | `.github/workflows/ci.yml` |
| 판정 방식 | `needs` + `if: always()`, 모든 `needs.*.result`가 `success`일 때만 통과 | `.github/workflows/ci.yml`(「필수 체크 계약」) |
| 최신 브랜치 요구 | `strict=false` | 템플릿 `protection.required_status_checks` |
| 머지 큐 | ruleset `merge-queue`: `merge_method=SQUASH`, `grouping_strategy=ALLGREEN`, `max_entries_to_build=5`, `max_entries_to_merge=5`, `min_entries_to_merge=1`, `min_entries_to_merge_wait_minutes=0`, `check_response_timeout_minutes=60` | 템플릿 `rulesets` |
| 병합 방식 | `allow_squash_merge=true`, `allow_merge_commit=false`, `allow_rebase_merge=false` | 템플릿 `repository` |
| 자동 병합 | `allow_auto_merge=false` | 템플릿 `repository` |
| 병합 뒤 브랜치 | `delete_branch_on_merge=true` | 템플릿 `repository` |
| base 병합 | PR 브랜치에 base를 합치지 않는다. 리뷰한 SHA로 큐에 넣는다 | POLICY §5 |

## (a) 새 저장소 셋업

시작 전에 소유자가 「조직 설정」을 한 번 맞춰 둔다. `<repo-baseline>`은 `main`을 받은 이 저장소의 클론, `<project>`는 새 저장소의 로컬 클론이다.

1. 소유자: 조직 아래에 공개 저장소를 만들고 받는다.

   ```sh
   gh repo create <조직>/<이름> --public --clone
   gh api repos/<조직>/<이름> --jq '[.visibility, .owner.type, .id] | @tsv'
   ```

   확인: `public	Organization	<숫자>`. 숫자는 4의 `repository_id`다.
2. 에이전트: 코어를 적용한다([prompts/setup.md](../../prompts/setup.md) 또는 [docs/start.md](../../docs/start.md)).
3. 에이전트: 위 표의 파일을 복사하고 `ci.yml`의 `check`·`test`를 `AGENTS.md`의 명령으로 채운다. 세부 job을 나누면 「필수 체크 계약」대로 판정 job `ci`가 모은다.

   확인: `grep -n REPLACE .github/workflows/ci.yml`이 아무것도 출력하지 않는다. `.coderabbit.yaml`을 새로 복사했으면 `cmp <repo-baseline>/templates/github/.coderabbit.yaml .coderabbit.yaml`이 아무것도 출력하지 않는다. 이미 있던 파일에 합쳤으면 `grep -qx 'language: "ko-KR"' .coderabbit.yaml`의 종료 코드가 0이다(「CodeRabbit 설정」의 1).
4. 에이전트: `.github/repository-settings.json`에 「저장소 설정 파일」의 예시 모양으로 저장소마다 다른 값만 쓴다. 필수 체크는 「계약 값」의 값이다. `patterns_allowed`에는 workflow가 쓰는 GitHub 밖 action을 `owner/repo@*`로 적는다. 아래 명령이 출력한 것 가운데 `actions/`·`github/`로 시작하지 않는 것이다. 없으면 빈 목록이다.

   ```sh
   grep -rhoE 'uses: *[^@ ]+' .github/workflows | sed -E 's/uses: *//' | sort -u
   ```

5. 에이전트: 2~4를 PR 하나로 연다. 이 PR은 민감한 파일을 건드리므로 POLICY §3·§4대로 새 세션이 리뷰한다.

   확인: `gh pr checks <PR>`에 `ci`가 `pass`로 나온다.
6. 소유자: diff를 읽고 병합한다. 아직 브랜치 보호와 큐가 없으므로 화면에서 squash로 병합한다. 그 뒤 `git -C <project> switch main && git -C <project> pull --ff-only`(기본 브랜치가 `main`이 아니면 그 이름).
7. 소유자: 계획을 본다. 읽기만 한다.

   명령은 「클론 맞추기와 재적용」의 블록이다. `<project-1> <project-2>`를 `<project>` 하나로 바꿔 실행한다.

   확인: `BASELINE: common values from <repo-baseline>/templates/github/repository-settings.json; ...` 줄이 있고, 끝 줄이 `Plan only; nothing written. Review it, then rerun with --apply.`다(종료 코드 1). `DIFF:` 줄이 「계약 값」과 다른 값을 바꾸는지 읽는다.
8. 소유자: `--apply`를 붙여 다시 실행한다.

   ```sh
   python3 <repo-baseline>/tools/apply_github_settings.py <project> --apply
   ```

   확인: 끝 줄이 `PASS: <조직>/<이름> settings match baseline`이다(종료 코드 0). `MANUAL:` 줄이 있으면 그 항목을 화면에서 고치고 7부터 다시 한다.
9. 에이전트: `SECURITY.md`를 PR로 연다. 8에서 비공개 취약점 보고가 켜졌으므로 이제 병합할 수 있다. 소유자가 리뷰한 SHA로 큐에 넣는다(POLICY §5).

   확인: `gh pr view <PR> --json state --jq .state`가 `MERGED`다. 큐를 거친 첫 병합이다.
10. 소유자: 계획을 한 번 더 본다(명령은 7과 같다).

   확인: 끝 줄이 `No writes needed`이고 종료 코드 0이다.

에이전트는 7·8을 실행하지 않는다. 도구는 소유자의 `gh` 로그인으로 `gh api`를 부른다.

## (b) 기존 저장소 옮기기

템플릿 전체를 복사한 옛 `.github/repository-settings.json`을 쓰는 저장소, 또는 개인 계정이 소유한 저장소를 이 계약으로 옮긴다. 옮기는 동안에도 옛 필수 체크가 그대로 요구되므로, 옛 job은 지우지 않고 세부 job으로 둔다.

1. 소유자(개인 계정 저장소일 때만. 에이전트는 하지 않는다): 「조직 설정」을 맞춘 조직으로 저장소를 옮긴다. 이미 조직 소유면 2로 간다.

   ```sh
   gh api repos/<개인>/<이름> --jq .id
   gh api --method POST repos/<개인>/<이름>/transfer -f new_owner=<조직>
   gh api repos/<조직>/<이름> --jq '[.full_name, .owner.type, .visibility, .id] | @tsv'
   git -C <project> remote set-url origin https://github.com/<조직>/<이름>.git
   git -C <project> remote -v
   ```

   확인: 셋째 명령이 `<조직>/<이름>	Organization	public	<숫자>`를 출력하고, 그 숫자가 첫째 명령의 숫자와 같다(저장소 ID는 옮겨도 바뀌지 않는다). 옮기기는 비동기로 끝난다([문서](https://docs.github.com/en/rest/repos/repos#transfer-a-repository), 2026-11-16 확인). 셋째 명령이 404이거나 옛 이름을 출력하면 잠시 뒤 다시 실행한다. `remote -v`의 `origin`이 `github.com/<조직>/<이름>`이다. 옮기면 시크릿 스캔, push 보호, CodeQL default setup이 꺼진다(2026-11-16 확인). 7·8의 apply가 다시 켠다.
2. 에이전트: 현재 서버 값을 기록한다. 9에서 비교한다. 브랜치 보호가 없으면 404가 나온다. 그것도 기록한다.

   ```sh
   gh api repos/<조직>/<이름>/branches/main/protection --jq '.required_status_checks'
   ```

3. 에이전트: 필수 체크를 판정 job `ci` 하나로 모은다. 옛 필수 체크였던 job은 이름을 바꾸지 않고 세부 job으로 둔다. 판정 job `ci`가 그 job들을 `needs`로 모은다(「필수 체크 계약」). 필수 체크로 쓰던 모든 workflow의 `on:`에 `pull_request`와 `merge_group`이 있게 한다. 1에서 옮겼으면 옛 소유자 이름을 쓰는 곳도 고친다. `grep -rn '<개인>/' .github`가 아무것도 출력하지 않아야 한다.
4. 에이전트: `.github/repository-settings.json`을 「저장소 설정 파일」의 예시 모양으로 줄인다. 파일이 없으면 (a)의 4대로 새로 쓴다. 남기는 값은 「저장소 설정 파일」의 둘째 항목에 적은 것뿐이다(1에서 옮겼으면 `repository`는 새 이름). `checks`는 「계약 값」의 값 하나로 바꾼다. 나머지는 모두 지운다. 그래서 `strict`도 템플릿 값을 따른다. 템플릿과 일부러 다르게 둔 값을 남겼으면 PR 본문에 이유를 적는다.
5. 에이전트: 3·4를 PR 하나로 연다. 「CodeRabbit 설정」의 1대로 `.coderabbit.yaml`을 같은 PR에 넣는다. 루트에 이 파일이 없으면 복사하고, 이미 있으면 `language` 줄만 합친다. 민감한 파일이므로 새 세션이 리뷰한다.

   확인: `gh pr checks <PR>`에 옛 필수 체크와 `ci`가 모두 `pass`로 나온다.
6. 소유자: diff를 읽고 리뷰한 SHA로 큐에 넣는다(POLICY §5). 큐가 아직 없으면(1에서 옮긴 직후 등) 화면에서 squash로 병합한다. 병합된 뒤 `git -C <project> switch main && git -C <project> pull --ff-only`(기본 브랜치가 `main`이 아니면 그 이름).
7. 소유자: 계획을 본다(명령은 (a)의 7).

   확인: `DIFF:`는 `protection.required_status_checks.strict: true -> false`와 `protection.required_status_checks.checks`(옛 체크 → `ci`) 둘뿐이다. 1에서 옮겼거나 큐가 없었으면 꺼진 보안 기능과 `rulesets.merge-queue`의 `DIFF:`도 나온다. 그 밖의 `DIFF:`는 옛 파일이 템플릿과 달랐던 값이다. 적용하지 않고 4로 돌아가 그 값을 남길지 정한다.
8. 소유자: `--apply`를 붙여 다시 실행한다(명령은 (a)의 8).

   확인: 끝 줄이 `PASS: <조직>/<이름> settings match baseline`이다.
9. 에이전트 또는 소유자: 2의 명령을 다시 실행한다.

   확인: `strict`가 `false`이고 `checks`에 `ci` 하나만 있다.
10. 에이전트: 다음 PR이 `ci`만으로 큐를 거쳐 병합되는지 본다. 확인은 (a)의 9와 같다.
11. 에이전트(필요할 때): 3에서 남긴 옛 판정 job을 `ci`에 합치거나 지우는 PR을 연다. 필수 체크가 이제 `ci` 하나이므로 옛 이름이 없어져도 PR이 막히지 않는다.

## 조직 설정

저장소를 조직으로 옮기기 전에 소유자가 조직 설정을 한 번 맞춘다. `apply_github_settings.py`는 저장소 설정만 다루고 조직 설정은 쓰지 않는다. 조직은 무료 플랜이면 된다. 아래 값은 2026-11-16에 `minjunkim-labs`에서 화면으로 맞춘 것이다. 2FA 필수는 2FA가 없는 외부 협력자가 있어 그 조직에서 아직 켜지 않았다.

| 화면 | 값 | 이유 |
| --- | --- | --- |
| Settings → Advanced Security → Configurations | 새 구성 하나: 시크릿 스캔과 push 보호, CodeQL default setup, Dependency graph, Dependabot 알림과 보안 업데이트, 비공개 취약점 보고를 Enabled로 둔다. 「Use as default for newly created repositories」는 Public, 「Enforce configuration」은 Don't enforce로 둔다. 기존 저장소에는 적용하지 않는다 | 조직에서 새로 만든 저장소가 처음부터 보안 기능을 갖는다. 강제하면 `apply_github_settings.py`가 설정을 바꾸지 못하고, 자체 CodeQL workflow를 쓰는 저장소와 default setup이 부딪친다 |
| Settings → Member privileges | 저장소 만들기(Public, Private), 공개 여부 변경, 삭제와 이전, 저장소 관리자의 GitHub App 설치, 팀 만들기를 모두 끈다. 기본 권한은 Read로 둔다 | 초대한 멤버가 저장소, 규칙, 연결된 App을 바꾸지 못하게 소유자만 한다. Public은 Private을 끈 뒤에야 끌 수 있다 |
| Settings → Actions → General | 외부 기여자 workflow 승인은 Require approval for all external contributors, Workflow permissions는 Read, Allow GitHub Actions to create and approve pull requests는 끈다 | 새 저장소가 물려받는 값을 저장소 기준값(`fork_policy`, `workflow_token`)과 맞춘다 |
| Settings → Authentication security | Require two-factor authentication을 켠다 | 켜기 전에 People → Outside collaborators를 본다. 2FA가 없는 외부 협력자는 조직에서 빠진다 |
| People | 소유자의 멤버십을 Public으로 둔다 | 개인 프로필에 조직이 보인다 |

저장소를 조직으로 옮기는 절차는 「(b) 기존 저장소 옮기기」의 1이다.

멤버 권한과 2FA는 `read:org` 권한으로 읽어 확인한다. 나머지 조직 설정은 `admin:org` 권한이 필요해 화면에서 본다.

```sh
gh api orgs/<조직> --jq '{members_can_create_public_repositories, members_can_create_private_repositories, members_can_change_repo_visibility, members_can_delete_repositories, members_can_create_teams, two_factor_requirement_enabled}'
```

## 필수 체크 계약

- 필수 체크 이름과 트리거는 「계약 값」의 값이다. `merge_group` 실행에는 `github.event.pull_request`와 `github.head_ref`가 없다. 필수 체크가 `merge_group`에서 돌지 않으면 큐에 넣은 PR이 병합되지 않는다.
- 세부 job을 나누면 `ci` job이 `needs`로 모두 기다린다. `if: always()`를 붙여 세부 job이 실패해도 판정 job이 돌게 한다. 판정 job은 모든 `needs.*.result`가 `success`일 때만 통과한다. `if: always()`만 있고 결과를 보지 않으면 세부 job이 실패해도 통과한다.
- PR 브랜치에 base를 합치지 않는다. 리뷰한 SHA로 큐에 넣는다(POLICY §5).

```yaml
  ci:
    name: ci
    needs: [lint, test]
    if: always()
    runs-on: ubuntu-24.04
    steps:
      - name: every job succeeded
        env:
          RESULTS: ${{ join(needs.*.result, ' ') }}
        run: for r in $RESULTS; do [ "$r" = success ] || { echo "a job ended with $r"; exit 1; }; done
```

필수 체크를 하나로 두면 세부 job을 더하거나 이름을 바꿔도 저장소 설정을 바꾸지 않는다. `ci.yml` 템플릿은 job이 하나뿐이라 그 job이 판정 job이다.

## 저장소 설정 파일

`apply_github_settings.py`와 `check_github_settings.py`는 이 폴더의 `repository-settings.json`을 공통값으로 읽는다. 저장소의 `.github/repository-settings.json`은 그 위에 얹는다. 두 도구는 공통값을 읽은 파일 경로를 `BASELINE:` 줄로 출력한다.

- 객체는 키마다 합친다. 저장소 파일에 값이 있으면 그 값이 이긴다. 목록(`checks`, `patterns_allowed`, `rulesets`)은 통째로 바뀐다.
- 저장소 파일에는 저장소마다 다른 값만 둔다: `repository`, `repository_id`, 필수 체크 `context`, `patterns_allowed`, 필요하면 `exceptions`. 템플릿과 일부러 다르게 둔 값도 남긴다. 예: 기본 브랜치가 `main`이 아니면 `default_branch`와 `expected.repository.default_branch`, CodeQL advanced setup이면 `expected.codeql.state`(`not-configured`)와 `expected.codeql_workflow`. 지우면 템플릿 값을 받아 계획이 그 값으로 바꾸려 한다. 공통값을 바꾸려면 저장소마다 PR을 내지 않고 이 템플릿을 바꾸는 PR 하나를 낸다.
- `exceptions`에 적은 경로는 공통값에서 빠진다.
- 저장소 파일에서 빠진 값이 템플릿의 `REPLACE` 값이면 도구는 조회 전에 멈춘다.
- 템플릿 전체를 복사한 기존 파일도 그대로 통과한다. 다만 그 파일의 값이 이기므로, 공통값(예: `strict`)이 바뀌어도 그 저장소에는 적용되지 않는다. 공통값을 따르려면 파일을 아래처럼 줄인다.

```json
{
  "repository": "OWNER/NAME",
  "repository_id": 123456789,
  "expected": {
    "protection": {"required_status_checks": {"checks": [{"context": "ci", "app_id": 15368}]}},
    "allowed_actions": {"patterns_allowed": []}
  }
}
```

### 클론 맞추기와 재적용

공통값이 바뀌면 소유자가 저장소마다 계획을 보고 적용한다. 도구는 실행한 repo-baseline 클론의 템플릿을 읽으므로 먼저 클론을 upstream과 같고 변경이 없는 `main`으로 맞춘다. 아래 명령은 어느 조건이든 어긋나면 계획을 돌리지 않는다.

```sh
git -C <repo-baseline> switch main &&
git -C <repo-baseline> pull --ff-only &&
[ -z "$(git -C <repo-baseline> status --porcelain --untracked-files=all)" ] &&
[ "$(git -C <repo-baseline> rev-parse HEAD)" = "$(git -C <repo-baseline> rev-parse '@{u}')" ] &&
for p in <project-1> <project-2>; do
  python3 <repo-baseline>/tools/apply_github_settings.py "$p"
done
```

계획을 승인한 저장소만 `--apply`를 붙여 다시 실행하고 `PASS`를 본다.

### 결정 근거

- `strict`를 끈다(2026-11-16). 머지 큐는 최신 base와 앞선 큐 항목을 합친 결과로 필수 CI를 다시 돌린다. [문서](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue)는 큐가 「Require branches to be up to date」와 같은 이점을 주되 작성자에게 브랜치 업데이트를 요구하지 않는다고 쓴다. strict를 꺼야 한다고 쓰지는 않는다(2026-11-16 확인). strict를 켜 두면 base가 움직일 때마다 PR head를 바꿔야 하고, head가 바뀌면 다시 리뷰한다(POLICY §5).
- 공통값을 템플릿에 모은다(2026-11-16). 그날 한 조직의 저장소 셋이 모두 템플릿 전체를 복사해 strict 같은 공통값을 저장소마다 들고 있었다. 정책 하나를 바꾸려면 저장소 수만큼 PR이 필요했다. 셋 모두 `merge-queue` ruleset(squash, ALLGREEN, 최대 5), `strict: true`, `allow_auto_merge: false`, `delete_branch_on_merge: true`를 썼다.
- 조직 ruleset은 쓰지 않는다. 2026-11-16 무료 조직의 설정 화면에 「Organization rulesets won't be enforced until you upgrade this organization account to GitHub Team」이 떴다. 조직은 무료 플랜을 유지하고 공통값은 이 템플릿에 둔다.

## CodeRabbit 설정

`.coderabbit.yaml`은 리뷰 언어를 한국어(`ko-KR`, 기본값 `en-US`)로 정한다. 근거 문서와 확인일은 파일 주석에 있다. `inheritance: true`가 있어서 이 파일에 없는 키는 바로 아래 설정 단계를 따른다. Central YAML(`coderabbit` 저장소의 설정)이 없으면 CodeRabbit 웹 설정이다. 그 단계에 `inheritance`가 없으면 상속은 거기서 멈춘다. 이 파일에 `inheritance: true`가 없으면 웹 설정 대신 기본값이 쓰인다. 요약·채팅 답글까지 한국어가 되는지는 확인하지 못했다. 이 파일은 저장소마다 다른 값이 없어 「계약 값」 표에 넣지 않는다. 그 표는 GitHub 설정 값이고, 이 파일은 파일 자체가 정본이다. 새 저장소는 (a)의 3에서, 기존 저장소는 (b)의 5에서 함께 복사한다. 따로 더하거나 공통값이 바뀌었으면 아래를 한다. 어느 쪽이든 병합한 뒤 3으로 확인한다.

1. 에이전트: 파일을 넣어 PR로 연다. 리뷰는 POLICY §3대로 한다.
   - 저장소 루트에 `.coderabbit.yml`이나 `.coderabbit.config.ts`가 있으면 아무것도 넣지 않고 PR 본문에 적어 소유자에게 남긴다. YAML 파일이 있으면 CodeRabbit은 `.coderabbit.config.ts`를 무시한다([configuration-overview](https://docs.coderabbit.ai/guides/configuration-overview), 2026-11-16 확인).
   - 저장소 루트에 CodeRabbit 설정 파일이 하나도 없으면 그대로 복사한다.

     ```sh
     cp <repo-baseline>/templates/github/.coderabbit.yaml <project>/.coderabbit.yaml
     cmp <repo-baseline>/templates/github/.coderabbit.yaml <project>/.coderabbit.yaml
     ```

     확인: `cmp`가 아무것도 출력하지 않고 종료 코드 0이다.
   - `.coderabbit.yaml`이 이미 있으면 파일 전체를 복사하지 않는다. 그 파일에 `language: "ko-KR"` 줄만 합친다. 원래 `language` 줄이 있으면 그 줄을 바꾼다. 합친 사실을 PR 본문에 적는다.

     ```sh
     grep -qx 'language: "ko-KR"' <project>/.coderabbit.yaml
     ```

     확인: 종료 코드 0이다.
2. 소유자: diff를 읽고 병합한다(POLICY §5).
3. 에이전트: 그다음 PR에서 CodeRabbit 리뷰가 한국어인지 본다.

   확인: CodeRabbit의 줄 단위 댓글 본문이 한국어다. 영어면 CodeRabbit 웹의 조직 global override에 `language`가 있는지 소유자가 본다. 그 값이 저장소 YAML보다 우선한다.

공통값을 바꾸려면 저장소마다 PR을 내지 않고 이 템플릿을 바꾼 뒤 위 1~3을 다시 한다.

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
