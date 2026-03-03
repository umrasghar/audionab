"""Tests for audionab.database — no GUI or FFmpeg required."""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audionab.database import HistoryDB


class TestHistoryDB:
    def setup_method(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db = HistoryDB(self.tmp.name)

    def teardown_method(self):
        try:
            self.db.conn.close()
        except Exception:
            pass
        try:
            os.unlink(self.tmp.name)
            # Also clean WAL/SHM files
            for ext in ("-wal", "-shm"):
                p = self.tmp.name + ext
                if os.path.exists(p):
                    os.unlink(p)
        except Exception:
            pass

    def test_empty_stats(self):
        stats = self.db.get_stats()
        assert stats["total"] == 0
        assert stats["success"] == 0
        assert stats["failed"] == 0
        assert stats["total_input"] == 0
        assert stats["total_output"] == 0

    def test_add_conversion(self):
        # Create a temp file to use as source
        src = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        src.write(b"fake video data")
        src.close()
        try:
            row_id = self.db.add_conversion(src.name, "/tmp/out.mp3", "192k")
            assert row_id == 1
            assert self.db.get_stats()["total"] == 1
        finally:
            os.unlink(src.name)

    def test_update_conversion(self):
        src = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        src.write(b"x" * 100)
        src.close()
        try:
            row_id = self.db.add_conversion(src.name, "/tmp/out.mp3")
            self.db.update_conversion(row_id, status="success", output_size=50)

            stats = self.db.get_stats()
            assert stats["success"] == 1
            assert stats["total_output"] == 50
        finally:
            os.unlink(src.name)

    def test_get_history(self):
        src = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        src.write(b"data")
        src.close()
        try:
            self.db.add_conversion(src.name, "/tmp/a.mp3")
            self.db.add_conversion(src.name, "/tmp/b.mp3")
            rows = self.db.get_history()
            assert len(rows) == 2
            # Most recent first
            assert rows[0]["output_name"] == "b.mp3"
        finally:
            os.unlink(src.name)

    def test_delete_entry(self):
        src = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        src.write(b"data")
        src.close()
        try:
            row_id = self.db.add_conversion(src.name, "/tmp/out.mp3")
            self.db.delete_entry(row_id)
            assert self.db.get_stats()["total"] == 0
        finally:
            os.unlink(src.name)

    def test_clear_history(self):
        src = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        src.write(b"data")
        src.close()
        try:
            self.db.add_conversion(src.name, "/tmp/a.mp3")
            self.db.add_conversion(src.name, "/tmp/b.mp3")
            self.db.clear_history()
            assert self.db.get_stats()["total"] == 0
            assert self.db.get_history() == []
        finally:
            os.unlink(src.name)

    def test_wal_mode_enabled(self):
        row = self.db.conn.execute("PRAGMA journal_mode").fetchone()
        assert row[0] == "wal"

    def test_schema_version(self):
        row = self.db.conn.execute(
            "SELECT MAX(version) as v FROM schema_version"
        ).fetchone()
        assert row[0] >= 1
