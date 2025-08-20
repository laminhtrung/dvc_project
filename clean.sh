#!/bin/bash
set -euo pipefail

echo "======================================"
echo " 🧹 DỌN DẸP TAG + DVC CACHE"
echo "======================================"

# ========================
# 1) XÓA GIT TAG (local + remote)
# ========================
echo "📌 Fetch và đồng bộ tags từ remote..."
git fetch --tags --prune origin || true

echo "🧹 Xóa toàn bộ tag LOCAL..."
git tag -l | xargs -r git tag -d

echo "🧹 Xóa toàn bộ tag REMOTE trên origin..."
# Lấy danh sách tag từ remote, lọc ra tên, rồi xóa từng cái
git ls-remote --tags origin | awk '{print $2}' | sed 's@refs/tags/@@' | while read -r tag; do
  if [[ -n "$tag" ]]; then
    echo "   - Xóa remote tag: $tag"
    git push --delete origin "$tag" || true
  fi
done

# Kiểm tra lại
echo "📌 Kiểm tra lại tags sau khi xóa:"
echo "Local tags:"
git tag -l || true
echo "Remote tags:"
git ls-remote --tags origin || true

# ========================
# 2) DỌN DẸP DVC CACHE
# ========================
echo "🗑️  Xóa thư mục .dvc/cache local..."
rm -rf .dvc/cache || true

echo "🧹 Dọn các file cache không cần thiết trong workspace..."
dvc gc -w -f || true

# Nếu muốn dọn cả cache trên remote (MinIO/S3), bỏ comment dòng dưới:
# dvc gc -w -c -f || true

# ========================
# 3) LOẠI BỎ .dvc/cache KHỎI GIT INDEX (nếu lỡ add)
# ========================
if git ls-files --error-unmatch .dvc/cache >/dev/null 2>&1; then
  echo "🧾 .dvc/cache đang bị track → gỡ khỏi index..."
  git rm -r --cached .dvc/cache
  git commit -m "chore: remove .dvc/cache from git index"
fi

# Đảm bảo .gitignore có dòng ignore cache
if ! grep -qxE '^\.dvc/cache/?$' .gitignore 2>/dev/null; then
  echo ".dvc/cache/" >> .gitignore
  git add .gitignore
  git commit -m "chore: ignore .dvc/cache" || true
fi

echo "======================================"
echo " ✅ HOÀN TẤT DỌN DẸP"
echo "======================================"
