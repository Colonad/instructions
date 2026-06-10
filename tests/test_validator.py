from labelguard.models import ApplicationData, Status
from labelguard.validator import GOVERNMENT_WARNING_EXACT, verify_label_text


def app_data(**overrides):
    base = dict(
        brand_name="OLD TOM DISTILLERY",
        class_type="Kentucky Straight Bourbon Whiskey",
        alcohol_content="45% Alc./Vol. (90 Proof)",
        net_contents="750 mL",
        producer_name_address="Old Tom Distillery, Louisville, KY",
    )
    base.update(overrides)
    return ApplicationData(**base)


def test_perfect_label_passes():
    text = "\n".join(
        [
            "OLD TOM DISTILLERY",
            "Kentucky Straight Bourbon Whiskey",
            "45% Alc./Vol. (90 Proof)",
            "750 mL",
            "Old Tom Distillery, Louisville, KY",
            GOVERNMENT_WARNING_EXACT,
        ]
    )
    report = verify_label_text("ok.txt", app_data(), text)
    assert report.overall_status == Status.PASS
    assert all(check.status == Status.PASS for check in report.checks)


def test_case_only_brand_change_is_not_automatic_failure():
    text = "\n".join(
        [
            "Old Tom Distillery",
            "Kentucky Straight Bourbon Whiskey",
            "45% Alcohol by Volume",
            "750 ml",
            "Old Tom Distillery, Louisville, KY",
            GOVERNMENT_WARNING_EXACT,
        ]
    )
    report = verify_label_text("case.txt", app_data(), text)
    brand = next(check for check in report.checks if check.field == "Brand Name")
    assert brand.status in {Status.PASS, Status.REVIEW}


def test_bad_government_warning_fails_even_if_similar():
    text = "\n".join(
        [
            "OLD TOM DISTILLERY",
            "Kentucky Straight Bourbon Whiskey",
            "45% Alc./Vol.",
            "750 mL",
            "Old Tom Distillery, Louisville, KY",
            "Government Warning: According to doctors, pregnant women should avoid alcohol. Alcohol may impair driving.",
        ]
    )
    report = verify_label_text("bad-warning.txt", app_data(), text)
    warning = next(check for check in report.checks if check.field == "Government Health Warning")
    assert warning.status == Status.FAIL
    assert report.overall_status == Status.FAIL


def test_proof_can_satisfy_abv():
    text = "\n".join(
        [
            "OLD TOM DISTILLERY",
            "Kentucky Straight Bourbon Whiskey",
            "90 Proof",
            "750 mL",
            "Old Tom Distillery, Louisville, KY",
            GOVERNMENT_WARNING_EXACT,
        ]
    )
    report = verify_label_text("proof.txt", app_data(), text)
    abv = next(check for check in report.checks if check.field == "Alcohol Content")
    assert abv.status == Status.PASS


def test_net_contents_mismatch_fails():
    text = "\n".join(
        [
            "OLD TOM DISTILLERY",
            "Kentucky Straight Bourbon Whiskey",
            "45% Alc./Vol.",
            "375 mL",
            "Old Tom Distillery, Louisville, KY",
            GOVERNMENT_WARNING_EXACT,
        ]
    )
    report = verify_label_text("bad-size.txt", app_data(), text)
    net = next(check for check in report.checks if check.field == "Net Contents")
    assert net.status == Status.FAIL
