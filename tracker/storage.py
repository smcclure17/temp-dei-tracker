from datetime import datetime
import hashlib
import json
import pathlib

from tracker.models import ScrapeResult

ROOT = pathlib.Path(__file__).parent.parent
# DATA_ROOT = pathlib.Path("data") / "tracker"
# DATA_ROOT.mkdir(exist_ok=True)

DATA_ROOT = pathlib.Path("/mnt/s3/tracker")
DATETIME = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")


def get_path_for_url(url: str):
    return DATA_ROOT / url_to_id(url)


def url_to_id(url: str) -> str:
    """Create unique ID from url. Used for naming directories"""
    return hashlib.sha256(url.encode("utf")).hexdigest()[:7]


def get_previous_snapshot(
    base_path: pathlib.Path, compare_to_oldest: bool = False
) -> ScrapeResult:
    def load_content_from_dir(directory: pathlib.Path) -> ScrapeResult:
        content = (directory / "content.md").read_text()
        content_html_dir = directory / "content.html"
        if content_html_dir.exists():
            content_html = content_html_dir.read_text()
        else:
            content_html=None
        meta = (directory / "meta.json").read_text()
        meta_dict = json.loads(meta)
        return ScrapeResult(**meta_dict, content=content, content_html=content_html)

    if not compare_to_oldest:
        return load_content_from_dir(base_path / "current")

    # Find oldest timestamped directory
    timestamp_dirs = [
        d for d in base_path.iterdir() if d.is_dir() and d.name != "current"
    ]

    target_dir = (
        min(timestamp_dirs, key=lambda d: d.name)
        if timestamp_dirs
        else base_path / "current"
    )

    if target_dir == base_path / "current":
        print("Warning: No timestamped dirs found. Falling back to current")

    return load_content_from_dir(target_dir)


def get_existing_screenshot(path: pathlib.Path):
    path = path / "current" / "meta.json"
    if not path.exists():
        print("No archive exists. skipping old png fetch")
        return None

    data = ScrapeResult(
        **json.loads(path.read_text()), content=""
    )  # hack, we don't need content
    return data.screenshot_url


def _save_data(
    curr_path: pathlib.Path,
    page: ScrapeResult,
):
    curr_path.mkdir(exist_ok=True)
    content_path = curr_path / "content.md"
    content_html_path = curr_path / "content.html"
    meta_path = curr_path / "meta.json"
    markdown = page.content
    metadata = page.model_dump_json(exclude=("content", "content_html"))

    content_path.write_text(markdown)
    meta_path.write_text(metadata)
    content_html_path.write_text(page.content_html)


def save_current_data(path: pathlib.Path, page: ScrapeResult):
    path = path / "current"
    _save_data(path, page)


def save_archive_data(path: pathlib.Path, page: ScrapeResult):
    path = path / DATETIME
    _save_data(path, page)


def persist_update_time():
    path = ROOT / "meta.txt"
    path.write_text(f"Last updated: {DATETIME}")


def get_last_update_time():
    path = ROOT / "meta.txt"
    str_date = path.read_text().split(": ")[1].strip()
    return datetime.strptime(str_date, "%Y-%m-%dT%H-%M-%S")
