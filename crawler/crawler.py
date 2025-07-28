"""
crawlers_local.py
--------------------------------------------------------------------
Scrape Google Images or Youtube using `icrawler` or `YoutubevideoCrawler`
and save directly to local folder `data/raw/`, no MinIO used.
"""

import argparse
import time
import shutil
from pathlib import Path
from typing import List, Optional
from icrawler.builtin import GoogleImageCrawler
from dotenv import load_dotenv
from youtube_crawler.Youtube_fixed import YoutubevideoCrawler

load_dotenv()

# === CONSTANTS ===
RAW_DIR = Path("../data/raw")
TEMP_DIR = Path("./temp_download")


def clear_temp_folder():
    """Xóa toàn bộ file trong thư mục tạm"""
    if TEMP_DIR.exists():
        for f in TEMP_DIR.glob("*"):
            if f.is_file():
                f.unlink()
    else:
        TEMP_DIR.mkdir(parents=True, exist_ok=True)


def crawl_google_images(query: str,
                        n_imgs: int,
                        save_dir: Path,
                        filters: Optional[dict] = None) -> List[Path]:
    """
    Crawl Google Images vào thư mục tạm, rồi đổi tên và chuyển về `save_dir`.
    """
    print(f"[✓] Crawling Google Images: '{query}'")

    clear_temp_folder()
    save_dir.mkdir(parents=True, exist_ok=True)

    # Crawl ảnh vào thư mục tạm
    crawler = GoogleImageCrawler(storage={"root_dir": str(TEMP_DIR)})
    crawler.crawl(keyword=query, max_num=n_imgs, filters=filters or {})

    # Tạo timestamp cho file: ddmm_HHMMSS
    timestamp = time.strftime("%y%d%m_%H%M%S")

    # Bắt đầu đánh số file đích theo số lượng đã có sẵn
    existing_files = list(save_dir.glob("*.jpg"))
    start_idx = len(existing_files)

    final_files = []
    for i, img_path in enumerate(sorted(TEMP_DIR.glob("*"))):
        ext = img_path.suffix or ".jpg"
        new_name = f"{timestamp}_{query.replace(' ', '_')}_{start_idx + i:04d}{ext}"
        new_path = save_dir / new_name
        shutil.move(str(img_path), str(new_path))
        final_files.append(new_path)

    print(f"[✓] Saved {len(final_files)} images to {save_dir}")
    return final_files


def crawl_youtube_videos(query: str,
                         n_videos: int,
                         save_dir: Path,
                         filters: Optional[dict] = None) -> List[Path]:
    """
    Crawl YouTube videos và lưu vào `save_dir`.
    """
    print(f"[✓] Crawling YouTube videos: '{query}' into {save_dir}")
    save_dir.mkdir(parents=True, exist_ok=True)
    YoutubevideoCrawler(storage={"root_dir": str(save_dir)}).crawl(
        keyword=query,
        max_num=n_videos,
        filters=filters or {}
    )
    return list(save_dir.iterdir())


def main():
    parser = argparse.ArgumentParser(
        description="Scrape Google Images or YouTube videos and save to local folder"
    )
    parser.add_argument("--query", required=True,
                        help="Search keywords")
    parser.add_argument("--num-image", "-n", type=int, default=50,
                        help="Number of images/videos to download (default: 50)")
    parser.add_argument("--type", choices=["images", "videos"], default="images",
                        help="Choose 'images' or 'videos' (default: images)")
    parser.add_argument("--save_dir", type=str,
                        help="Directory to save images or videos")

    args = parser.parse_args()

    save_path = Path(args.save_dir) if args.save_dir else RAW_DIR / (
        "images" if args.type == "images" else "videos")

    if args.type == "images":
        crawl_google_images(args.query, args.num_image, save_path)
    else:
        crawl_youtube_videos(args.query, args.num_image, save_path)


if __name__ == "__main__":
    main()
