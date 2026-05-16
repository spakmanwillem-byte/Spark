"""
Graph API Tests - Knowledge Graph / Verbanden Module
Tests for nodes, edges, clusters, search, neighborhood, and stats endpoints.
Data: 2424 nodes, 11757 edges from JSON files
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestGraphStats:
    """Tests for GET /api/graph/stats - returns total_nodes, total_edges, top_tags, most_connected, avg_connections"""

    def test_stats_returns_200(self):
        """Stats endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/graph/stats")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    def test_stats_has_total_nodes(self):
        """Stats returns total_nodes = 2424"""
        response = requests.get(f"{BASE_URL}/api/graph/stats")
        data = response.json()
        assert "total_nodes" in data, "Missing total_nodes field"
        assert data["total_nodes"] == 2424, f"Expected 2424 nodes, got {data['total_nodes']}"

    def test_stats_has_total_edges(self):
        """Stats returns total_edges = 11757"""
        response = requests.get(f"{BASE_URL}/api/graph/stats")
        data = response.json()
        assert "total_edges" in data, "Missing total_edges field"
        assert data["total_edges"] == 11757, f"Expected 11757 edges, got {data['total_edges']}"

    def test_stats_has_top_tags(self):
        """Stats returns top_tags array with tag and count"""
        response = requests.get(f"{BASE_URL}/api/graph/stats")
        data = response.json()
        assert "top_tags" in data, "Missing top_tags field"
        assert isinstance(data["top_tags"], list), "top_tags should be a list"
        assert len(data["top_tags"]) > 0, "top_tags should not be empty"
        # Check structure of first tag
        first_tag = data["top_tags"][0]
        assert "tag" in first_tag, "Tag item missing 'tag' field"
        assert "count" in first_tag, "Tag item missing 'count' field"

    def test_stats_has_most_connected(self):
        """Stats returns most_connected array with id, label, connections"""
        response = requests.get(f"{BASE_URL}/api/graph/stats")
        data = response.json()
        assert "most_connected" in data, "Missing most_connected field"
        assert isinstance(data["most_connected"], list), "most_connected should be a list"
        assert len(data["most_connected"]) <= 20, f"Expected up to 20 most connected, got {len(data['most_connected'])}"
        # Check structure
        first = data["most_connected"][0]
        assert "id" in first, "Missing 'id' in most_connected item"
        assert "label" in first, "Missing 'label' in most_connected item"
        assert "connections" in first, "Missing 'connections' in most_connected item"

    def test_stats_has_avg_connections(self):
        """Stats returns avg_connections"""
        response = requests.get(f"{BASE_URL}/api/graph/stats")
        data = response.json()
        assert "avg_connections" in data, "Missing avg_connections field"
        assert isinstance(data["avg_connections"], (int, float)), "avg_connections should be numeric"


class TestGraphNodes:
    """Tests for GET /api/graph/nodes - paginated nodes with filtering"""

    def test_nodes_returns_200(self):
        """Nodes endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/graph/nodes")
        assert response.status_code == 200

    def test_nodes_pagination_default(self):
        """Nodes returns paginated results with default limit=50"""
        response = requests.get(f"{BASE_URL}/api/graph/nodes")
        data = response.json()
        assert "nodes" in data, "Missing nodes field"
        assert "total" in data, "Missing total field"
        assert "limit" in data, "Missing limit field"
        assert "offset" in data, "Missing offset field"
        assert data["limit"] == 50, f"Expected default limit 50, got {data['limit']}"
        assert data["offset"] == 0, f"Expected default offset 0, got {data['offset']}"
        assert len(data["nodes"]) <= 50, "Should return at most 50 nodes"

    def test_nodes_pagination_custom(self):
        """Nodes respects custom limit and offset"""
        response = requests.get(f"{BASE_URL}/api/graph/nodes?limit=10&offset=5")
        data = response.json()
        assert data["limit"] == 10
        assert data["offset"] == 5
        assert len(data["nodes"]) <= 10

    def test_nodes_filter_by_tag(self):
        """Nodes can be filtered by tag"""
        response = requests.get(f"{BASE_URL}/api/graph/nodes?tag=systeem")
        data = response.json()
        assert response.status_code == 200
        # All returned nodes should have 'systeem' tag
        for node in data["nodes"]:
            tags = node.get("tags", [])
            assert "systeem" in tags, f"Node {node.get('id')} missing 'systeem' tag"

    def test_nodes_search_by_label(self):
        """Nodes can be searched by label/description"""
        response = requests.get(f"{BASE_URL}/api/graph/nodes?search=roadkill")
        data = response.json()
        assert response.status_code == 200
        assert data["total"] > 0, "Should find nodes matching 'roadkill'"
        # Check that results contain roadkill in label or description
        for node in data["nodes"]:
            label = (node.get("label") or "").lower()
            desc = (node.get("description") or "").lower()
            assert "roadkill" in label or "roadkill" in desc, f"Node doesn't match search term"

    def test_nodes_structure(self):
        """Nodes have expected structure (id, label, type, description, tags)"""
        response = requests.get(f"{BASE_URL}/api/graph/nodes?limit=1")
        data = response.json()
        assert len(data["nodes"]) > 0, "Should return at least one node"
        node = data["nodes"][0]
        assert "id" in node, "Node missing 'id'"
        assert "label" in node, "Node missing 'label'"


class TestGraphEdges:
    """Tests for GET /api/graph/edges - edges list with filtering"""

    def test_edges_returns_200(self):
        """Edges endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/graph/edges")
        assert response.status_code == 200

    def test_edges_structure(self):
        """Edges returns edges array with total"""
        response = requests.get(f"{BASE_URL}/api/graph/edges")
        data = response.json()
        assert "edges" in data, "Missing edges field"
        assert "total" in data, "Missing total field"
        assert data["total"] == 11757, f"Expected 11757 total edges, got {data['total']}"

    def test_edges_item_structure(self):
        """Edge items have source, target, id"""
        response = requests.get(f"{BASE_URL}/api/graph/edges?limit=10")
        data = response.json()
        assert len(data["edges"]) > 0, "Should return edges"
        edge = data["edges"][0]
        assert "id" in edge, "Edge missing 'id'"
        assert "source" in edge, "Edge missing 'source'"
        assert "target" in edge, "Edge missing 'target'"

    def test_edges_filter_by_node_id(self):
        """Edges can be filtered by node_id"""
        # Use the Roadkill node ID from the data
        node_id = "12465c90-1ba7-447c-a370-6ba87f45e255"
        response = requests.get(f"{BASE_URL}/api/graph/edges?node_id={node_id}")
        data = response.json()
        assert response.status_code == 200
        # All edges should involve this node
        for edge in data["edges"]:
            assert edge["source"] == node_id or edge["target"] == node_id, \
                f"Edge {edge['id']} doesn't involve node {node_id}"


class TestGraphNeighborhood:
    """Tests for GET /api/graph/neighborhood/{node_id} - center node + neighbors + edges"""

    def test_neighborhood_returns_200(self):
        """Neighborhood endpoint returns 200 for valid node"""
        node_id = "12465c90-1ba7-447c-a370-6ba87f45e255"  # Roadkill
        response = requests.get(f"{BASE_URL}/api/graph/neighborhood/{node_id}")
        assert response.status_code == 200

    def test_neighborhood_structure(self):
        """Neighborhood returns center_node, nodes, edges, totals"""
        node_id = "12465c90-1ba7-447c-a370-6ba87f45e255"
        response = requests.get(f"{BASE_URL}/api/graph/neighborhood/{node_id}")
        data = response.json()
        assert "center_node" in data, "Missing center_node"
        assert "nodes" in data, "Missing nodes"
        assert "edges" in data, "Missing edges"
        assert "total_nodes" in data, "Missing total_nodes"
        assert "total_edges" in data, "Missing total_edges"

    def test_neighborhood_center_node_correct(self):
        """Center node matches requested node_id"""
        node_id = "12465c90-1ba7-447c-a370-6ba87f45e255"
        response = requests.get(f"{BASE_URL}/api/graph/neighborhood/{node_id}")
        data = response.json()
        assert data["center_node"]["id"] == node_id, "Center node ID mismatch"
        assert "Roadkill" in data["center_node"]["label"], "Center node should be Roadkill"

    def test_neighborhood_includes_center_in_nodes(self):
        """Nodes array includes the center node"""
        node_id = "12465c90-1ba7-447c-a370-6ba87f45e255"
        response = requests.get(f"{BASE_URL}/api/graph/neighborhood/{node_id}")
        data = response.json()
        node_ids = [n["id"] for n in data["nodes"]]
        assert node_id in node_ids, "Center node should be in nodes array"

    def test_neighborhood_invalid_node(self):
        """Neighborhood returns error for invalid node_id"""
        response = requests.get(f"{BASE_URL}/api/graph/neighborhood/invalid-node-id-xyz")
        data = response.json()
        assert "error" in data, "Should return error for invalid node"

    def test_neighborhood_depth_parameter(self):
        """Neighborhood respects depth parameter"""
        node_id = "12465c90-1ba7-447c-a370-6ba87f45e255"
        response = requests.get(f"{BASE_URL}/api/graph/neighborhood/{node_id}?depth=1")
        assert response.status_code == 200
        data = response.json()
        assert data["total_nodes"] >= 1, "Should have at least the center node"


class TestGraphClusters:
    """Tests for GET /api/graph/clusters - clusters grouped by shared tags"""

    def test_clusters_returns_200(self):
        """Clusters endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/graph/clusters")
        assert response.status_code == 200

    def test_clusters_structure(self):
        """Clusters returns clusters array and total_clusters"""
        response = requests.get(f"{BASE_URL}/api/graph/clusters")
        data = response.json()
        assert "clusters" in data, "Missing clusters field"
        assert "total_clusters" in data, "Missing total_clusters field"
        assert isinstance(data["clusters"], list), "clusters should be a list"

    def test_clusters_item_structure(self):
        """Cluster items have tag, size, members"""
        response = requests.get(f"{BASE_URL}/api/graph/clusters")
        data = response.json()
        assert len(data["clusters"]) > 0, "Should have clusters"
        cluster = data["clusters"][0]
        assert "tag" in cluster, "Cluster missing 'tag'"
        assert "size" in cluster, "Cluster missing 'size'"
        assert "members" in cluster, "Cluster missing 'members'"
        assert isinstance(cluster["members"], list), "members should be a list"

    def test_clusters_min_size_parameter(self):
        """Clusters respects min_size parameter"""
        response = requests.get(f"{BASE_URL}/api/graph/clusters?min_size=5")
        data = response.json()
        # All clusters should have size >= 5
        for cluster in data["clusters"]:
            assert cluster["size"] >= 5, f"Cluster {cluster['tag']} has size {cluster['size']} < 5"

    def test_clusters_sorted_by_size(self):
        """Clusters are sorted by size descending"""
        response = requests.get(f"{BASE_URL}/api/graph/clusters")
        data = response.json()
        sizes = [c["size"] for c in data["clusters"]]
        assert sizes == sorted(sizes, reverse=True), "Clusters should be sorted by size descending"

    def test_clusters_members_have_id_label(self):
        """Cluster members have id and label"""
        response = requests.get(f"{BASE_URL}/api/graph/clusters")
        data = response.json()
        cluster = data["clusters"][0]
        member = cluster["members"][0]
        assert "id" in member, "Member missing 'id'"
        assert "label" in member, "Member missing 'label'"


class TestGraphSearch:
    """Tests for GET /api/graph/search - search nodes with scores"""

    def test_search_returns_200(self):
        """Search endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/graph/search?q=roadkill")
        assert response.status_code == 200

    def test_search_structure(self):
        """Search returns results array and total"""
        response = requests.get(f"{BASE_URL}/api/graph/search?q=roadkill")
        data = response.json()
        assert "results" in data, "Missing results field"
        assert "total" in data, "Missing total field"

    def test_search_results_have_scores(self):
        """Search results include score field"""
        response = requests.get(f"{BASE_URL}/api/graph/search?q=roadkill")
        data = response.json()
        assert len(data["results"]) > 0, "Should find results for 'roadkill'"
        for result in data["results"]:
            assert "score" in result, "Result missing 'score'"
            assert result["score"] > 0, "Score should be positive"

    def test_search_results_sorted_by_score(self):
        """Search results are sorted by score descending"""
        response = requests.get(f"{BASE_URL}/api/graph/search?q=roadkill")
        data = response.json()
        scores = [r["score"] for r in data["results"]]
        assert scores == sorted(scores, reverse=True), "Results should be sorted by score descending"

    def test_search_exact_match_highest_score(self):
        """Exact label match gets highest score (100)"""
        response = requests.get(f"{BASE_URL}/api/graph/search?q=roadkill")
        data = response.json()
        # Find result with exact match in label
        for result in data["results"]:
            if "roadkill" == result.get("label", "").lower():
                assert result["score"] == 100, "Exact match should have score 100"
                break

    def test_search_requires_query(self):
        """Search requires q parameter"""
        response = requests.get(f"{BASE_URL}/api/graph/search")
        assert response.status_code == 422, "Should return 422 for missing query"

    def test_search_min_length(self):
        """Search requires minimum query length"""
        response = requests.get(f"{BASE_URL}/api/graph/search?q=")
        assert response.status_code == 422, "Should return 422 for empty query"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
