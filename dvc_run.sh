#!/bin/bash
set -e

# ==============================================================================
# Step 1: Crawl data
# ==============================================================================
cd crawler
python crawler.py
cd ..

# ==============================================================================
# Helper: Lấy version kế tiếp (dựa trên tag Git)
# ==============================================================================
get_next_version() {
    existing_tags=$(git tag -l "labeled_v*" | sed 's/labeled_v//' | sort -nr)
    if [[ -z "$existing_tags" ]]; then
        echo 1
    else
        next=$(( $(echo "$existing_tags" | head -n1) + 1 ))
        echo $next
    fi
}

version=$(get_next_version)
echo "🔖 Version tiếp theo: v$version"

# ==============================================================================
# Step 2: Reproduce labeling stage
# ==============================================================================

# Bỏ tracking git data/labeled trước khi repro autolabel (đảm bảo Git không theo dõi thư mục output)
git rm -r --cached 'data/labeled' || true   # thêm || true để tránh lỗi nếu chưa track
git commit -m "stop tracking data/labeled" || true # tránh lỗi commit nếu không có thay đổi

echo "🏷️  Đang chạy 'autolabel' stage..."
dvc repro autolabel

# commit output (dvc.lock + .gitignore) sau khi repro để theo dõi chính xác output
echo "📌 Commit output data/labeled vào DVC..."
dvc commit

echo "📦 Thêm dvc.lock, .gitignore và commit vào Git..."
git add dvc.lock data/.gitignore
git commit -m "v$version: Labeled and split raw data"

git tag -f "labeled_v$version" -m "Version $version: Labeled data"

# ==============================================================================
# Step 3: Reproduce augmentation stage
# ==============================================================================
echo "🧪 Đang chạy 'augment_data' stage..."
dvc repro augment_data  # Tự động thực thi stage augment_data từ dvc.yaml

# Xoá stage đang track riêng 'images'
dvc remove augment_data

# Track toàn bộ thư mục
dvc add data/processed/train

# Commit lại DVC
git add data/processed/train.dvc .gitignore
git commit -m "v$version: Track full augmented train directory"
dvc commit
git tag -f "augmented_v$version" -m "Version $version: Full train dir"




# ==============================================================================
# Step 4: Push to DVC remote + Git remote
# ==============================================================================
dvc remote add -f -d myremote s3://data
dvc remote modify myremote endpointurl http://localhost:9000
dvc remote modify myremote access_key_id minioadmin
dvc remote modify myremote secret_access_key minioadmin


echo "⬆️  Đẩy dữ liệu lên DVC remote (MinIO)..."
dvc push -r minio_remote

echo "⬆️  Đẩy code + tag lên Git remote..."
if ! git remote | grep -q "origin"; then
    echo "🛰️  Remote 'origin' chưa tồn tại. Thêm vào..."
    git remote add origin https://github.com/laminhtrung/dvc_project.git
fi

git push -u origin main --tags
