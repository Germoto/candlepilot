from pathlib import Path

from candlepilot.reporting import write_json, write_trades_csv


def test_reporting_writes_files(tmp_path: Path):
    write_json(tmp_path / "a.json", {"ok": True})
    write_trades_csv(tmp_path / "b.csv", [{"entry_time": "x", "result_pips": 1.2}])
    assert (tmp_path / "a.json").exists()
    assert (tmp_path / "b.csv").exists()
