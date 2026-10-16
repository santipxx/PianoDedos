import unittest

from core import NOTES
from rhythm import MusicTile, RhythmGame, jingle_bells


class TestJingleBells(unittest.TestCase):
    def test_sus_notas_caben_en_las_10_teclas(self):
        tiles = jingle_bells()
        self.assertGreaterEqual(len(tiles), 45)
        self.assertTrue(all(t.note in NOTES for t in tiles))
        self.assertEqual([t.note for t in tiles[:3]], ["E4"] * 3)
        self.assertIn("G4", [t.note for t in tiles])
        self.assertIn("C4", [t.note for t in tiles])

    def test_tiempos_ordenados_y_duracion(self):
        tiles = jingle_bells(105)
        self.assertAlmostEqual(tiles[0].at, 0.0)
        self.assertEqual(sorted(t.at for t in tiles), [t.at for t in tiles])
        self.assertTrue(all(t.duration > 0 for t in tiles))
        self.assertGreater(tiles[-1].at, 30.0)

    def test_velocidad_controla_tempo(self):
        normal = jingle_bells(100)
        lenta = jingle_bells(50)
        self.assertAlmostEqual(lenta[10].at, normal[10].at * 2)
        for bpm in (0, 39, 201):
            with self.assertRaises(ValueError):
                jingle_bells(bpm)

    def test_acierto_en_ventana_correcta(self):
        game = RhythmGame((MusicTile("E4", 2.0, 0.5),))
        self.assertEqual(game.press("E4", 2.0), "PERFECT")
        self.assertIsNone(game.press("E4", 2.0))
        self.assertEqual(game.score, 100)
        self.assertEqual(game.hits, 1)
        self.assertEqual(game.accuracy(), 100.0)

    def test_diferentes_juicios_y_combo(self):
        game = RhythmGame((MusicTile("C4", 1, 0.5),
                           MusicTile("D4", 2, 0.5),
                           MusicTile("E4", 3, 0.5)))
        self.assertEqual(game.press("C4", 1.15), "GOOD")
        self.assertEqual(game.press("D4", 2.26), "OK")
        self.assertEqual(game.press("E4", 3.01), "PERFECT")
        self.assertEqual(game.score, 70 + 40 + 100)
        self.assertEqual(game.best_combo, 3)
        self.assertEqual(game.misses, 0)

    def test_notas_repetidas_cuentan_separadamente(self):
        game = RhythmGame((MusicTile("E4", 0, 0.2),
                           MusicTile("E4", 0.6, 0.2)))
        self.assertEqual(game.press("E4", 0.01), "PERFECT")
        self.assertEqual(game.press("E4", 0.6), "PERFECT")
        self.assertEqual(game.hits, 2)

    def test_nota_fuera_de_tiempo_y_miss(self):
        game = RhythmGame((MusicTile("F4", 1, 0.3),
                           MusicTile("G4", 2, 0.3)))
        self.assertIsNone(game.press("F4", 0))
        game.update(1.32)
        self.assertEqual(game.misses, 1)
        self.assertEqual(game.results[0], "MISS")
        self.assertEqual(game.press("G4", 2), "PERFECT")
        self.assertEqual(game.accuracy(), 50.0)
        self.assertTrue(game.finished(3.2))


if __name__ == "__main__":
    unittest.main()
