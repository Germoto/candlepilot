from candlepilot.indicators import ema, rsi


def test_ema_returns_series():
    values = [1,2,3,4,5,6,7,8,9,10]
    result = ema(values, 3)
    assert len(result) == len(values) - 3 + 1
    assert result[-1] > result[0]


def test_rsi_uptrend_is_high():
    values = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16]
    assert rsi(values, 14) > 70
