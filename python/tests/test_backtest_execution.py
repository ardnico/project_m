from fxbot.backtest.execution import ExecutionModel, LatencyProfile, VolatilityScaledSlippage


def test_effective_price_and_latency():
    model = ExecutionModel(
        slippage=VolatilityScaledSlippage(base=0.1, vol_factor=0.05),
        latency=LatencyProfile(p50=80, p95=120, p99=200),
        rejection_rate={"tokyo": 0.01, "london": 0.05},
    )

    assert model.effective_price(100.0, volatility=0.2, side="BUY") == 100.0 + 0.1 + 0.2 * 0.05
    assert model.effective_price(100.0, volatility=0.2, side="SELL") == 100.0 - (0.1 + 0.2 * 0.05)
    assert model.expected_latency(0.5) == 80
    assert model.expected_latency(0.8) == 120
    assert model.expected_latency(0.99) == 200
