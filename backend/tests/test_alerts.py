from app.services.alerts import evaluate_alerts


def test_high_score_triggers_critical():
    alerts = evaluate_alerts(
        composite_score=80, regime="elevated",
        concentration={"hhi": 0.10, "top": [], "by_sector": {}},
        stress_results={"covid_2020": -0.20},
    )
    cats = {a.category for a in alerts}
    assert "risk_score" in cats
    assert any(a.severity == "critical" for a in alerts if a.category == "risk_score")


def test_concentration_single_name_alert():
    alerts = evaluate_alerts(
        composite_score=20, regime="normal",
        concentration={
            "hhi": 0.05,
            "top": [{"symbol": "MSFT", "weight": 0.25}],
            "by_sector": {},
        },
        stress_results={"covid_2020": -0.10},
    )
    titles = [a.title for a in alerts]
    assert any("MSFT" in t for t in titles)


def test_no_false_positives_when_clean():
    alerts = evaluate_alerts(
        composite_score=30, regime="normal",
        concentration={"hhi": 0.10, "top": [{"symbol": "VEQT", "weight": 0.10}], "by_sector": {"diversified": 0.5}},
        stress_results={"covid_2020": -0.18},
    )
    severities = [a.severity for a in alerts]
    assert "critical" not in severities
