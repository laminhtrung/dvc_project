import argparse
from pathlib import Path
import os
import glob
import yaml
import json
from stats import analyze_split
from visualize import (
    bar_chart_objects_per_class,
    pie_chart_class_distribution,
    visualize_split_distribution,
)

def main():
    parser = argparse.ArgumentParser(description="Analyze dataset splits")
    parser.add_argument("--dataset_dir", type=str, required=True, help="Path to the dataset directory")
    parser.add_argument("--output_file", type=str, default="data/stats/statistics.json", help="Path to output JSON")
    args = parser.parse_args()

    # Dataset root
    dataset_root = Path(args.dataset_dir)
    yaml_file = glob.glob(os.path.join(dataset_root, "*.yaml"))

    if not yaml_file:
        print("YAML file does not exist!")
        return
    else:
        yaml_path = yaml_file[0]
        with open(yaml_path, 'r') as f:
            data_cfg = yaml.safe_load(f)

    class_names = {i: name for i, name in enumerate(data_cfg['names'])}

    # Output dir (parent of output_file)
    output_file_path = Path(args.output_file)
    output_dir = output_file_path.parent
    os.makedirs(output_dir, exist_ok=True)

    split_image_stats = {}
    all_stats = {}

    splits = ["all"]
    for split in splits:
        stats = analyze_split(dataset_root, split)
        print(f"\nStats for '{split}':\n", stats)

        # Generate visualizations
        bar_chart_objects_per_class(split, stats, class_names, output_dir)
        pie_chart_class_distribution(split, stats, class_names, output_dir)

        split_image_stats[split] = stats["total_images"]
        all_stats[split] = stats

    # Visualize overall split distribution
    visualize_split_distribution(split_image_stats, output_dir)

    # Save stats to JSON
    with open(output_file_path, "w") as f:
        json.dump(all_stats, f, indent=2)

    print(f"\n✅ Statistics saved to {output_file_path}")

if __name__ == "__main__":
    main()
