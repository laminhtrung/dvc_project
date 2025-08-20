import numpy as np
import matplotlib.pyplot as plt

# Định nghĩa hàm z(x, y)
def z_func(x, y):
    return (339 - 0.01*x - 0.003*y)*x + (339 - 0.004*x - 0.01*y)*y - (400000 + 195*x + 225*y)

# Tạo lưới giá trị x và y
x = np.linspace(0, 50000, 100)  # khoảng giá trị x
y = np.linspace(0, 50000, 100)  # khoảng giá trị y
X, Y = np.meshgrid(x, y)        # tạo lưới
Z = z_func(X, Y)                # tính giá trị z trên lưới

# Vẽ surface 3D
fig = plt.figure(figsize=(10, 7))
ax = fig.add_subplot(111, projection='3d')
surf = ax.plot_surface(X, Y, Z, cmap='viridis', edgecolor='none')

# Gán nhãn trục và tiêu đề
ax.set_xlabel('x')
ax.set_ylabel('y')
ax.set_zlabel('z')
ax.set_title('3D Surface of z(x, y)')

# Thêm thanh màu
fig.colorbar(surf, shrink=0.5, aspect=5)

# Lưu ảnh
plt.savefig("z_surface.png", dpi=300, bbox_inches='tight')

# Hiển thị
plt.show()

import numpy as np

# Hàm z(x, y)
def z_func(x, y):
    return (339 - 0.01*x - 0.003*y)*x + (339 - 0.004*x - 0.01*y)*y - (400000 + 195*x + 225*y)

# --- Bước 1: Quét thô để tìm vùng cực đại ---
step = 1  # bước nhảy (chỉnh nhỏ để chính xác hơn)
x_range = range(0, 50001, step)
y_range = range(0, 50001, step)

max_z = -float('inf')
best_x = 0
best_y = 0

for x in x_range:
    for y in y_range:
        z_val = z_func(x, y)
        if z_val > max_z:
            max_z = z_val
            best_x = x
            best_y = y

print(f"[Quét thô] x={best_x}, y={best_y}, z={max_z}")

# --- Bước 2: Quét chi tiết quanh điểm tốt nhất ---
search_range_x = range(max(0, best_x - step), min(50000, best_x + step) + 1)
search_range_y = range(max(0, best_y - step), min(50000, best_y + step) + 1)

for x in search_range_x:
    for y in search_range_y:
        z_val = z_func(x, y)
        if z_val > max_z:
            max_z = z_val
            best_x = x
            best_y = y

print(f"[Kết quả chính xác] x={best_x}, y={best_y}, z={max_z}")
