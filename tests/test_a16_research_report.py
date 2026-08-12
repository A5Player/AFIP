from afip.exit_evidence_research import A16PolicyRanking, build_a16_research_report
def ranking(policy, rank): return A16PolicyRanking(policy,30,.5,.6,1,.4,.2,rank)
def test_report_is_read_only_and_orders_rankings():
    report=build_a16_research_report([ranking("B",2),ranking("A",1)])
    assert report.status=="READY" and report.read_only and report.execution_authority=="NONE"
    assert [x["policy_id"] for x in report.rankings]==["A","B"]
def test_empty_report_waits_for_evidence():
    report=build_a16_research_report([])
    assert report.status=="WAIT" and report.reason=="minimum_research_sample_not_met"
