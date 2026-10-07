"""Download public Marble example exports into data/marble_examples/ and verify SHA-256.

World Labs assets are NOT redistributed in this repository; this script fetches them from the
public locations listed at https://docs.worldlabs.ai/marble/export/specs. Check World Labs'
terms before reuse; no licence is stated for these files. Usage: python scripts/fetch_data.py [--force]
"""
import hashlib
import pathlib
import sys
import urllib.request

BASE = "https://wlt-ai-cdn.art/example_exports"
ROOT = pathlib.Path(__file__).resolve().parents[1] / "data" / "marble_examples"

# name -> {suffix: sha256}; hashes recorded 2026-10-02
FILES = {
    "elegant_library_with_fireplace": {
        "_500k.spz": "c89fb6606929faf7cefcf2577f54fa141b1bceaf55af070d54f7b986fab96870",
        "_collider.glb": "813c622312de2cc2abfd107d55430c660a015e4c070cd12b510cf4de2f508c05",
        "_pano.png": "b6bcda4d02c5c2ca84f593b7626e18ec085898f21a9baac7e9e5017ebebd2e60"},
    "modern_house_with_lush_landscaping": {
        "_500k.spz": "932b7df6059b271f1573e24334116d8d4e1321c3f99f177dfe8ce629834a620e",
        "_collider.glb": "a9ab04ad30947f85000fad460f7bcf7488dfb4b995a449a4124342c4b53d5467"},
    "narrow_european_cobblestone_lane": {
        "_500k.spz": "f9133e75d4fa9c122e1d036b204042a8e164d5d06f635069e1480e3dcf75e099",
        "_collider.glb": "08e75e0ad55ceea8ba9305bd1845749b741ca4337cda240e5a35253449eb00c9",
        "_pano.png": "e6772fbd49df9456e174e397eb07a01f4f690183b8709cc1307a4cb23d821fdf"},
    "rustic_kitchen_with_natural_light": {
        "_500k.spz": "351f5f2ceb6ee9095a4b4100f864db9780a21cc6bdb8a70c6f88117cbb1d5fe0",
        "_collider.glb": "38b9f692edeb671b7106f3e36cfe7f4c55be20e98fe90c014a8714b09874f6fa",
        "_pano.png": "bfbc06994ff0ca492b486b3d270f3196fb6b1fb103c7e836a648af8946c8d16c"},
    "warm_traditional_kitchen_interior": {
        "_500k.spz": "93de2e34f8c34f9118e37895701b39a15ef51a0b16469c49e3f8412d185475f9",
        "_collider.glb": "4f40f384f245683e6d23aa42231896071570a438ae0c39fd4dc330eed8c1a72c",
        "_pano.png": "6de2befd56823ef9fa0d7775e2b620fa6a16aca7f3f410df56aa30f31882a324"},
}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main(force=False):
    ROOT.mkdir(parents=True, exist_ok=True)
    bad = 0
    for world, parts in FILES.items():
        for suffix, digest in parts.items():
            dst = ROOT / f"{world}{suffix}"
            if force or not dst.exists():
                url = f"{BASE}/{world}/{world}{suffix}"
                print("downloading", url)
                urllib.request.urlretrieve(url, dst)
            ok = sha256(dst) == digest
            bad += not ok
            print(("ok       " if ok else "MISMATCH ") + dst.name)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main("--force" in sys.argv)
