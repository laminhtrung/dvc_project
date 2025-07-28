export MINIO_ENDPOINT="http://0.0.0.0:9000"
export MINIO_ACCESS_KEY="HEw4SbEVuUSOEQiaEmUH"
export MINIO_SECRET_KEY="HYXz5qby7b9v2nh5DpzWqexkHPGNdinXPbMJy0VX"
export MINIO_BUCKET="ivadatasets"

python crawler_fixed.py \
       --query "dog and cat" \
       --num-image 20 \
       --prefix "dogsandcats/"
