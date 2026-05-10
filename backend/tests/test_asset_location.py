from app.services.asset_location import HoldingPlacement, recommend_placement


def test_us_dividend_to_rrsp():
    holdings = [
        HoldingPlacement(symbol="MSFT", asset_class="equity", sector="tech",
                         region="us", is_dividend_payer=True,
                         current_account_type="non_reg"),
    ]
    suggestions = recommend_placement(holdings)
    assert len(suggestions) == 1
    assert suggestions[0].recommended_account_type == "rrsp"


def test_canadian_dividend_to_non_reg():
    holdings = [
        HoldingPlacement(symbol="ENB.TO", asset_class="equity", sector="energy",
                         region="ca", is_dividend_payer=True,
                         current_account_type="tfsa"),
    ]
    suggestions = recommend_placement(holdings)
    assert suggestions[0].recommended_account_type == "non_reg"


def test_already_optimal_no_suggestion():
    holdings = [
        HoldingPlacement(symbol="MSFT", asset_class="equity", sector="tech",
                         region="us", is_dividend_payer=True,
                         current_account_type="rrsp"),
    ]
    assert recommend_placement(holdings) == []
