import cv2
import random
import yaml
from pathlib import Path

def load_class_names(yaml_path):
    with open(yaml_path, "r") as f:
        data = yaml.safe_load(f)
    return data["names"]

def generate_colors(num_classes):
    return {
        i: [random.randint(0, 255) for _ in range(3)]
        for i in range(num_classes)
    }

def load_yolo_labels(txt_path, img_width, img_height):
    boxes = []
    labels = []

    if not txt_path.exists():
        return boxes, labels

    with open(txt_path, "r") as f:
        lines = f.readlines()

    for line in lines:
        parts = line.strip().split()
        if len(parts) != 5:
            continue

        class_id, x_center, y_center, w, h = map(float, parts)
        x_center *= img_width
        y_center *= img_height
        w *= img_width
        h *= img_height

        x1 = int(x_center - w / 2)
        y1 = int(y_center - h / 2)
        x2 = int(x_center + w / 2)
        y2 = int(y_center + h / 2)

        boxes.append([x1, y1, x2, y2])
        labels.append(int(class_id))

    return boxes, labels

def draw_boxes(image, boxes, labels=None, class_names=None, colors=None, thickness=2):
    for i, (x1, y1, x2, y2) in enumerate(boxes):
        cls_id = labels[i]
        color = colors.get(cls_id, (0, 255, 0)) if colors else (0, 255, 0)
        class_name = class_names[cls_id] if class_names and cls_id < len(class_names) else str(cls_id)

        cv2.rectangle(image, (x1, y1), (x2, y2), color, thickness)
        cv2.putText(image, class_name, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX,
                    0.6, color, 2)
    return image

def visualize_folder(img_dir: Path, label_dir: Path, output_dir: Path, yaml_path: Path):
    class_names = load_class_names(yaml_path)
    colors = generate_colors(len(class_names))

    output_dir.mkdir(parents=True, exist_ok=True)
    image_paths = list(img_dir.glob("*.[jp][pn]g"))

    print(f"[INFO] Visualizing {len(image_paths)} images from {img_dir}")

    for img_path in image_paths:
        label_path = label_dir / (img_path.stem + ".txt")
        img = cv2.imread(str(img_path))
        if img is None:
            print(f"[WARNING] Cannot read image {img_path}, skipping.")
            continue

        h, w = img.shape[:2]
        boxes, labels = load_yolo_labels(label_path, w, h)
        vis_image = draw_boxes(img, boxes, labels, class_names, colors)
        output_path = output_dir / img_path.name
        cv2.imwrite(str(output_path), vis_image)
        print(f"[✓] Saved visualized image to: {output_path}")

# ==== Ví dụ sử dụng ====
if __name__ == "__main__":
    image_folder = Path("../data/labeled/train/images")
    label_folder = Path("../data/labeled/train/labels")
    output_folder = Path("../data/visualized")
    yaml_file = Path("../data/data.yaml")  # Chứa class names

    visualize_folder(image_folder, label_folder, output_folder, yaml_file)
