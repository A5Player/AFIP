from afip.research_ranking import RankingPolicy, ResearchRankingEngine

def row(name, win, dd, expectancy=2, pf=1.5, recovery=2, stability=80):
    return {"research_id": name, "win_rate_percentage": win, "maximum_drawdown_percentage": dd,
            "expectancy": expectancy, "profit_factor": pf, "recovery_factor": recovery,
            "stability_score": stability, "trade_count": 100, "out_of_sample_windows": 3}

def test_high_win_rate_does_not_override_drawdown_limit():
    engine = ResearchRankingEngine(RankingPolicy(maximum_drawdown_percentage=20))
    assert engine.classify(row("high_win_high_dd", 95, 35)) == "QUARANTINED"

def test_lower_win_rate_can_rank_when_drawdown_is_controlled():
    engine = ResearchRankingEngine()
    report = engine.rank([row("unsafe", 95, 35), row("stable", 65, 5)])
    assert report["top_overall"][0]["research_id"] == "stable"

def test_insufficient_evidence_is_not_ranked():
    engine = ResearchRankingEngine()
    item = row("small", 80, 2)
    item["trade_count"] = 5
    assert engine.classify(item) == "INSUFFICIENT_EVIDENCE"

def test_deterministic_tie_order():
    engine = ResearchRankingEngine()
    report = engine.rank([row("b", 60, 5), row("a", 60, 5)])
    assert [x["research_id"] for x in report["top_overall"]] == ["a", "b"]
