import pathlib, sys, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "tools"))
import twb_inspector as ti

class T(unittest.TestCase):
    def test_fixture(self):
        info = ti.inspect(pathlib.Path(__file__).parent / "fixture_tableau_charts.twb")
        kinds = {s["name"]: s["kind"] for s in info["sheets"]}
        self.assertEqual(kinds, {"Heatmap": "Highlight table / heatmap", "Bubbles": "Packed bubbles", "Treemap": "Treemap",
                                 "DualAxis": "Dual axis / combo", "Scatter": "Scatter", "BoxPlot": "Box-and-whisker"})
        self.assertEqual([c[0] for c in info["calcs"]], ["Profit Ratio", "Tỷ lệ đạt"])
        self.assertEqual(info["dashboards"], ["Tổng quan"])

if __name__ == "__main__":
    unittest.main()
