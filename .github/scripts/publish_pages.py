"""Publish a complete update on top of the current Pages branch."""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time


PAGES_REF = "refs/heads/gh-pages"
BOT_NAME = "github-actions[bot]"
BOT_EMAIL = "41898282+github-actions[bot]@users.noreply.github.com"
PUBLISH_MESSAGES = {
    "data": "Publish stock data",
    "ui": "Publish UI",
    "thumbnails": "Publish thumbnails",
}


def git(*args, env=None, check=True):
    return subprocess.run(
        ["git", *args], check=check, capture_output=True, text=True,
        encoding="utf-8", errors="replace", env=env,
    )


def fetch_pages_head():
    result = git("ls-remote", "--exit-code", "origin", PAGES_REF, check=False)
    if result.returncode == 2:
        return None
    result.check_returncode()
    git("fetch", "--no-tags", "--depth=1", "origin", PAGES_REF)
    return git("rev-parse", "FETCH_HEAD").stdout.strip()


def copy_entry(source, destination):
    if source.is_dir():
        shutil.copytree(source, destination, dirs_exist_ok=True)
    else:
        shutil.copy2(source, destination)


def copy_stock_data(pages):
    public_data = Path("public/data")
    with (public_data / "stock.json").open(encoding="utf-8") as stock_file:
        stock = json.load(stock_file)
    if (
        not isinstance(stock, dict)
        or not isinstance(stock.get("generated_at"), str)
        or not stock["generated_at"]
        or not isinstance(stock.get("products"), list)
        or not stock["products"]
        or not isinstance(stock.get("sources"), list)
        or not stock["sources"]
        or not isinstance(stock.get("manufacturers"), list)
        or any(
            not isinstance(product, dict) or not product.get("id") or not isinstance(product.get("offers"), list)
            for product in stock["products"]
        )
    ):
        raise ValueError("public/data/stock.json does not contain a valid catalog")
    destination = pages / "data"
    destination.mkdir(exist_ok=True)
    sources = sorted(public_data.glob("*.json"))
    for source in sources:
        shutil.copy2(source, destination / source.name)
    return [f"data/{source.name}" for source in sources]


def copy_ui(pages):
    built = Path("dist")
    if not (built / "index.html").is_file():
        raise FileNotFoundError("dist/index.html is required to publish UI")
    first_ui = not (pages / "index.html").exists()
    updated_paths = [".nojekyll"]
    for artifact in built.iterdir():
        if artifact.name not in {"assets", "data"}:
            copy_entry(artifact, pages / artifact.name)
            updated_paths.append(artifact.name)

    assets = pages / "assets"
    assets.mkdir(exist_ok=True)
    for artifact in (built / "assets").iterdir():
        destination = assets / artifact.name
        if (Path("public/assets") / artifact.name).exists():
            if not first_ui or destination.exists():
                continue
        copy_entry(artifact, destination)
        updated_paths.append(f"assets/{artifact.name}")
    if not (pages / "data/stock.json").is_file():
        updated_paths.extend(copy_stock_data(pages))
    (pages / ".nojekyll").touch()
    return updated_paths


def copy_thumbnails(pages):
    assets = pages / "assets"
    assets.mkdir(exist_ok=True)
    updated_assets = set()
    for name in ("filamentos3d", "grilon3", "thumbs"):
        directory = assets / name
        if directory.exists():
            if not directory.resolve().is_relative_to(pages.resolve()):
                raise ValueError(f"Unexpected asset directory outside the Pages copy: {directory}")
            shutil.rmtree(directory)
            updated_assets.add(f"assets/{name}")
    for artifact in Path("public/assets").iterdir():
        copy_entry(artifact, assets / artifact.name)
        updated_assets.add(f"assets/{artifact.name}")
    return sorted(updated_assets) + copy_stock_data(pages)


def publish_once(kind):
    parent = fetch_pages_head()
    with tempfile.TemporaryDirectory(prefix="central-pages-", dir=os.getenv("RUNNER_TEMP")) as temp_dir:
        scratch = Path(temp_dir)
        pages = scratch / "site"
        pages.mkdir()
        env = {
            **os.environ,
            "GIT_INDEX_FILE": str(scratch / "index"),
            "GIT_AUTHOR_NAME": BOT_NAME,
            "GIT_AUTHOR_EMAIL": BOT_EMAIL,
            "GIT_COMMITTER_NAME": BOT_NAME,
            "GIT_COMMITTER_EMAIL": BOT_EMAIL,
        }
        git("read-tree", parent or "--empty", env=env)
        original_tree = git("write-tree", env=env).stdout.strip()
        git("checkout-index", "--all", f"--prefix={pages.as_posix()}/", env=env)

        if kind == "data":
            updated_paths = copy_stock_data(pages)
        elif kind == "ui":
            updated_paths = copy_ui(pages)
        else:
            updated_paths = copy_thumbnails(pages)

        git("--literal-pathspecs", f"--work-tree={pages}", "add", "--all", "--", *updated_paths, env=env)
        next_tree = git("write-tree", env=env).stdout.strip()
        if next_tree == original_tree:
            print("Pages is already up to date.")
            return
        arguments = ["commit-tree", next_tree, "-m", PUBLISH_MESSAGES[kind]]
        if parent:
            arguments.extend(["-p", parent])
        commit = git(*arguments, env=env).stdout.strip()
        git("push", "origin", f"{commit}:{PAGES_REF}")
        print(f"Published {kind} to Pages at {commit}.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=PUBLISH_MESSAGES)
    kind = parser.parse_args().kind
    for attempt in range(1, 4):
        try:
            publish_once(kind)
            return
        except subprocess.CalledProcessError as error:
            print(f"Pages attempt {attempt}/3 failed: {(error.stderr or str(error)).strip()}", flush=True)
            if attempt == 3:
                raise SystemExit(error.returncode) from error
            time.sleep(attempt * 2)


if __name__ == "__main__":
    main()
