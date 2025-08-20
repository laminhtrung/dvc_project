"""
crawlers_local.py
--------------------------------------------------------------------
Scrape Google Images or Youtube using `icrawler` or `YoutubevideoCrawler`
and save directly to local folder `data/raw/`, no MinIO used.
Now supports config file `crawl_config.yaml`.
"""

import argparse
import time
import shutil
import yaml
from pathlib import Path
from typing import List, Optional
from icrawler.builtin import GoogleImageCrawler
from dotenv import load_dotenv
from youtube_crawler.Youtube_fixed import YoutubevideoCrawler
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))
from logs.log import logger  # 👉 THÊM logger vào đây

load_dotenv()

# === CONSTANTS ===
RAW_DIR = Path("root/trunglm8/project/data/raw")
TEMP_DIR = Path("./temp_download")
DEFAULT_CONFIG_PATH = "/root/trunglm8/project/config/crawl_config.yaml"


def clear_temp_folder():
    """Xóa toàn bộ file trong thư mục tạm"""
    if TEMP_DIR.exists():
        for f in TEMP_DIR.glob("*"):
            if f.is_file():
                f.unlink()
    else:
        TEMP_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"🧹 Cleared temporary folder {TEMP_DIR}")


def crawl_google_images(query: str,
                        n_imgs: int,
                        save_dir: Path,
                        filters: Optional[dict] = None) -> List[Path]:
    """
    Crawl Google Images vào thư mục tạm, rồi đổi tên và chuyển về `save_dir`.
    """
    logger.info(f"🔍 Crawling Google Images: '{query}' with max {n_imgs} images")

    clear_temp_folder()
    save_dir.mkdir(parents=True, exist_ok=True)

    crawler = GoogleImageCrawler(storage={"root_dir": str(TEMP_DIR)})
    crawler.crawl(keyword=query, max_num=n_imgs, filters=filters or {})

    timestamp = time.strftime("%y%d%m_%H%M%S")
    existing_files = list(save_dir.glob("*.jpg"))
    start_idx = len(existing_files)

    final_files = []
    for i, img_path in enumerate(sorted(TEMP_DIR.glob("*"))):
        ext = img_path.suffix or ".jpg"
        new_name = f"{timestamp}_{query.replace(' ', '_')}_{start_idx + i:04d}{ext}"
        new_path = save_dir / new_name
        shutil.move(str(img_path), str(new_path))
        final_files.append(new_path)

    logger.info(f"✅ Saved {len(final_files)} images to {save_dir}")
    return final_files


def crawl_youtube_videos(query: str,
                         n_videos: int,
                         save_dir: Path,
                         filters: Optional[dict] = None) -> List[Path]:
    logger.info(f"📺 Crawling YouTube videos: '{query}' into {save_dir}")
    save_dir.mkdir(parents=True, exist_ok=True)

    YoutubevideoCrawler(storage={"root_dir": str(save_dir)}).crawl(
        keyword=query,
        max_num=n_videos,
        filters=filters or {}
    )

    logger.info(f"✅ Downloaded YouTube videos to {save_dir}")
    return list(save_dir.iterdir())


def load_config(config_path: str = DEFAULT_CONFIG_PATH) -> dict:
    logger.info(f"📄 Loading crawl config from: {config_path}")
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)["crawl"]
    logger.info(f"🔧 Config loaded: {config}")
    return config


def main():
    parser = argparse.ArgumentParser(
        description="Scrape Google Images or YouTube videos and save to local folder"
    )
    parser.add_argument("--config", type=str, default=DEFAULT_CONFIG_PATH,
                        help="Path to crawl_config.yaml")

    args = parser.parse_args()
    cfg = load_config(args.config)

    query = cfg["query"]
    num = cfg.get("num_images", 50)
    crawl_type = cfg.get("type", "images")
    save_dir = Path(cfg.get("save_dir", RAW_DIR / ("images" if crawl_type == "images" else "videos")))
    filters = cfg.get("filters", {})

    logger.info(f"🚀 Start crawling pipeline: query='{query}' type='{crawl_type}' num={num}")
    if crawl_type == "images":
        crawl_google_images(query, num, save_dir, filters)
    else:
        crawl_youtube_videos(query, num, save_dir, filters)

    logger.info("✅ Crawl pipeline completed.")


if __name__ == "__main__":
    main()
