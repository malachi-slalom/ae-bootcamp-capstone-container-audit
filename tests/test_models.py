from src.models import Applicability, Finding, Severity, to_dict


def test_to_dict_serializes_enums() -> None:
    finding = Finding(
        finding_id="demo",
        title="Demo",
        severity=Severity.LOW,
        evidence="evidence",
        applicability=Applicability.APPLICABLE,
        recommendation="review",
    )

    serialized = to_dict(finding)

    assert serialized["severity"] == "low"
    assert serialized["applicability"] == "applicable"