import json
import tempfile
import unittest
from pathlib import Path

from turath_inveniordm.cantaloupe_mirror import (
    DEFAULT_PAGE_HEIGHT,
    DEFAULT_PAGE_WIDTH,
    create_dimensions_cache_from_hocr_dir,
    get_hocr_page_dimensions,
)


class TestCantaloupeMirror(unittest.TestCase):
    def test_get_hocr_page_dimensions_with_valid_bbox_returns_dimensions(self):
        hocr_content = (
            "<div class='ocr_page' title='bbox 0 0 1380 2058'></div>"
        )

        dims = get_hocr_page_dimensions(hocr_content)

        self.assertEqual(dims, (1380, 2058))

    def test_get_hocr_page_dimensions_with_missing_bbox_returns_none(self):
        hocr_content = "<div class='ocr_page'></div>"

        dims = get_hocr_page_dimensions(hocr_content)

        self.assertIsNone(dims)

    def test_create_dimensions_cache_from_hocr_dir_writes_json_in_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            hocr_dir = tmp_path / "hocr"
            hocr_dir.mkdir(parents=True, exist_ok=True)
            (hocr_dir / "001.hocr").write_text(
                "<div class='ocr_page' title='bbox 0 0 100 200'></div>",
                encoding="utf-8",
            )
            (hocr_dir / "002.hocr").write_text(
                "<div class='ocr_page' title='bbox 0 0 300 400'></div>",
                encoding="utf-8",
            )
            output_file = tmp_path / "dimensions.json"

            dims = create_dimensions_cache_from_hocr_dir(hocr_dir, output_file)

            self.assertTrue(output_file.exists())
            self.assertEqual(dims, [{"w": 100, "h": 200}, {"w": 300, "h": 400}])
            loaded = json.loads(output_file.read_text(encoding="utf-8"))
            self.assertEqual(loaded, dims)

    def test_create_dimensions_cache_from_hocr_dir_with_no_hocr_creates_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            hocr_dir = tmp_path / "hocr"
            hocr_dir.mkdir(parents=True, exist_ok=True)
            output_file = tmp_path / "dimensions.json"

            dims = create_dimensions_cache_from_hocr_dir(hocr_dir, output_file)

            self.assertEqual(
                dims,
                [{"w": DEFAULT_PAGE_WIDTH, "h": DEFAULT_PAGE_HEIGHT}],
            )
            loaded = json.loads(output_file.read_text(encoding="utf-8"))
            self.assertEqual(loaded, dims)


if __name__ == "__main__":
    unittest.main()
