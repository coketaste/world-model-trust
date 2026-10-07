import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_site_data_builds_and_parses(tmp_path):
    subprocess.run([sys.executable, str(ROOT / "scripts" / "build_site_data.py"), "--out", str(tmp_path)], check=True, capture_output=True)
    text = (tmp_path / "data.js").read_text()
    committed = (ROOT / "site" / "assets" / "data.js").read_text()
    assert text == committed, "site/assets/data.js is stale: run scripts/build_site_data.py"
    assert text.startswith("window.WMT = ") and text.rstrip().endswith(";")
    data = json.loads(text[len("window.WMT = "):].rstrip().rstrip(";"))
    assert len(data["wp0"]["cases"]) == 12
    assert len(data["wp3"]["cells"]) == 1080
    assert set(data["wp1"]) >= {"preregistered", "amended"}
