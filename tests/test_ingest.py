import hashlib
import tempfile
import unittest
from pathlib import Path

from src.ingest import sha256


class Sha256Tests(unittest.TestCase):
    def test_sha256_matches_known_value(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.txt"
            path.write_bytes(b"Queensland road safety\n")
            expected = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(sha256(path), expected)


if __name__ == "__main__":
    unittest.main()
