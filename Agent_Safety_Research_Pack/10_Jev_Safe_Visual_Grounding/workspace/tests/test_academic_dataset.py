import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "academic_2000"


def rows():
    return [json.loads(x) for x in (DATA / "manifest.jsonl").read_text().splitlines() if x.strip()]


def test_academic_manifest_counts_and_ids():
    data = rows()
    assert len(data) == 2000
    assert len({r["case_id"] for r in data}) == 2000
    assert Counter(r["source_dataset"] for r in data) == {
        "ScreenSpot-v2-variants": 1500,
        "ImageJevBench Box public v0.1": 300,
        "Jev safe GUI grounding synthetic pilot": 200,
    }


def test_boxes_are_valid_and_absent_candidates_have_none():
    for row in rows():
        for box in row["ground_truth_boxes_norm"]:
            x1, y1, x2, y2 = box
            assert x1 < x2 and y1 < y2
            if row["target_status"] != "offscreen":
                assert 0 <= x1 < x2 <= 1
                assert 0 <= y1 < y2 <= 1
        if row["target_status"] == "absent_candidate":
            assert row["ground_truth_boxes_norm"] == []
            assert row["reference_action"] == "abstain"
            assert row["human_review_required"] is True


def test_screen_pairs_do_not_cross_proposed_splits():
    data = {r["case_id"]: r for r in rows()}
    for row in data.values():
        pair = row.get("paired_case_id")
        if pair:
            assert data[pair]["proposed_split"] == row["proposed_split"]
            assert data[pair]["image_group_id"] == row["image_group_id"]


def test_auxiliary_counterfactual_count():
    import csv
    with (DATA / "counterfactual_candidates.csv").open(newline="", encoding="utf-8") as f:
        assert len(list(csv.DictReader(f))) == 66
