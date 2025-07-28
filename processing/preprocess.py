import cv2
import os
import random
import shutil
from pathlib import Path
import albumentations as A
from albumentations.pytorch import ToTensorV2


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
    return [cls_id, x_c, y_c, w, h]


from albumentations.augmentations.dropout.coarse_dropout import CoarseDropout

def get_augmentation_pipeline():
    return A.Compose([
        A.HorizontalFlip(p=0.5),
        A.Rotate(limit=30, p=0.5),  # ±30 độ
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

    if len(labels) == 0:
        return False  # Không augment nếu không có nhãn hợp lệ

    bboxes = [yolo_to_bbox(lab, width, height) for lab in labels]
    category_ids = [b[-1] for b in bboxes]
    for b in bboxes:
        b.pop()  # Loại bỏ class_id trước khi augment

    aug = get_augmentation_pipeline()
    augmented = aug(image=img, bboxes=bboxes, category_ids=category_ids)
    img_aug = cv2.cvtColor(augmented['image'], cv2.COLOR_RGB2BGR)
    aug_bboxes = augmented['bboxes']
    aug_labels = [bbox_to_yolo(list(b) + [cat], width, height)
                  for b, cat in zip(aug_bboxes, augmented['category_ids'])]

    # Tạo tên mới cho ảnh augment
    aug_img_name = img_path.stem + "_aug" + img_path.suffix
    aug_lbl_name = img_path.stem + "_aug.txt"

    aug_img_out = output_images_dir / aug_img_name
    aug_lbl_out = output_labels_dir / aug_lbl_name

    cv2.imwrite(str(aug_img_out), img_aug)
    save_label(aug_labels, aug_lbl_out)

    return True

if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('--image_dir', type=str, default='../data/labeled/train/images', help="Input image folder")
    parser.add_argument('--label_dir', type=str, default='../data/labeled/train/labels', help="Input label folder")
    parser.add_argument('--output_dir', type=str, default='../data/labeled/train', help="Output base directory")
    args = parser.parse_args()

    input_images_dir = Path(args.image_dir)
    input_labels_dir = Path(args.label_dir)

    output_images_dir = Path(args.output_dir) / "images"
    output_labels_dir = Path(args.output_dir) / "labels"

    output_images_dir.mkdir(parents=True, exist_ok=True)
    output_labels_dir.mkdir(parents=True, exist_ok=True)

    # 1. Lấy danh sách ảnh đã được augment trước đó
    augmented_stems = set(f.stem.split('_aug')[0] for f in input_images_dir.glob('*_aug*.png'))

    # 2. Chỉ chọn ảnh gốc chưa từng được augment
    img_files = [
    f for f in list(input_images_dir.glob('*.jpg')) + list(input_images_dir.glob('*.png'))
    if "_aug" not in f.stem and f.stem not in augmented_stems]

    count = 0
    for img_path in img_files:
        label_path = input_labels_dir / (img_path.stem + '.txt')

        try:
            saved = preprocess_image_and_label(img_path, label_path, output_images_dir, output_labels_dir)
            if saved:
                count += 1
                print(f"[\u2713] Saved original and augmented: {img_path.name}")
        except Exception as e:
            print(f"[!] Error processing {img_path.name}: {e}")

    print(f"\n\u2705 Total processed and saved images: {count}")
