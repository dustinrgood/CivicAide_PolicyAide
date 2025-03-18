import asyncio

from civicaide.policy_analysis import run_policy_analysis


def test_policy_analysis():
    query = "Analyze the impact of a recent policy change in local education funding."
    report = asyncio.run(run_policy_analysis(query))
    assert isinstance(report, str) and len(report) > 0, "Report should be a non-empty string"
    print("Test passed: policy analysis produced output.")


if __name__ == "__main__":
    test_policy_analysis() 