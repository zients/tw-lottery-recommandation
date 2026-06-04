from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parents[1]


def test_project_name_uses_recommendation_spelling():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert pyproject["project"]["name"] == "tw-lottery-recommendation"


def test_project_files_do_not_use_wrong_recommend_spelling():
    project_files = ["README.md", "pyproject.toml", "uv.lock"]
    contents = "\n".join(
        (ROOT / file_name).read_text(encoding="utf-8")
        for file_name in project_files
    )
    typo = "re" + "command"

    assert typo not in contents.lower()
