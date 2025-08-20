import logging
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler

# Tạo thư mục logs nếu chưa có
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Tạo logger
logger = logging.getLogger("pipeline_logger")
logger.setLevel(logging.INFO)

# Ghi log xoay vòng theo ngày
file_handler = TimedRotatingFileHandler(
    log_dir / "pipeline.log", when="midnight", backupCount=7, encoding="utf-8"
)
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

# In log ra console
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("%(message)s"))

# Tránh thêm handler nhiều lần
if not logger.handlers:
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

