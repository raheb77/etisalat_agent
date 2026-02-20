import os
from pathlib import Path


os.environ["APP_ENV"] = "test"

fixture_dir = Path(__file__).resolve().parent / "fixtures" / "facts"
os.environ["FACTS_DIR"] = str(fixture_dir)
