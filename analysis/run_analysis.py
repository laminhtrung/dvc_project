import argparse
from pathlib import Path
import os
import glob
import yaml
from stats import analyze_split
from visualize import (
    bar_chart_objects_per_class,
    pie_chart_class_distribution,
    visualize_split_distribution,
)

def main():
    parser = argparse.ArgumentParser(description="Analyze dataset splits")
    parser.add_argument("--dataset_dir", type=str, required=True, help="Path to the dataset directory")
    args = parser.parse_args()

    # Dataset root
    dataset_root = Path(args.dataset_dir)
    yaml_file = glob.glob(os.path.join(dataset_root, "*.yaml"))

    if not yaml_file:
        print("yaml file does not exist!")
    else:
        yaml_path = yaml_file[0]
        
        with open(yaml_path, 'r') as f:
            data_cfg = yaml.safe_load(f)
            
    splits = ["all"]

    class_names = {i: name for i, name in enumerate(data_cfg['names'])} #classes name

    ##output dir
    output_dir = dataset_root / "stats"
    os.makedirs(output_dir, exist_ok=True)

    split_image_stats = {}
    # Analyze and visualize each split
    for split in splits:
        stats = analyze_split(dataset_root, split)
        print(f"\nStats for {split}:\n", stats)

        bar_chart_objects_per_class(split, stats, class_names, output_dir)
        pie_chart_class_distribution(split, stats, class_names, output_dir)

        split_image_stats[split] = stats["total_images"]

    visualize_split_distribution(split_image_stats, output_dir)

if __name__ == "__main__":
    main()
