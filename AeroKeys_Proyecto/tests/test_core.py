import unittest
from types import SimpleNamespace

from core import GestureGate, Melody, joint_angle, note_frequency


class TestPiano(unittest.TestCase):
    def test_tuning(self):
        self.assertAlmostEqual(note_frequency("A4"), 440.0, places=5)
        self.assertAlmostEqual(note_frequency("C5"), 523.251, places=2)

    def test_angle(self):
        self.assertAlmostEqual(joint_angle((-1, 0), (0, 0), (1, 0)), 180.0)
        self.assertAlmostEqual(joint_angle((-1, 0), (0, 0), (0, 1)), 90.0)

    def test_media_pipe_landmarks(self):
        # MediaPipe entrega objetos con propiedades .x y .y, no tuplas.
        p = lambda x, y: SimpleNamespace(x=x, y=y)
        self.assertAlmostEqual(joint_angle(p(-1, 0), p(0, 0), p(1, 0)), 180.0)

    def test_gesture_debounce(self):
        gate = GestureGate(frames=2)
        key = ("Right", "index")
        self.assertNotIn(key, gate.update({key}))
        self.assertIn(key, gate.update({key}))
        self.assertIn(key, gate.update(set()))
        self.assertNotIn(key, gate.update(set()))

    def test_melody(self):
        melody = Melody(beat_seconds=1.0)
        self.assertEqual(melody.at(0.01)[0], "E4")
        self.assertIsNone(melody.at(0.95)[0])
        self.assertEqual(melody.at(2.0)[0], "F4")


if __name__ == "__main__":
    unittest.main()
