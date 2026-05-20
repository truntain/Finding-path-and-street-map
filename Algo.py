import numpy as np
import heapq
import osmnx as ox
from math import radians, cos, sqrt
import time


try:
    maps_data = ox.load_graphml('noithanh_HaNoi.graphml')
except FileNotFoundError:
    print("Lỗi: Không tìm thấy file noithanh_HaNoi.graphml. Hãy đảm bảo file tồn tại.")
    maps_data = None
except Exception as e:
    print(f"Lỗi khi tải maps_data: {e}")
    maps_data = None

def Create_path_coord(path_nodes, current_maps_data):
    if not current_maps_data or not path_nodes or len(path_nodes) < 2:
        return []
    path_coords = []
    for i in range(len(path_nodes) - 1):
        u, v = path_nodes[i], path_nodes[i+1]
        # Đảm bảo node u và v có trong current_maps_data.nodes trước khi truy cập
        if u in current_maps_data.nodes and v in current_maps_data.nodes:
            # Kiểm tra xem node có thuộc tính 'y' và 'x' không
            if 'y' in current_maps_data.nodes[u] and 'x' in current_maps_data.nodes[u] and \
               'y' in current_maps_data.nodes[v] and 'x' in current_maps_data.nodes[v]:
                coord_u = (current_maps_data.nodes[u]['y'], current_maps_data.nodes[u]['x'])
                coord_v = (current_maps_data.nodes[v]['y'], current_maps_data.nodes[v]['x'])
                path_coords.append([coord_u, coord_v])
            else:
                # print(f"Cảnh báo: Node {u} hoặc {v} thiếu thuộc tính tọa độ.")
                return [] # Trả về rỗng nếu có lỗi dữ liệu node
        else:
            # print(f"Cảnh báo: Node {u} hoặc {v} không tồn tại trong bản đồ khi tạo tọa độ.")
            return [] # Trả về rỗng nếu có lỗi
    return path_coords

def Create_simple_Graph(current_maps_data):
    if not current_maps_data:
        return {}
    Edges = list(current_maps_data.edges(data=True, keys=True))
    Graph = {node: [] for node in current_maps_data.nodes}

    for u, v, k, data in Edges:
        length = data.get('length')
        if length is not None:
            # Đảm bảo u và v là các node hợp lệ trong Graph đã khởi tạo
            if u in Graph and v in Graph:
                 Graph[u].append([v, length])
            # else:
                # print(f"Cảnh báo: Node {u} hoặc {v} từ cạnh không có trong danh sách node của đồ thị.")
    return Graph

def h1(current, goal, current_maps_data):
    if not current_maps_data:
        return float('inf')
    if current not in current_maps_data.nodes or goal not in current_maps_data.nodes:
        return float('inf')
    # Kiểm tra node có thuộc tính tọa độ không
    if not ('y' in current_maps_data.nodes[current] and 'x' in current_maps_data.nodes[current] and \
            'y' in current_maps_data.nodes[goal] and 'x' in current_maps_data.nodes[goal]):
        # print(f"Cảnh báo: Node {current} hoặc {goal} thiếu thuộc tính tọa độ cho h1.")
        return float('inf')

    lat1 = current_maps_data.nodes[current]['y']
    lon1 = current_maps_data.nodes[current]['x']
    lat2 = current_maps_data.nodes[goal]['y']
    lon2 = current_maps_data.nodes[goal]['x']
    lat_mean = radians((lat1 + lat2) / 2)
    dx = (lon2 - lon1) * 111320 * cos(lat_mean)
    dy = (lat2 - lat1) * 111320
    return sqrt(dx**2 + dy**2)

def calculate_actual_path_length(path_node_ids, simple_graph):
    if not path_node_ids or len(path_node_ids) < 2:
        return 0.0
    total_length = 0.0
    for i in range(len(path_node_ids) - 1):
        u_node = path_node_ids[i]
        v_node = path_node_ids[i+1]
        edge_found = False
        if u_node in simple_graph:
            for neighbor_node, cost in simple_graph[u_node]:
                if neighbor_node == v_node:
                    if isinstance(cost, (int, float)): # Đảm bảo cost là số
                        total_length += cost
                        edge_found = True
                        break
                    else:
                        # print(f"Cảnh báo: Chi phí cạnh giữa {u_node} và {v_node} không phải là số: {cost}")
                        return float('inf') 
            if not edge_found:
                # print(f"CẢNH BÁO: Không tìm thấy cạnh giữa {u_node} và {v_node} trong simple_graph khi tính chiều dài.")
                return float('inf')
        else:
            # print(f"CẢNH BÁO: Node {u_node} không có trong simple_graph khi tính chiều dài.")
            return float('inf')
    return total_length

def reconstruct_path_nodes(came_from, current_node):
    total_path_nodes = [current_node]
    # Kiểm tra current_node có phải là list không (để debug lỗi unhashable)
    # print(f"reconstruct_path_nodes - current_node type: {type(current_node)}, value: {current_node}")
    while current_node in came_from: # came_from keys phải là hashable (node_id)
        current_node = came_from[current_node]
        total_path_nodes.append(current_node)
    total_path_nodes.reverse()
    return total_path_nodes

def reconstruct_path_coords(came_from, current_node, current_maps_data):
    path_nodes = reconstruct_path_nodes(came_from, current_node)
    return Create_path_coord(path_nodes, current_maps_data)

def path_to_edges(path_nodes):
    if not path_nodes or len(path_nodes) < 2:
        return []
    return [(path_nodes[i], path_nodes[i + 1]) for i in range(len(path_nodes) - 1)]

# --- CÁC HÀM THUẬT TOÁN ĐÃ SỬA ---

def A_star(graph_simple, start, goal, current_maps_data=maps_data):
    if not current_maps_data or start not in graph_simple or goal not in graph_simple:
        return None, 0, 0.0, 0.0

    start_time = time.perf_counter()
    nodes_expanded = 0
    open_set = []
    heapq.heappush(open_set, (h1(start, goal, current_maps_data), start))
    came_from = {}
    g_score = {node: float('inf') for node in graph_simple}
    g_score[start] = 0
    f_score = {node: float('inf') for node in graph_simple}
    f_score[start] = h1(start, goal, current_maps_data)

    while open_set:
        current_f_val, current_node = heapq.heappop(open_set)
        # print(f"A* current_node: {current_node}, type: {type(current_node)}") # DEBUG
        if not isinstance(current_node, (int, str, np.integer, np.int64, np.int32)): # Đảm bảo current_node là hashable
            print(f"A* LỖI: current_node là unhashable: {current_node} type {type(current_node)}")
            return None, nodes_expanded, time.perf_counter() - start_time, 0.0

        if current_f_val > f_score[current_node]:
            continue
        nodes_expanded += 1

        if current_node == goal:
            execution_time = time.perf_counter() - start_time
            path_node_ids_result = reconstruct_path_nodes(came_from, current_node) # Lấy node IDs
            path_coordinates = Create_path_coord(path_node_ids_result, current_maps_data) # Tạo coords từ node IDs
            total_distance_val = calculate_actual_path_length(path_node_ids_result, graph_simple) # Tính length từ node IDs
            return path_coordinates, nodes_expanded, execution_time, total_distance_val

        for neighbor_data in graph_simple.get(current_node, []):
            neighbor_node = neighbor_data[0]
            # print(f"A* neighbor_node: {neighbor_node}, type: {type(neighbor_node)}") # DEBUG
            if not isinstance(neighbor_node, (int, str, np.integer, np.int64, np.int32)): # Đảm bảo neighbor_node là hashable
                print(f"A* LỖI: neighbor_node là unhashable: {neighbor_node} type {type(neighbor_node)}")
                continue # Bỏ qua neighbor này nếu nó không hợp lệ

            cost = neighbor_data[1]
            if not isinstance(cost, (int, float)): # Đảm bảo cost là số
                # print(f"A* Cảnh báo: Chi phí không hợp lệ {cost} cho cạnh đến {neighbor_node}")
                continue

            tentative_g_score = g_score[current_node] + cost
            if tentative_g_score < g_score[neighbor_node]:
                came_from[neighbor_node] = current_node
                g_score[neighbor_node] = tentative_g_score
                f_score[neighbor_node] = tentative_g_score + h1(neighbor_node, goal, current_maps_data)
                heapq.heappush(open_set, (f_score[neighbor_node], neighbor_node))

    execution_time = time.perf_counter() - start_time
    return None, nodes_expanded, execution_time, 0.0

def Greedy_best_first_search(graph_simple, start, goal, current_maps_data=maps_data):
    if not current_maps_data or start not in graph_simple or goal not in graph_simple:
        return None, 0, 0.0, 0.0 # Thêm total_distance_val = 0.0

    start_time = time.perf_counter()
    nodes_expanded = 0
    open_set = []
    heapq.heappush(open_set, (h1(start, goal, current_maps_data), start))
    came_from = {}
    visited_nodes = {start}

    while open_set:
        _, current_node = heapq.heappop(open_set)
        # print(f"Greedy current_node: {current_node}, type: {type(current_node)}") # DEBUG
        if not isinstance(current_node, (int, str, np.integer, np.int64, np.int32)):
            print(f"Greedy LỖI: current_node là unhashable: {current_node} type {type(current_node)}")
            return None, nodes_expanded, time.perf_counter() - start_time, 0.0

        nodes_expanded += 1

        if current_node == goal:
            execution_time = time.perf_counter() - start_time
            path_node_ids_result = reconstruct_path_nodes(came_from, current_node)
            path_coordinates = Create_path_coord(path_node_ids_result, current_maps_data)
            total_distance_val = calculate_actual_path_length(path_node_ids_result, graph_simple)
            return path_coordinates, nodes_expanded, execution_time, total_distance_val

        for neighbor_data in graph_simple.get(current_node, []):
            neighbor_node = neighbor_data[0]
            # print(f"Greedy neighbor_node: {neighbor_node}, type: {type(neighbor_node)}") # DEBUG
            if not isinstance(neighbor_node, (int, str, np.integer, np.int64, np.int32)):
                print(f"Greedy LỖI: neighbor_node là unhashable: {neighbor_node} type {type(neighbor_node)}")
                continue

            if neighbor_node not in visited_nodes:
                visited_nodes.add(neighbor_node) # Add hashable node_id
                came_from[neighbor_node] = current_node
                heapq.heappush(open_set, (h1(neighbor_node, goal, current_maps_data), neighbor_node))

    execution_time = time.perf_counter() - start_time
    return None, nodes_expanded, execution_time, 0.0

def UCS(graph_simple, start, goal, current_maps_data=maps_data):
    if not current_maps_data or start not in graph_simple or goal not in graph_simple:
        return None, 0, 0.0, 0.0

    start_time = time.perf_counter()
    nodes_expanded = 0
    open_set = []
    heapq.heappush(open_set, (0, start))
    came_from = {}
    g_score = {node: float('inf') for node in graph_simple}
    g_score[start] = 0

    while open_set:
        current_g, current_node = heapq.heappop(open_set)
        # print(f"UCS current_node: {current_node}, type: {type(current_node)}") # DEBUG
        if not isinstance(current_node, (int, str, np.integer, np.int64, np.int32)):
            print(f"UCS LỖI: current_node là unhashable: {current_node} type {type(current_node)}")
            return None, nodes_expanded, time.perf_counter() - start_time, 0.0

        if current_g > g_score[current_node]:
            continue
        nodes_expanded += 1

        if current_node == goal:
            execution_time = time.perf_counter() - start_time
            path_node_ids_result = reconstruct_path_nodes(came_from, current_node)
            path_coordinates = Create_path_coord(path_node_ids_result, current_maps_data)
            total_distance_val = calculate_actual_path_length(path_node_ids_result, graph_simple)
            return path_coordinates, nodes_expanded, execution_time, total_distance_val

        for neighbor_data in graph_simple.get(current_node, []):
            neighbor_node = neighbor_data[0]
            # print(f"UCS neighbor_node: {neighbor_node}, type: {type(neighbor_node)}") # DEBUG
            if not isinstance(neighbor_node, (int, str, np.integer, np.int64, np.int32)):
                print(f"UCS LỖI: neighbor_node là unhashable: {neighbor_node} type {type(neighbor_node)}")
                continue
            
            cost = neighbor_data[1]
            if not isinstance(cost, (int, float)):
                # print(f"UCS Cảnh báo: Chi phí không hợp lệ {cost} cho cạnh đến {neighbor_node}")
                continue

            tentative_g_score = g_score[current_node] + cost
            if tentative_g_score < g_score[neighbor_node]:
                came_from[neighbor_node] = current_node
                g_score[neighbor_node] = tentative_g_score
                heapq.heappush(open_set, (g_score[neighbor_node], neighbor_node))

    execution_time = time.perf_counter() - start_time
    return None, nodes_expanded, execution_time, 0.0

def Dijkstra(graph_simple, start, goal, current_maps_data=maps_data):
    if not current_maps_data or start not in graph_simple or goal not in graph_simple:
        return None, 0, 0.0, 0.0
    return UCS(graph_simple, start, goal, current_maps_data)
def DFS_search(graph_simple, start, goal, current_maps_data=maps_data):
    """
    Tìm đường đi từ start đến goal bằng thuật toán DFS.
    Không đảm bảo đường đi ngắn nhất.
    Trả về: (path_coordinates, nodes_expanded, execution_time, total_distance_val)
    """
    if not current_maps_data or start not in graph_simple or goal not in graph_simple:
        return None, 0, 0.0, 0.0

    start_time = time.perf_counter()
    nodes_expanded = 0
    
    # Stack lưu trữ các node cần duyệt
    # Mỗi phần tử trong stack là một tuple (node, parent_node) để dùng cho came_from
    open_stack = [(start, None)] 
    
    came_from = {} 
    visited_dfs = set() # Theo dõi các node đã được đưa vào stack để tránh chu trình và lặp lại

    path_node_ids_result = None

    while open_stack:
        current_node, parent_for_current = open_stack.pop() # Lấy từ cuối stack (LIFO)
        
        # Nếu node này đã được xử lý từ một đường khác (do có thể có nhiều đường dẫn đến 1 node trong DFS)
        # và chúng ta chỉ cần tìm 1 đường đi thì có thể bỏ qua.
        # Tuy nhiên, để came_from được ghi nhận đúng cho đường đi đầu tiên tìm thấy, 
        # ta sẽ kiểm tra visited_dfs khi thêm vào stack.
        # Nếu current_node đã có trong came_from nghĩa là nó đã có parent, không ghi đè.
        if current_node not in came_from and parent_for_current is not None:
             came_from[current_node] = parent_for_current
        
        # Nếu node này chưa được "mở rộng" thì mới xử lý
        if current_node in visited_dfs and current_node != start : # Cho phép xử lý start node lần đầu
            continue
        visited_dfs.add(current_node)
        nodes_expanded += 1


        if current_node == goal:
            execution_time = time.perf_counter() - start_time
            path_node_ids_result = reconstruct_path_nodes(came_from, current_node)
            path_coordinates = Create_path_coord(path_node_ids_result, current_maps_data)
            total_distance_val = calculate_actual_path_length(path_node_ids_result, graph_simple)
            return path_coordinates, nodes_expanded, execution_time, total_distance_val

        # Thêm các neighbors chưa được thăm vào stack
        # Đảo ngược thứ tự duyệt neighbors để stack.pop() hoạt động giống đệ quy (duyệt "sâu" theo thứ tự thông thường)
        for neighbor_data in reversed(graph_simple.get(current_node, [])):
            neighbor_node = neighbor_data[0]
            # Chỉ thêm vào stack nếu neighbor chưa được thăm (chưa được đưa vào stack trước đó)
            if neighbor_node not in visited_dfs: 
                # visited_dfs.add(neighbor_node) # Đánh dấu visited khi đưa vào stack để tránh thêm nhiều lần
                                              # Hoặc đánh dấu khi pop ra như hiện tại, tùy cách quản lý
                if neighbor_node not in came_from: # Chỉ ghi nhận parent đầu tiên
                    came_from[neighbor_node] = current_node
                open_stack.append((neighbor_node, current_node)) # Thêm cả parent để cập nhật came_from

    # Không tìm thấy đường đi
    execution_time = time.perf_counter() - start_time
    return None, nodes_expanded, execution_time, 0.0