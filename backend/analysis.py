def build_adjacency(rows):
    graph = {}

    for row in rows:
        source_id = row[0]
        target_id = row[1]

        if source_id not in graph:
            graph[source_id] = []

        graph[source_id].append(target_id)

    return graph

def collect_affected_ids(root_id, graph):
    queue = []
    visited = set()
    result = []

    if root_id in graph:
        for item in graph[root_id]:
            queue.append(item)

    while queue:
        current_id = queue.pop(0)

        if current_id in visited:
            continue

        visited.add(current_id)
        result.append(current_id)

        if current_id in graph:
            for next_id in graph[current_id]:
                if next_id not in visited:
                    queue.append(next_id)

    return result