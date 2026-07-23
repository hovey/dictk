from pathlib import Path

import pytest

from dictk.cli import main
from dictk.imaging import read_image


def test_help_exits_cleanly(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])
    assert exc_info.value.code == 0
    assert "dictk" in capsys.readouterr().out


def test_rosta_create_writes_file(tmp_path: Path):
    exit_code = main(["rosta", "20", "16", "--density", "0.5", "-o", str(tmp_path)])
    assert exit_code == 0

    files = list(tmp_path.glob("rosta_*.tiff"))
    assert len(files) == 1

    image = read_image(files[0])
    assert image.shape == (16, 20)


def test_rosta_create_invalid_density_fails_cleanly(tmp_path: Path, capsys):
    exit_code = main(["rosta", "20", "16", "--density", "1.5", "-o", str(tmp_path)])
    assert exit_code == 1
    assert "error" in capsys.readouterr().err
    assert list(tmp_path.glob("rosta_*.tiff")) == []


def test_rosta_create_unwritable_output_fails_cleanly(tmp_path: Path, capsys):
    unwritable = tmp_path / "unwritable"
    unwritable.mkdir()
    unwritable.chmod(0o000)
    try:
        exit_code = main(["rosta", "20", "16", "-o", str(unwritable / "sub")])
        assert exit_code == 1
        assert "error" in capsys.readouterr().err
    finally:
        unwritable.chmod(0o755)


def test_checkerboard_create_writes_file(tmp_path: Path):
    exit_code = main(["checkerboard", "20", "16", "-o", str(tmp_path)])
    assert exit_code == 0

    files = list(tmp_path.glob("checkerboard_*.tiff"))
    assert len(files) == 1

    image = read_image(files[0])
    assert image.shape == (16, 20)


def test_checkerboard_create_invalid_count_x_fails_cleanly(tmp_path: Path, capsys):
    exit_code = main(
        ["checkerboard", "20", "16", "--count-x", "0", "-o", str(tmp_path)]
    )
    assert exit_code == 1
    assert "error" in capsys.readouterr().err
    assert list(tmp_path.glob("checkerboard_*.tiff")) == []


def test_checkerboard_create_respects_short_count_flags(tmp_path: Path):
    exit_code = main(
        ["checkerboard", "20", "16", "-x", "2", "-y", "3", "-o", str(tmp_path)]
    )
    assert exit_code == 0

    files = list(tmp_path.glob("checkerboard_20w_by_16h_2x3.tiff"))
    assert len(files) == 1


def test_checkerboard_create_unwritable_output_fails_cleanly(tmp_path: Path, capsys):
    unwritable = tmp_path / "unwritable"
    unwritable.mkdir()
    unwritable.chmod(0o000)
    try:
        exit_code = main(["checkerboard", "20", "16", "-o", str(unwritable / "sub")])
        assert exit_code == 1
        assert "error" in capsys.readouterr().err
    finally:
        unwritable.chmod(0o755)


def test_astronaut_create_writes_file(tmp_path: Path):
    exit_code = main(["astronaut", "40", "20", "-o", str(tmp_path)])
    assert exit_code == 0

    files = list(tmp_path.glob("astronaut_*.tiff"))
    assert len(files) == 1

    image = read_image(files[0])
    assert image.shape == (20, 40)


def test_astronaut_create_invalid_width_fails_cleanly(tmp_path: Path, capsys):
    exit_code = main(["astronaut", "0", "20", "-o", str(tmp_path)])
    assert exit_code == 1
    assert "error" in capsys.readouterr().err
    assert list(tmp_path.glob("astronaut_*.tiff")) == []


def test_astronaut_create_unwritable_output_fails_cleanly(tmp_path: Path, capsys):
    unwritable = tmp_path / "unwritable"
    unwritable.mkdir()
    unwritable.chmod(0o000)
    try:
        exit_code = main(["astronaut", "40", "20", "-o", str(unwritable / "sub")])
        assert exit_code == 1
        assert "error" in capsys.readouterr().err
    finally:
        unwritable.chmod(0o755)


def test_astronaut_defaults_to_512x512(tmp_path: Path):
    exit_code = main(["astronaut", "-o", str(tmp_path)])
    assert exit_code == 0

    files = list(tmp_path.glob("astronaut_512w_by_512h.tiff"))
    assert len(files) == 1

    image = read_image(files[0])
    assert image.shape == (512, 512)


def test_astronaut_positional_width_only_defaults_height(tmp_path: Path):
    exit_code = main(["astronaut", "300", "-o", str(tmp_path)])
    assert exit_code == 0

    files = list(tmp_path.glob("astronaut_300w_by_512h.tiff"))
    assert len(files) == 1

    image = read_image(files[0])
    assert image.shape == (512, 300)


@pytest.mark.parametrize("image_format", ["tiff", "png", "jpg", "svg"])
def test_astronaut_create_respects_format(tmp_path: Path, image_format: str):
    exit_code = main(
        ["astronaut", "40", "20", "-o", str(tmp_path), "--format", image_format]
    )
    assert exit_code == 0

    files = list(tmp_path.glob(f"astronaut_*.{image_format}"))
    assert len(files) == 1


@pytest.mark.parametrize("image_format", ["tiff", "png", "jpg", "svg"])
def test_rosta_create_respects_format(tmp_path: Path, image_format: str):
    exit_code = main(
        ["rosta", "20", "16", "-o", str(tmp_path), "--format", image_format]
    )
    assert exit_code == 0

    files = list(tmp_path.glob(f"rosta_*.{image_format}"))
    assert len(files) == 1


@pytest.mark.parametrize("image_format", ["tiff", "png", "jpg", "svg"])
def test_checkerboard_create_respects_format(tmp_path: Path, image_format: str):
    exit_code = main(
        ["checkerboard", "20", "16", "-o", str(tmp_path), "--format", image_format]
    )
    assert exit_code == 0

    files = list(tmp_path.glob(f"checkerboard_*.{image_format}"))
    assert len(files) == 1


def test_rosta_create_invalid_format_fails_cleanly(tmp_path: Path):
    with pytest.raises(SystemExit) as exc_info:
        main(["rosta", "20", "16", "-o", str(tmp_path), "--format", "bmp"])
    assert exc_info.value.code == 2


def test_checkerboard_defaults_to_200x200(tmp_path: Path):
    exit_code = main(["checkerboard", "-o", str(tmp_path)])
    assert exit_code == 0

    files = list(tmp_path.glob("checkerboard_200w_by_200h_*.tiff"))
    assert len(files) == 1

    image = read_image(files[0])
    assert image.shape == (200, 200)


def test_checkerboard_positional_width_only_defaults_height(tmp_path: Path):
    exit_code = main(["checkerboard", "300", "-o", str(tmp_path)])
    assert exit_code == 0

    files = list(tmp_path.glob("checkerboard_300w_by_200h_*.tiff"))
    assert len(files) == 1

    image = read_image(files[0])
    assert image.shape == (200, 300)


def test_rosta_defaults_to_200x200(tmp_path: Path):
    exit_code = main(["rosta", "-o", str(tmp_path)])
    assert exit_code == 0

    files = list(tmp_path.glob("rosta_200w_by_200h_*.tiff"))
    assert len(files) == 1

    image = read_image(files[0])
    assert image.shape == (200, 200)


def test_rosta_positional_width_only_defaults_height(tmp_path: Path):
    exit_code = main(["rosta", "300", "-o", str(tmp_path)])
    assert exit_code == 0

    files = list(tmp_path.glob("rosta_300w_by_200h_*.tiff"))
    assert len(files) == 1

    image = read_image(files[0])
    assert image.shape == (200, 300)
