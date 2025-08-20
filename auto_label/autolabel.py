from ultralytics import YOLO
from pathlib import Path
import cv2
import argparse
import yaml
import random
import shutil
import json
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from analysis.stats import analyze_split

def load_class_mapping(yaml_path: Path) -> dict:
    with open(yaml_path, "r") as f:
        data = yaml.safe_load(f)
    return {v: int(k) for k, v in data["names"].items()}


def auto_label(input_dir: Path, output_label_dir: Path, class_yaml: Path,
               model_path: str = "yolov8x.pt", conf_thresh: float = 0.4):

    model = YOLO(model_path)
    model.conf = conf_thresh
    output_label_dir.mkdir(parents=True, exist_ok=True)

    class_name_to_idx = load_class_mapping(class_yaml)

    image_files = list(input_dir.glob("*.[jp][pn]g"))
    print(f"[INFO] Found {len(image_files)} images in {input_dir}")

    new_labeled_files = []

    for img_path in image_files:
        label_path = output_label_dir / (img_path.stem + ".txt")

        # ✅ Bỏ qua nếu đã label trước đó
        if label_path.exists():
            print(f"[SKIP] Đã label: {img_path.name}")
            continue

        results = model(img_path)
        im = cv2.imread(str(img_path))
        if im is None:
            print(f"[WARNING] Cannot read image {img_path}, skipping.")
            continue

        h, w = im.shape[:2]
        detections = results[0].boxes

        if len(detections) == 0:
            print(f"[INFO] No detections in {img_path.name} => removed")
            img_path.unlink()  # ⚠️ Xóa ảnh gốc nếu không có detection
            continue

        with open(label_path, "w") as f:
            for i in range(len(detections)):
                box = detections.xyxy[i]
                cls_idx = int(detections.cls[i].item())
                try:
                    class_name = model.model.names[cls_idx]
                except (AttributeError, IndexError):
                    continue

                if class_name not in class_name_to_idx:
                    continue

                mapped_cls = class_name_to_idx[class_name]
                xmin, ymin, xmax, ymax = box
                x_center = ((xmin + xmax) / 2) / w
                y_center = ((ymin + ymax) / 2) / h
                bw = (xmax - xmin) / w
                bh = (ymax - ymin) / h
                f.write(f"{mapped_cls} {x_center:.6f} {y_center:.6f} {bw:.6f} {bh:.6f}\n")

        new_labeled_files.append(img_path)

    return new_labeled_files


def split_dataset(image_paths, label_dir: Path, output_base: Path,
                  train_ratio=0.7, val_ratio=0.2, test_ratio=0.1):
    if not image_paths:
        print("[INFO] Không có ảnh mới cần chia tập.")
        return

    random.shuffle(image_paths)
    total = len(image_paths)
    train_end = int(total * train_ratio)
    val_end = train_end + int(total * val_ratio)

    splits = {
        "train": image_paths[:train_end],
        "val": image_paths[train_end:val_end],
        "test": image_paths[val_end:]
    }

    for split, files in splits.items():
        img_out = output_base / split / "images"
        lbl_out = output_base / split / "labels"
        img_out.mkdir(parents=True, exist_ok=True)
        lbl_out.mkdir(parents=True, exist_ok=True)

        for img_path in files:
            target_img_path = img_out / img_path.name
            target_lbl_path = lbl_out / (img_path.stem + ".txt")

            # ✅ Bỏ qua nếu đã tồn tại
            if target_img_path.exists() and target_lbl_path.exists():
                print(f"[!] Bỏ qua (đã tồn tại): {img_path.name}")
                continue

            shutil.copy(img_path, target_img_path)

            lbl_path = label_dir / (img_path.stem + ".txt")
            if lbl_path.exists():
                shutil.copy(lbl_path, target_lbl_path)

        print(f"[✓] {split}: {len(files)} images")


def main():
    parser = argparse.ArgumentParser(description="Auto-label images and split dataset")
    parser.add_argument("--input_dir", type=str, default="data/raw/images", help="Folder chứa ảnh input")
    parser.add_argument("--output_dir", type=str, default="data/labeled", help="Folder output chứa labels và splits")
    parser.add_argument("--yaml", type=str, default="data/data.yaml", help="Đường dẫn tới file data.yaml")
    parser.add_argument("--model", type=str, default="yolov8x.pt", help="Đường dẫn tới model YOLOv8")
    parser.add_argument("--conf", type=float, default=0.4, help="Confidence threshold")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    label_dir = output_dir / "labels"

    # Step 1: Chỉ label ảnh mới
    new_labeled_imgs = auto_label(input_dir, label_dir, Path(args.yaml), args.model, args.conf)

    # Step 2: Chỉ chia tập ảnh vừa mới label
    split_dataset(new_labeled_imgs, label_dir, output_dir)

    # Optional: Xoá label tạm nếu cần
    # if label_dir.exists():
    #     shutil.rmtree(label_dir)
    #     print(f"[✓] Đã xoá thư mục tạm: {label_dir}")
    # Step 3: Phân tích thống kê các tập và lưu JSON
    all_stats = {}
    for split in ["train", "val", "test"]:
        stats = analyze_split(output_dir, split)
        if stats:
            print(f"\n📊 Stats for {split.upper()}:")
            for k, v in stats.items():
                print(f"  {k}: {v}")
            all_stats[split] = stats

    # Lưu thống kê ra file JSON trong thư mục output_dir/stats.json
    stats_json_path = output_dir / "stats.json"
    with open(stats_json_path, "w") as f:
        json.dump(all_stats, f, indent=2)
    print(f"\n✅ Đã lưu thống kê vào file: {stats_json_path}")


if __name__ == "__main__":
    main()
