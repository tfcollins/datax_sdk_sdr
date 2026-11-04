from datax_support.check import check_manifest


def test_check_accepts_fixture(fix, tmp_repo):
    assert check_manifest(fix / "tick.support.json", tmp_repo) == []


def test_check_rejects_unknown_feature_slug(fix, tmp_repo):
    errs = check_manifest(fix / "bad-feature.json", tmp_repo)
    assert any("unknown feature 'timed-gpoi'" in e for e in errs)


def test_check_validated_requires_tier_ge_2(fix, tmp_repo):
    errs = check_manifest(fix / "bad-tier.json", tmp_repo)
    assert any("tier >= 2" in e for e in errs)


def test_check_missing_workflow_names_file(fix, tmp_repo):
    errs = check_manifest(fix / "bad-workflow.json", tmp_repo)
    assert any("nope.yml" in e for e in errs)


def test_check_rejects_run_url(fix, tmp_repo):
    errs = check_manifest(fix / "bad-run-url.json", tmp_repo)
    assert any("workflow run or artifact" in e for e in errs)


def test_check_integration_artifacts_requires_evidence(fix, tmp_repo):
    errs = check_manifest(fix / "bad-ia-no-evidence.json", tmp_repo)
    assert any("evidence" in e for e in errs)


def test_check_planned_allows_no_tier(fix, tmp_repo):
    assert check_manifest(fix / "planned-only.json", tmp_repo) == []


def test_check_software_only_allows_tier_1(fix, tmp_repo):
    assert check_manifest(fix / "software-only.support.json", tmp_repo) == []
    errs = check_manifest(fix / "bad-software-tier.json", tmp_repo)
    assert any("tier >= 2" in e for e in errs)


def test_check_rejects_tier_on_planned_row(fix, tmp_repo):
    errs = check_manifest(fix / "bad-planned-tier.json", tmp_repo)
    assert any("planned" in e and "tier" in e for e in errs)
