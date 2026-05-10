from decimal import Decimal

from app.services.acb import AcbResult, apply_buy, apply_sell


def test_average_cost_method():
    state = AcbResult()
    apply_buy(state, Decimal("10"), Decimal("1000"))
    apply_buy(state, Decimal("10"), Decimal("1500"))
    assert state.acb_per_unit == Decimal("125")


def test_realized_gain():
    state = AcbResult()
    apply_buy(state, Decimal("10"), Decimal("1000"))
    apply_buy(state, Decimal("10"), Decimal("1500"))
    apply_sell(state, Decimal("5"), Decimal("800"))
    assert state.realized_gain_cad == Decimal("175")
    assert state.quantity == Decimal("15")


def test_oversell_raises():
    state = AcbResult()
    apply_buy(state, Decimal("5"), Decimal("500"))
    try:
        apply_sell(state, Decimal("10"), Decimal("1000"))
    except ValueError:
        return
    raise AssertionError("expected ValueError")
