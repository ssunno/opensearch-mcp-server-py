# Copyright OpenSearch Contributors
# SPDX-License-Identifier: Apache-2.0

import json
import pytest
import sys
from unittest.mock import patch, Mock


class TestTools:
    def setup_method(self):
        """Setup that runs before each test method"""
        # Mock OpenSearch modules
        self.mock_client = Mock()
        sys.modules["opensearch.client"] = Mock(client=self.mock_client)
        sys.modules["opensearch.helper"] = Mock(
            list_indices=Mock(return_value=[]),
            get_index_mapping=Mock(return_value={}),
            search_index=Mock(return_value={}),
            aggregation_search=Mock(return_value={}),
            get_shards=Mock(return_value=[]),
        )

        # Import after mocking
        from tools.tools import (
            ListIndicesArgs,
            GetIndexMappingArgs,
            SearchIndexArgs,
            AggregationArgs,
            GetShardsArgs,
            list_indices_tool,
            get_index_mapping_tool,
            search_index_tool,
            aggregation_tool,
            get_shards_tool,
            TOOL_REGISTRY,
        )

        # Store the imports as instance attributes
        self.ListIndicesArgs = ListIndicesArgs
        self.GetIndexMappingArgs = GetIndexMappingArgs
        self.SearchIndexArgs = SearchIndexArgs
        self.AggregationArgs = AggregationArgs
        self.GetShardsArgs = GetShardsArgs
        self.TOOL_REGISTRY = TOOL_REGISTRY

        # Store the tool functions
        self._list_indices_tool = list_indices_tool
        self._get_index_mapping_tool = get_index_mapping_tool
        self._search_index_tool = search_index_tool
        self._aggregation_tool = aggregation_tool
        self._get_shards_tool = get_shards_tool

        # Setup patches
        self.patcher_list_indices = patch("tools.tools.list_indices")
        self.patcher_get_mapping = patch("tools.tools.get_index_mapping")
        self.patcher_search = patch("tools.tools.search_index")
        self.patcher_aggregation = patch("tools.tools.aggregation_search")
        self.patcher_shards = patch("tools.tools.get_shards")

        # Start patches
        self.mock_list_indices = self.patcher_list_indices.start()
        self.mock_get_mapping = self.patcher_get_mapping.start()
        self.mock_search = self.patcher_search.start()
        self.mock_aggregation = self.patcher_aggregation.start()
        self.mock_shards = self.patcher_shards.start()

        # Test URL
        self.test_url = "https://test-opensearch-domain.com"

    def teardown_method(self):
        """Cleanup after each test method"""
        # Stop all patches
        self.patcher_list_indices.stop()
        self.patcher_get_mapping.stop()
        self.patcher_search.stop()
        self.patcher_aggregation.stop()
        self.patcher_shards.stop()

        # Clean up module mocks
        sys.modules.pop("opensearch.client", None)
        sys.modules.pop("opensearch.helper", None)

    @pytest.mark.asyncio
    async def test_list_indices_tool(self):
        """Test list_indices_tool successful"""
        # Setup
        self.mock_list_indices.return_value = [{"index": "index1"}, {"index": "index2"}]

        # Execute
        result = await self._list_indices_tool(
            self.ListIndicesArgs(opensearch_url=self.test_url)
        )

        # Assert
        assert len(result) == 1
        assert result[0]["type"] == "text"
        assert "index1\nindex2" in result[0]["text"]
        self.mock_list_indices.assert_called_once_with(self.test_url)

    @pytest.mark.asyncio
    async def test_list_indices_tool_error(self):
        """Test list_indices_tool exception handling"""
        # Setup
        self.mock_list_indices.side_effect = Exception("Test error")

        # Execute
        result = await self._list_indices_tool(
            self.ListIndicesArgs(opensearch_url=self.test_url)
        )

        # Assert
        assert len(result) == 1
        assert result[0]["type"] == "text"
        assert "Error listing indices: Test error" in result[0]["text"]
        self.mock_list_indices.assert_called_once_with(self.test_url)

    @pytest.mark.asyncio
    async def test_get_index_mapping_tool(self):
        """Test get_index_mapping_tool successful"""
        # Setup
        mock_mapping = {"mappings": {"properties": {"field1": {"type": "text"}}}}
        self.mock_get_mapping.return_value = mock_mapping

        # Execute
        result = await self._get_index_mapping_tool(
            self.GetIndexMappingArgs(opensearch_url=self.test_url, index="test-index")
        )

        # Assert
        assert len(result) == 1
        assert result[0]["type"] == "text"
        assert "Mapping for test-index" in result[0]["text"]
        assert json.loads(result[0]["text"].split("\n", 1)[1]) == mock_mapping
        self.mock_get_mapping.assert_called_once_with(self.test_url, "test-index")

    @pytest.mark.asyncio
    async def test_get_index_mapping_tool_error(self):
        """Test get_index_mapping_tool exception handling"""
        # Setup
        self.mock_get_mapping.side_effect = Exception("Test error")

        # Execute
        result = await self._get_index_mapping_tool(
            self.GetIndexMappingArgs(opensearch_url=self.test_url, index="test-index")
        )

        # Assert
        assert len(result) == 1
        assert result[0]["type"] == "text"
        assert "Error getting mapping: Test error" in result[0]["text"]
        self.mock_get_mapping.assert_called_once_with(self.test_url, "test-index")

    @pytest.mark.asyncio
    async def test_search_index_tool(self):
        """Test search_index_tool successful"""
        # Setup
        mock_results = {
            "hits": {"total": {"value": 1}, "hits": [{"_source": {"field": "value"}}]}
        }
        self.mock_search.return_value = mock_results

        # Execute
        result = await self._search_index_tool(
            self.SearchIndexArgs(
                opensearch_url=self.test_url,
                index="test-index",
                query={"match_all": {}},
            )
        )

        # Assert
        assert len(result) == 1
        assert result[0]["type"] == "text"
        assert "Search results from test-index" in result[0]["text"]
        assert json.loads(result[0]["text"].split("\n", 1)[1]) == mock_results
        self.mock_search.assert_called_once_with(
            self.test_url, "test-index", {"match_all": {}}
        )

    @pytest.mark.asyncio
    async def test_search_index_tool_error(self):
        """Test search_index_tool exception handling"""
        # Setup
        self.mock_search.side_effect = Exception("Test error")

        # Execute
        result = await self._search_index_tool(
            self.SearchIndexArgs(
                opensearch_url=self.test_url,
                index="test-index",
                query={"match_all": {}},
            )
        )

        # Assert
        assert len(result) == 1
        assert result[0]["type"] == "text"
        assert "Error searching index: Test error" in result[0]["text"]
        self.mock_search.assert_called_once_with(
            self.test_url, "test-index", {"match_all": {}}
        )

    @pytest.mark.asyncio
    async def test_aggregation_tool(self):
        """Test aggregation_tool successful with aggregations in response"""
        # Setup
        mock_aggregation_results = {
            "aggregations": {
                "price_stats": {
                    "count": 1000,
                    "min": 10.0,
                    "max": 1000.0,
                    "avg": 250.5,
                    "sum": 250500.0,
                }
            },
            "hits": {"total": {"value": 1000}},
        }
        self.mock_aggregation.return_value = mock_aggregation_results

        # Execute
        result = await self._aggregation_tool(
            self.AggregationArgs(
                opensearch_url=self.test_url,
                index="test-index",
                query={"aggs": {"price_stats": {"stats": {"field": "price"}}}},
            )
        )

        # Assert
        assert len(result) == 1
        assert result[0]["type"] == "text"
        assert "Aggregation results from test-index" in result[0]["text"]

        # Extract and verify aggregation results
        text_parts = result[0]["text"].split("\n", 1)
        aggregation_data = json.loads(text_parts[1])
        assert aggregation_data == mock_aggregation_results["aggregations"]

        self.mock_aggregation.assert_called_once_with(
            self.test_url,
            "test-index",
            {"aggs": {"price_stats": {"stats": {"field": "price"}}}},
        )

    @pytest.mark.asyncio
    async def test_aggregation_tool_no_aggregations(self):
        """Test aggregation_tool when response has no aggregations field"""
        # Setup
        mock_results = {"hits": {"total": {"value": 0}, "hits": []}}
        self.mock_aggregation.return_value = mock_results

        # Execute
        result = await self._aggregation_tool(
            self.AggregationArgs(
                opensearch_url=self.test_url,
                index="test-index",
                query={"aggs": {"my_agg": {"terms": {"field": "category"}}}},
            )
        )

        # Assert
        assert len(result) == 1
        assert result[0]["type"] == "text"
        assert (
            "No aggregation results found for index 'test-index'" in result[0]["text"]
        )
        assert (
            "Please verify your aggregation query contains valid 'aggs' or 'aggregations' field"
            in result[0]["text"]
        )
        self.mock_aggregation.assert_called_once_with(
            self.test_url,
            "test-index",
            {"aggs": {"my_agg": {"terms": {"field": "category"}}}},
        )

    @pytest.mark.asyncio
    async def test_aggregation_tool_error(self):
        """Test aggregation_tool exception handling"""
        # Setup
        self.mock_aggregation.side_effect = Exception("Test aggregation error")

        # Execute
        result = await self._aggregation_tool(
            self.AggregationArgs(
                opensearch_url=self.test_url,
                index="test-index",
                query={"aggs": {"count_agg": {"value_count": {"field": "id"}}}},
            )
        )

        # Assert
        assert len(result) == 1
        assert result[0]["type"] == "text"
        assert (
            "Error executing aggregation query: Test aggregation error"
            in result[0]["text"]
        )
        self.mock_aggregation.assert_called_once_with(
            self.test_url,
            "test-index",
            {"aggs": {"count_agg": {"value_count": {"field": "id"}}}},
        )

    @pytest.mark.asyncio
    async def test_get_shards_tool(self):
        """Test get_shards_tool successful"""
        # Setup
        mock_shards = [
            {
                "index": "test-index",
                "shard": "0",
                "prirep": "p",
                "state": "STARTED",
                "docs": "1000",
                "store": "1mb",
                "ip": "127.0.0.1",
                "node": "node1",
            }
        ]
        self.mock_shards.return_value = mock_shards

        # Execute
        result = await self._get_shards_tool(
            self.GetShardsArgs(opensearch_url=self.test_url, index="test-index")
        )

        # Assert
        assert len(result) == 1
        assert result[0]["type"] == "text"
        assert (
            "index | shard | prirep | state | docs | store | ip | node"
            in result[0]["text"]
        )
        assert (
            "test-index | 0 | p | STARTED | 1000 | 1mb | 127.0.0.1 | node1"
            in result[0]["text"]
        )
        self.mock_shards.assert_called_once_with(self.test_url, "test-index")

    @pytest.mark.asyncio
    async def test_get_shards_tool_error(self):
        """Test get_shards_tool exception handling"""
        # Setup
        self.mock_shards.side_effect = Exception("Test error")

        # Execute
        result = await self._get_shards_tool(
            self.GetShardsArgs(opensearch_url=self.test_url, index="test-index")
        )

        # Assert
        assert len(result) == 1
        assert result[0]["type"] == "text"
        assert "Error getting shards information: Test error" in result[0]["text"]
        self.mock_shards.assert_called_once_with(self.test_url, "test-index")

    def test_tool_registry(self):
        """Test TOOL_REGISTRY structure"""
        expected_tools = [
            "ListIndexTool",
            "IndexMappingTool",
            "SearchIndexTool",
            "AggregationTool",
            "GetShardsTool",
        ]

        for tool in expected_tools:
            assert tool in self.TOOL_REGISTRY
            assert "description" in self.TOOL_REGISTRY[tool]
            assert "input_schema" in self.TOOL_REGISTRY[tool]
            assert "function" in self.TOOL_REGISTRY[tool]
            assert "args_model" in self.TOOL_REGISTRY[tool]

    def test_input_models(self):
        """Test input models validation"""
        with pytest.raises(ValueError):
            self.GetIndexMappingArgs(
                opensearch_url=self.test_url
            )  # Should fail without index

        with pytest.raises(ValueError):
            self.SearchIndexArgs(
                opensearch_url=self.test_url, index="test"
            )  # Should fail without query

        with pytest.raises(ValueError):
            self.AggregationArgs(
                opensearch_url=self.test_url, index="test"
            )  # Should fail without query

        # Test valid inputs
        assert (
            self.GetIndexMappingArgs(opensearch_url=self.test_url, index="test").index
            == "test"
        )
        assert (
            self.SearchIndexArgs(
                opensearch_url=self.test_url, index="test", query={"match": {}}
            ).index
            == "test"
        )
        assert (
            self.AggregationArgs(
                opensearch_url=self.test_url, index="test", query={"aggs": {}}
            ).index
            == "test"
        )
        assert (
            self.GetShardsArgs(opensearch_url=self.test_url, index="test").index
            == "test"
        )
        assert isinstance(
            self.ListIndicesArgs(opensearch_url=self.test_url), self.ListIndicesArgs
        )
