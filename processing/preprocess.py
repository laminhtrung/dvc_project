import cv2
from pathlib import Path
import albumentations as A
from albumentations.augmentations.dropout.coarse_dropout import CoarseDropout
import shutil
import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from analysis.stats import analyze_split

def load_image(img_path):
    img = cv2.imread(str(img_path))
    if img is None:
        raise FileNotFoundError(f"Cannot load image {img_path}")
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

def load_label(label_path):
    labels = []
    try:
        with open(label_path, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) != 5:
                    continue
                cls_id, x_c, y_c, w, h = parts
                labels.append([int(cls_id), float(x_c), float(y_c), float(w), float(h)])
    except FileNotFoundError:
        pass
    return labels

def save_label(labels, save_path):
    with open(save_path, 'w') as f:
        for label in labels:
            f.write(' '.join(map(str, label)) + '\n')

def check_and_fix_labels(labels):
    fixed = []
    for cls_id, x_c, y_c, w, h in labels:
        x_c = min(max(x_c, 0), 1)
        y_c = min(max(y_c, 0), 1)
        w = min(max(w, 0), 1)
        h = min(max(h, 0), 1)
        if w > 0 and h > 0:
            fixed.append([cls_id, x_c, y_c, w, h])
    return fixed

def yolo_to_bbox(yolo_box, img_width, img_height):
    cls_id, x_c, y_c, w, h = yolo_box
    x1 = int((x_c - w / 2) * img_width)
    y1 = int((y_c - h / 2) * img_height)
    x2 = int((x_c + w / 2) * img_width)
    y2 = int((y_c + h / 2) * img_height)
    return [x1, y1, x2, y2, cls_id]

def bbox_to_yolo(bbox, img_width, img_height):
    x1, y1, x2, y2, cls_id = bbox
    x_c = ((x1 + x2) / 2) / img_width
    y_c = ((y1 + y2) / 2) / img_height
    w = (x2 - x1) / img_width
    h = (y2 - y1) / img_height
    return [int(cls_id), x_c, y_c, w, h]

def get_augmentation_pipeline():
    return A.Compose([
        A.HorizontalFlip(p=0.5),
        A.Rotate(limit=30, p=0.5),
        A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2, p=0.5),
        A.HueSaturationValue(hue_shift_limit=10, sat_shift_limit=15, val_shift_limit=10, p=0.5),
        A.GaussNoise(var_limit=(10.0, 50.0), p=0.3),
        A.MotionBlur(blur_limit=5, p=0.3),
        CoarseDropout(
            max_holes=8, max_height=20, max_width=20,
            min_holes=2, min_height=10, min_width=10,
            fill_value=0, p=0.3
        )
    ], bbox_params=A.BboxParams(format='pascal_voc', label_fields=['category_ids']))

def preprocess_image_and_label(img_path, label_path, output_images_dir, output_labels_dir):
    img = load_image(img_path)
    height, width = img.shape[:2]
    labels = load_label(label_path)
    labels = check_and_fix_labels(labels)

    # Lưu ảnh gốc và nhãn gốc vào output
    out_img_path = output_images_dir / img_path.name
    out_label_path = output_labels_dir / (img_path.stem + '.txt')

    # Chuyển ảnh RGB sang BGR trước khi lưu với cv2
    cv2.imwrite(str(out_img_path), cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
    save_label(labels, out_label_path)

    # Nếu không có nhãn hợp lệ, không augment thêm nữa
    if len(labels) == 0:
        return False

    # Chuẩn bị bbox để augment
    bboxes = [yolo_to_bbox(lab, width, height) for lab in labels]
    category_ids = [b[-1] for b in bboxes]
    for b in bboxes:
        b.pop()  # Loại bỏ class_id trước khi augment

    # Augmentation
    aug = get_augmentation_pipeline()
    augmented = aug(image=img, bboxes=bboxes, category_ids=category_ids)
    img_aug = cv2.cvtColor(augmented['image'], cv2.COLOR_RGB2BGR)
    aug_bboxes = augmented['bboxes']
    aug_labels = [bbox_to_yolo(list(b) + [cat], width, height)
                  for b, cat in zip(aug_bboxes, augmented['category_ids'])]

    # Lưu ảnh augment và nhãn augment
    aug_img_name = img_path.stem + "_aug" + img_path.suffix
    aug_lbl_name = img_path.stem + "_aug.txt"
    aug_img_out = output_images_dir / aug_img_name
    aug_lbl_out = output_labels_dir / aug_lbl_name
    cv2.imwrite(str(aug_img_out), img_aug)
    save_label(aug_labels, aug_lbl_out)

    return True

def get_all_stems(images_dir, exts=['.png', '.jpg']):
    stems = set()
    for ext in exts:
        for f in images_dir.glob(f'*{ext}'):
            stems.add(f.stem)
    return stems

if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('--image_dir', type=str, default='data/labeled/train/images', help="Input image folder")
    parser.add_argument('--label_dir', type=str, default='data/labeled/train/labels', help="Input label folder")
    parser.add_argument('--output_dir', type=str, default='data/processed', help="Output base directory")
    args = parser.parse_args()

    input_images_dir = Path(args.image_dir)
    input_labels_dir = Path(args.label_dir)
    output_base_dir = Path(args.output_dir)

    output_images_dir = output_base_dir / "train" / "images"
    output_labels_dir = output_base_dir / "train" / "labels"

    output_images_dir.mkdir(parents=True, exist_ok=True)
    output_labels_dir.mkdir(parents=True, exist_ok=True)

    # Lấy tất cả các stem (tên file không đuôi) trong output_images_dir (bao gồm ảnh gốc và ảnh augment)
    output_stems = get_all_stems(output_images_dir, exts=['.png', '.jpg'])

    # Lọc ảnh input: chỉ augment nếu ảnh đó chưa tồn tại trong output (theo stem)
    img_files = [
        f for f in list(input_images_dir.glob('*.jpg')) + list(input_images_dir.glob('*.png'))
        if f.stem not in output_stems
    ]

    count = 0
    for img_path in img_files:
        label_path = input_labels_dir / (img_path.stem + '.txt')

        try:
            saved = preprocess_image_and_label(img_path, label_path, output_images_dir, output_labels_dir)
            if saved:
                count += 1
                print(f"[✓] Saved augmented: {img_path.name}")
            else:
                print(f"[!] No valid labels for {img_path.name}, skipped augmentation.")
        except Exception as e:
            print(f"[!] Error processing {img_path.name}: {e}")

    print(f"\n✅ Total processed and saved images: {count}")

    # Copy val và test từ labeled sang processed (nếu có)
    for split in ['val', 'test']:
        src = Path('data/labeled') / split
        dst = output_base_dir / split
        if src.exists():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            print(f"[✓] Copied {split} from {src} to {dst}")
        else:
            print(f"[!] Warning: Source folder {src} does not exist. Skipping copy for {split}")
    
    print("\n📊 Phân tích dữ liệu sau augmentation:")
    all_stats = {}
    for split in ['train', 'val', 'test']:
        stats = analyze_split(output_base_dir, split)
        if stats:
            print(f"\n📂 Stats cho {split.upper()}:")
            for k, v in stats.items():
                print(f"  {k}: {v}")
            all_stats[split] = stats

    # Ghi lại thống kê ra file JSON
    stats_path = output_base_dir / "stats.json"
    with open(stats_path, "w") as f:
        json.dump(all_stats, f, indent=2)
    print(f"\n✅ Đã lưu thống kê vào: {stats_path}")
