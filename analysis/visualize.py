import os
import matplotlib.pyplot as plt

def bar_chart_objects_per_class(split, stats, class_names, output_dir):
    class_counts = stats['objets_per_class']
    class_labels = [class_names.get(k, f"class_{k}") for k in class_counts]
    class_values = list(class_counts.values())

    plt.figure(figsize=(10, 5))
    bars = plt.bar(class_labels, class_values, color='#556B2F')
    plt.title(f"Object Distribution per Class - {split}")
    plt.xlabel("Class")
    plt.ylabel("Number of Objects")
    plt.xticks(rotation=45)

    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2., height, '%d' % int(height), ha='center', va='bottom')

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f"{split}_objects_per_class.png"))
    plt.close()

def pie_chart_class_distribution(split, stats, class_names, output_dir):
    objects_per_class = stats['objets_per_class']
    total_objects = stats['total_objects']
    labels = [class_names[cls_id] for cls_id in objects_per_class]
    sizes = [count / total_objects * 100 for count in objects_per_class.values()]
    cmap = plt.get_cmap('GnBu', len(labels))
    colors = [cmap(i) for i in range(len(labels))]

    plt.figure(figsize=(8, 8))
    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
            startangle=140, textprops={'fontsize': 12})
    plt.axis('equal')
    plt.title(f'Phân bố đối tượng theo class - {split.upper()}', fontsize=14)
    plt.savefig(os.path.join(output_dir, f"{split}_class_distribution.png"))
    plt.close()

def visualize_split_distribution(split_image_stats, output_dir):
    train_imgs = split_image_stats.get('train', 0)
    val_imgs = split_image_stats.get('val', 0)
    test_imgs = split_image_stats.get('test', 0)
    total_imgs = train_imgs + val_imgs + test_imgs

    values = [train_imgs, val_imgs, test_imgs]
    colors = ["#B4591CB0", "#25612FD8", "#1D4E759E"]

    plt.figure(figsize=(10, 2))
    plt.barh(['Dataset'], train_imgs, color=colors[0], label=f"Train ({train_imgs})")
    plt.barh(['Dataset'], val_imgs, left=train_imgs, color=colors[1], label=f"Val ({val_imgs})")
    plt.barh(['Dataset'], test_imgs, left=train_imgs + val_imgs, color=colors[2], label=f"Test ({test_imgs})")

    plt.text(total_imgs + 50, 0, f"Total: {total_imgs}", va='center', fontsize=12, fontweight='bold')
    plt.xlabel("Số lượng ảnh")
    plt.title("Phân bố tổng số ảnh theo từng tập dữ liệu")
    plt.legend(loc='upper left', bbox_to_anchor=(1.0, 1.0))
    plt.grid(axis='x', linestyle='--', alpha=0.4)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "horizontal_bar_dataset_distribution.png"))
    plt.close()