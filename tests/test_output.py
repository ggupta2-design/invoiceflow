import os

import pytest

from invoiceflow.output import write_output


def test_output_creates_private_parent_directories(tmp_path):
    path = tmp_path / "reports" / "invoice.txt"

    result = write_output(path, "private report\n")

    assert result == path
    assert path.read_text(encoding="utf-8") == "private report\n"
    assert os.stat(path).st_mode & 0o777 == 0o600


def test_output_never_overwrites_existing_files(tmp_path):
    path = tmp_path / "report.json"
    path.write_text("trusted", encoding="utf-8")

    with pytest.raises(ValueError, match="already exists"):
        write_output(path, "replacement")

    assert path.read_text(encoding="utf-8") == "trusted"


def test_output_rejects_symbolic_link_destinations(tmp_path):
    target = tmp_path / "target.txt"
    target.write_text("trusted", encoding="utf-8")
    link = tmp_path / "report.txt"
    link.symlink_to(target)

    with pytest.raises(ValueError, match="already exists"):
        write_output(link, "replacement")

    assert target.read_text(encoding="utf-8") == "trusted"
