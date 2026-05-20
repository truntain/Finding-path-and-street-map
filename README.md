# Ứng Dụng Thuật Toán A* Trên Bản Đồ Thực Tế

⭐ **Ứng Dụng Thuật Toán A* Trên Bản Đồ Thực Tế Sử Dụng OSMnx và NetworkX**
📌 *Đồ án môn học - Nhập môn Trí tuệ Nhân tạo (Trường CNTT&TT, ĐHBKHN)*

---

## 📌 Tổng Quan

Dự án này triển khai **Thuật toán Tìm kiếm A\*** trên bản đồ thực tế sử dụng dữ liệu từ **OpenStreetMap (OSM)**. Đồ thị mạng lưới đường được xây dựng bằng thư viện **OSMnx** và **NetworkX**. Thuật toán A\* được áp dụng để tìm đường đi ngắn nhất giữa hai điểm trên mạng lưới giao thông thực tế (ví dụ: Hà Nội, Việt Nam).

---

## 📂 Tính Năng

✅ **Xây dựng Đồ thị từ Dữ liệu OSM**: 
   - Trích xuất mạng lưới đường thực tế.

✅ **Triển khai Thuật toán A\***: 
   - Tự cài đặt thuật toán A\* mà không sử dụng các hàm tìm đường đi ngắn nhất có sẵn.

✅ **Trực quan hóa**: 
   - Hiển thị đồ thị và đường đi ngắn nhất được tính toán.

✅ **Giao diện Web tương tác**: 
   - Cho phép người dùng chọn điểm đầu, cuối và thuật toán trên bản đồ trực quan.
   - (Thông qua file `Deploy.py` sử dụng Flask và Leaflet).

✅ **So sánh Thuật toán**: 
   - Cung cấp khả năng so sánh A\* với các thuật toán tìm đường khác như UCS (Dijkstra), Greedy BFS và DFS.

---

## 📊 Thuộc Tính Dữ Liệu Đường & Mô Tả

| Thuộc Tính | Mô Tả                                      |
| :--------- | :----------------------------------------- |
| **osmid** | ID của đoạn đường trong OpenStreetMap      |
| **highway**| Loại đường (khu dân cư, quốc lộ, v.v.)     |
| **oneway** | Cho biết đường có phải một chiều hay không   |
| **reversed**| Chiều của đường khi được tải từ OSM (True nếu ngược với chiều vẽ ban đầu) |
| **length** | Chiều dài đoạn đường (mét)                 |
| **geometry**| Dữ liệu GPS của đoạn đường (dạng LINESTRING) |
| **lanes** | Số làn đường                              |
| **name** | Tên đường (nếu có)                         |

---

## 📌 Công Nghệ Sử Dụng

-   **Python** 🐍
-   **OSMnx** 🌍 (Trích xuất mạng lưới đường thực tế từ OSM)
-   **NetworkX** 🔗 (Biểu diễn đồ thị và hỗ trợ các thao tác trên đồ thị)
-   **Matplotlib** 📊 (Trực quan hóa đồ thị trong Jupyter Notebook - `A_star.ipynb`)
-   **Flask** 🌐 (Xây dựng backend cho ứng dụng web - `Deploy.py`)
-   **Leaflet.js** 🗺️ (Hiển thị bản đồ và tương tác trên frontend - `index.html`)
-   **NumPy** (Tính toán số học, thường được OSMnx/NetworkX sử dụng)
-   **GeoPandas, Shapely** (Xử lý dữ liệu địa lý, được OSMnx sử dụng)

---

## 🚀 Cách Chạy Ứng Dụng Web

1.  **Cài đặt các thư viện cần thiết:**
    ```bash
    pip install osmnx networkx matplotlib numpy flask geopandas shapely
    ```

2.  **Chuẩn bị file dữ liệu bản đồ:**
    * Đảm bảo bạn có file `hanoi_inner_city_polygon_combined.graphml` trong cùng thư mục với `Deploy.py` (hoặc file `.graphml` tương ứng với khu vực bạn muốn sử dụng).
    * File này có thể được tạo ra từ notebook `A_star.ipynb` bằng cách sử dụng OSMnx để tải và lưu dữ liệu từ OpenStreetMap cho khu vực mong muốn.

3.  **Chạy ứng dụng Flask:**
    Mở terminal hoặc command prompt, điều hướng đến thư mục chứa dự án và chạy lệnh:
    ```bash
    python Deploy.py
    ```
    Ứng dụng sẽ chạy trên cổng 8000 theo mặc định.

4.  **Truy cập ứng dụng:**
    Mở trình duyệt web và truy cập vào địa chỉ `http://127.0.0.1:8000`.

5.  **Sử dụng Giao diện:**
    * Click vào bản đồ để chọn điểm bắt đầu và điểm kết thúc.
    * Hoặc sử dụng thanh tìm kiếm địa chỉ để chọn điểm.
    * Chọn thuật toán mong muốn từ danh sách thả xuống.
    * Nhấn nút "Reset Points" để chọn lại điểm.
    * Đường đi và thông tin (chiều dài, số nút duyệt, thời gian thực thi) sẽ được hiển thị.

---

---