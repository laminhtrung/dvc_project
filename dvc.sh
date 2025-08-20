#!/bin/bash
set -euo pipefail

# ==============================================================================
# Step 0: Ensure git remote and fetch tags
# ==============================================================================
if ! git remote | grep -q "^origin$"; then
  echo "🛰️  Git remote 'origin' chưa có. Thêm vào..."
  git remote add origin https://github.com/laminhtrung/dvc_project.git
fi

# Fetch tags from remote so we see latest state
git fetch --tags origin || true

# ==============================================================================
# Helper: get next version across local + remote for both labeled/augmented
# ==============================================================================
get_next_version() {
  # Collect numbers from both prefixes locally
  local local_labeled local_aug remote_labeled remote_aug
  local_labeled=$(git tag -l "labeled_v*"   | sed -E 's/^labeled_v([0-9]+)$/\1/'   || true)
  local_aug=$(    git tag -l "augmented_v*" | sed -E 's/^augmented_v([0-9]+)$/\1/' || true)

  # Collect numbers from both prefixes remotely
  remote_labeled=$(git ls-remote --tags origin "labeled_v*"   | awk '{print $2}' | sed -E 's@refs/tags/labeled_v([0-9]+).*@\1@'   || true)
  remote_aug=$(    git ls-remote --tags origin "augmented_v*" | awk '{print $2}' | sed -E 's@refs/tags/augmented_v([0-9]+).*@\1@' || true)

  # Merge all, keep only integers
  all_versions=$(printf "%s\n%s\n%s\n%s\n" "$local_labeled" "$local_aug" "$remote_labeled" "$remote_aug" \
    | grep -E '^[0-9]+$' || true)

  if [[ -z "${all_versions}" ]]; then
    echo 1
  else
    # next = max + 1
    echo "$all_versions" | sort -nr | head -n1 | awk '{print $1 + 1}'
  fi
}

# Check a tag availability both local & remote
tag_available() {
  local tag="$1"
  # local exists?
  if git show-ref --tags --quiet "refs/tags/${tag}"; then
    return 1
  fi
  # remote exists?
  if [[ $(git ls-remote --tags origin "${tag}" | wc -l) -gt 0 ]]; then
    return 1
  fi
  return 0
}

# Find a free tag name by bumping the version if needed
find_free_tag() {
  local base_prefix="$1"  # labeled_v or augmented_v
  local v="$2"            # starting number
  local candidate="${base_prefix}${v}"
  while ! tag_available "${candidate}"; do
    v=$((v + 1))
    candidate="${base_prefix}${v}"
  done
  echo "${candidate}"
}

version=$(get_next_version)
echo "🔖 Version khởi điểm: v${version}"

created_tags=()

# ==============================================================================
# Step 1: Crawl data
# ==============================================================================
echo "🕷️  Crawling data..."
pushd crawler >/dev/null
python crawler.py
popd >/dev/null

# ==============================================================================
# Step 2: Labeling stage
# ==============================================================================
echo "🏷️  Running 'autolabel'..."
python auto_label/autolabel.py

echo "📌 DVC add labeled data..."
dvc add data/labeled || echo "⚠️  DVC add failed hoặc không có file mới"

echo "📦 Commit to Git (labeled)..."
git add data/labeled.dvc dvc.lock data/.gitignore || true
if git diff --staged --quiet; then
  echo "❗ Không có thay đổi để commit cho labeled data → sẽ bỏ qua tag labeled"
  labeled_commit_done=0
else
  git commit -m "v${version}: Track labeled data with DVC"
  labeled_commit_done=1
fi

if [[ $labeled_commit_done -eq 1 ]]; then
  labeled_tag=$(find_free_tag "labeled_v" "${version}")
  git tag -a "${labeled_tag}" -m "Version ${labeled_tag#labeled_v}: Labeled data"
  created_tags+=("${labeled_tag}")
  echo "✅ Tạo tag: ${labeled_tag}"
fi

# ==============================================================================
# Step 3: Augmentation stage
# ==============================================================================
echo "🧪 Running 'augment_data'..."
python processing/preprocess.py

echo "📌 DVC add augmented data..."
dvc add data/processed || echo "⚠️  DVC add failed hoặc không có file mới"

echo "📦 Commit to Git (augmented)..."
git add data/processed.dvc dvc.lock data/.gitignore || true
if git diff --staged --quiet; then
  echo "❗ Không có thay đổi để commit cho augmented data → sẽ bỏ qua tag augmented"
  augmented_commit_done=0
else
  git commit -m "v${version}: Track augmented data with DVC"
  augmented_commit_done=1
fi

if [[ $augmented_commit_done -eq 1 ]]; then
  # Recompute next free version only if labeled didn't reserve it,
  # but we simply find the next available tag name for augmented prefix.
  augmented_tag=$(find_free_tag "augmented_v" "${version}")
  git tag -a "${augmented_tag}" -m "Version ${augmented_tag#augmented_v}: Augmented data"
  created_tags+=("${augmented_tag}")
  echo "✅ Tạo tag: ${augmented_tag}"
fi

# ==============================================================================
# Step 4: Push to DVC + Git remote
# ==============================================================================
echo "🔧 Config DVC remote (MinIO)..."
dvc remote add -f -d myremote s3://data
dvc remote modify myremote endpointurl http://0.0.0.0:9000
dvc remote modify myremote access_key_id minioadmin
dvc remote modify myremote secret_access_key minioadmin

echo "⬆️  DVC push..."
if ! dvc push; then
  echo "⚠️  DVC push failed (bỏ qua, tiếp tục Git push)"
fi

echo "⬆️  Git push main..."
git push origin HEAD:main || echo "⚠️  Git push main failed"

# Push only the tags created in this run
if [[ ${#created_tags[@]} -gt 0 ]]; then
  echo "⬆️  Git push các tag mới: ${created_tags[*]}"
  for t in "${created_tags[@]}"; do
    git push origin "refs/tags/${t}" || echo "⚠️  Push tag ${t} failed"
  done
else
  echo "ℹ️  Không có tag mới để push."
fi

echo "🎉 Done."
