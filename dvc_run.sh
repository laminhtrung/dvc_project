dvc remote add -d minio_remote s3://data
dvc remote modify minio_remote endpointurl  http://0.0.0.0:9000
dvc remote modify minio_remote access_key_id minioadmin
dvc remote modify minio_remote secret_access_key minioadmin

git config user.email "laminhtrung2001@gmail.com"
git config user.name "lamnhtrung"

git commit -m "Version 0: Add raw data"
dvc add data
git add data.dvc 
git tag v1

dvc push

git remote add origin https://github.com/laminhtrung/dvc_project.git
git branch -M main
git push -u origin main --tags