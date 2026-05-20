from flask import Flask, render_template, request, jsonify
import osmnx as ox
# import time # shortest_path.py đã xử lý thời gian

# Import các hàm cần thiết từ shortest_path.py
from Algo import (
    Create_simple_Graph,
    A_star,
    DFS_search,
    Greedy_best_first_search,
    Dijkstra
    # Đảm bảo rằng shortest_path.py cũng có các hàm phụ trợ như
    # h1, reconstruct_path_nodes, Create_path_coord, calculate_actual_path_length
    # và các hàm thuật toán đã được cập nhật để trả về 4 giá trị.
)

app = Flask(__name__)

# Tải bản đồ và tạo đồ thị đơn giản một lần khi ứng dụng khởi động
try:
    hanoi_inner_city_polygon_combined_map = ox.load_graphml('noithanh_HaNoi.graphml')
    G_simple = Create_simple_Graph(hanoi_inner_city_polygon_combined_map) # Hàm này cần đối tượng bản đồ từ osmnx
except FileNotFoundError:
    print("LỖI NGHIÊM TRỌNG: Không tìm thấy file noithanh_HaNoi.graphml. Ứng dụng không thể khởi động.")
    hanoi_inner_city_polygon_combined_map = None
    G_simple = {}
except Exception as e:
    print(f"Lỗi khi tải bản đồ hoặc tạo đồ thị đơn giản: {e}")
    hanoi_inner_city_polygon_combined_map = None
    G_simple = {}

@app.route('/')
def index_route(): # Đổi tên hàm để tránh trùng với module index (nếu có)
    if not hanoi_inner_city_polygon_combined_map:
        return "Lỗi: Dữ liệu bản đồ không tải được.", 500

    node_coords = []
    if hanoi_inner_city_polygon_combined_map and hanoi_inner_city_polygon_combined_map.nodes:
        node_coords = [(data['y'], data['x']) for node, data in hanoi_inner_city_polygon_combined_map.nodes(data=True)]
    
    all_edge_paths_coords = []
    if hanoi_inner_city_polygon_combined_map and hanoi_inner_city_polygon_combined_map.edges:
        for u, v, data in hanoi_inner_city_polygon_combined_map.edges(data=True):
            if 'geometry' in data:
                # LineString có thể chứa nhiều điểm, tạo ra các đoạn nhỏ hơn
                xs, ys = data['geometry'].xy
                edge_segment_coords = list(zip(ys, xs)) # List các (lat, lon)
                if len(edge_segment_coords) >= 2:
                     # Leaflet polyline nhận mảng các [lat, lng]
                    all_edge_paths_coords.append(edge_segment_coords)
            else:
                # Fallback nếu không có geometry, vẽ đường thẳng giữa 2 node
                if u in hanoi_inner_city_polygon_combined_map.nodes and v in hanoi_inner_city_polygon_combined_map.nodes:
                    coord_u = (hanoi_inner_city_polygon_combined_map.nodes[u]['y'], hanoi_inner_city_polygon_combined_map.nodes[u]['x'])
                    coord_v = (hanoi_inner_city_polygon_combined_map.nodes[v]['y'], hanoi_inner_city_polygon_combined_map.nodes[v]['x'])
                    all_edge_paths_coords.append([coord_u, coord_v])
                    
    return render_template('index.html', node_coords=node_coords, path_coords=all_edge_paths_coords)

algorithm_list = {
    'Dijkstra': Dijkstra,
    'A Star': A_star,
    'DFS': DFS_search,
    'BFS': Greedy_best_first_search,
}

@app.route('/find_shortest_path', methods=['POST'])
def find_shortest_path_route_handler(): # Đổi tên hàm
    if not hanoi_inner_city_polygon_combined_map or not G_simple:
        return jsonify({"error": "Dữ liệu bản đồ hoặc đồ thị chưa được tải trên server."}), 500

    data = request.json
    start_coords_input = data['start']  # Định dạng mong đợi: [lat, lon]
    end_coords_input = data['end']
    algorithm_name = data['algorithm']
    
    # max_depth không được sử dụng bởi các thuật toán hiện tại
    # max_depth = int(data.get('max_depth', 0)) 

    try:
        # ox.distance.nearest_nodes nhận (G, X=lon, Y=lat)
        start_node_id = ox.distance.nearest_nodes(hanoi_inner_city_polygon_combined_map, X=start_coords_input[1], Y=start_coords_input[0])
        end_node_id = ox.distance.nearest_nodes(hanoi_inner_city_polygon_combined_map, X=end_coords_input[1], Y=end_coords_input[0])
    except Exception as e:
        print(f"Lỗi khi tìm node gần nhất: {e}")
        return jsonify({"error": "Không tìm thấy node trên bản đồ cho tọa độ đã cho."}), 400
    
    selected_algorithm_func = algorithm_list.get(algorithm_name)
    if not selected_algorithm_func:
        return jsonify({"error": "Thuật toán không hợp lệ."}), 400

    # Gọi hàm thuật toán từ shortest_path.py
    # Các hàm này giờ được mong đợi trả về:
    # (path_coordinates, nodes_expanded, execution_time, total_actual_distance)
    try:
        path_coordinates_result, nodes_expanded, execution_time, total_distance_val = selected_algorithm_func(
            G_simple, start_node_id, end_node_id, hanoi_inner_city_polygon_combined_map # Truyền hanoi_inner_city_polygon_combined_map
        )
    except ValueError:
         # Xử lý trường hợp hàm thuật toán chưa được cập nhật để trả về 4 giá trị
        print(f"LƯU Ý: Thuật toán {algorithm_name} chưa trả về đủ 4 giá trị (thiếu total_distance).")
        try:
            path_coordinates_result, nodes_expanded, execution_time = selected_algorithm_func(
                G_simple, start_node_id, end_node_id, hanoi_inner_city_polygon_combined_map
            )
            total_distance_val = "N/A (tính toán bị thiếu)" # Đánh dấu là thiếu
        except Exception as e:
            print(f"Lỗi khi thực thi thuật toán {algorithm_name}: {e}")
            return jsonify({"error": f"Lỗi trong thuật toán {algorithm_name}."}), 500
    except Exception as e:
        print(f"Lỗi không xác định khi thực thi thuật toán {algorithm_name}: {e}")
        return jsonify({"error": "Lỗi server không xác định khi tìm đường."}), 500


    print(f"Thuật toán: {algorithm_name}, Điểm đầu ID: {start_node_id}, Điểm cuối ID: {end_node_id}")
    print(f"Đường đi được tìm thấy: {'Có' if path_coordinates_result else 'Không'}")
    if path_coordinates_result:
        print(f"Tổng quãng đường: {total_distance_val if isinstance(total_distance_val, (int, float)) else 'N/A'} m")
    print(f"Số nút đã duyệt: {nodes_expanded}, Thời gian thực thi: {execution_time:.6f}s")

    if path_coordinates_result is None or not path_coordinates_result:
        return jsonify({"error": "Không tìm thấy đường đi."}), 404

    start_node_actual_coords = (hanoi_inner_city_polygon_combined_map.nodes[start_node_id]['y'], hanoi_inner_city_polygon_combined_map.nodes[start_node_id]['x'])
    end_node_actual_coords = (hanoi_inner_city_polygon_combined_map.nodes[end_node_id]['y'], hanoi_inner_city_polygon_combined_map.nodes[end_node_id]['x'])
    
    start_connection_line = [start_node_actual_coords, (start_coords_input[0], start_coords_input[1])]
    end_connection_line = [end_node_actual_coords, (end_coords_input[0], end_coords_input[1])]
    
    return jsonify({
        'path_coords': path_coordinates_result,
        # 'max_depth': max_depth, # Vẫn trả về nếu client cần
        'start_path_segment': start_connection_line, # Đổi tên key để rõ ràng hơn
        'end_path_segment': end_connection_line,     # Đổi tên key
        'nodes_expanded': nodes_expanded,
        'execution_time': round(execution_time, 6),
        'total_distance': f"{total_distance_val:.2f} m" if isinstance(total_distance_val, (int, float)) else total_distance_val
    })

if __name__ == '__main__':
    app.run(debug=True, port=8000)
    