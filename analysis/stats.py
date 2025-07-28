import os
from collections import defaultdict
from pathlib import Path

def load_dataset_info(dataset_root):
    import glob, yaml
    yaml_file = glob.glob(os.path.join(dataset_root, "*.yaml"))
    if not yaml_file:
        raise FileNotFoundError("YAML file not found in dataset root.")
    with open(yaml_file[0], 'r') as f:
        data_cfg = yaml.safe_load(f)
    class_names = {i: name for i, name in enumerate(data_cfg['names'])}
    return class_names

def analyze_split(dataset_root: Path, split: str):
    if split == "all":
        image_dir = dataset_root / "images" / "augmented"
        label_dir = dataset_root / "labels" / "augmented"
    else:
        image_dir = dataset_root / split / "images"
        label_dir = dataset_root / split / "labels"

    total_objects = 0
    total_images = 0
    objects_per_class = defaultdict(int)

    image_files = [f for f in os.listdir(image_dir) if f.endswith(('.jpg', '.png'))]
    total_images = len(image_files)

    label_files = [f for f in os.listdir(label_dir) if f.endswith('.txt')]
    total_labels = len(label_files)

    for label_f in label_files:
        label_path = os.path.join(label_dir, label_f)
        with open(label_path, 'r') as f:
            lines = f.readlines()
            for line in lines:
                parts = line.strip().split()
                if len(parts) >= 5:
                    cls_id = int(parts[0])
                    objects_per_class[cls_id] += 1
                    total_objects += 1

    return {
        'total_images': total_images,
        'total_labels': total_labels,
        'total_objects': total_objects,
        'avg_objets_per_image': round(total_objects / total_images, 2) if total_images > 0 else 0,
        'objets_per_class': dict(objects_per_class),
    }