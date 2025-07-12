import pytest
from semver import Version
from unittest.mock import patch, MagicMock
from tools.utils import is_tool_compatible
from tools.tool_filter import get_tools, process_tool_filter
from tools.tool_params import baseToolArgs
import copy

# A dictionary for mocking TOOL_REGISTRY
MOCK_TOOL_REGISTRY = {
    'ListIndexTool': {
        'description': 'List indices',
        'input_schema': {'type': 'object', 'properties': {'param1': {'type': 'string'}}},
        'function': MagicMock(),
        'args_model': MagicMock(),
        'min_version': '1.0.0',
        'max_version': '3.0.0',
    },
    'SearchIndexTool': {
        'description': 'Search an index',
        'input_schema': {
            'type': 'object',
            'properties': {
                'opensearch_cluster_name': {'type': 'string'},
                'query': {'type': 'object'},
            },
        },
        'function': MagicMock(),
        'args_model': MagicMock(),
        'min_version': '2.0.0',
        'max_version': '3.0.0',
    },
}


class TestIsToolCompatible:
    def test_version_within_range(self):
        tool_info = {'min_version': '1.0.0', 'max_version': '3.0.0'}
        assert is_tool_compatible(Version.parse('2.0.0'), tool_info) is True

    def test_version_below_min(self):
        tool_info = {'min_version': '2.0.0', 'max_version': '3.0.0'}
        assert is_tool_compatible(Version.parse('1.5.0'), tool_info) is False

    def test_version_above_max(self):
        tool_info = {'min_version': '1.0.0', 'max_version': '2.0.0'}
        assert is_tool_compatible(Version.parse('2.1.0'), tool_info) is False

    def test_version_equal_to_min(self):
        tool_info = {'min_version': '1.0.0', 'max_version': '3.0.0'}
        assert is_tool_compatible(Version.parse('1.0.0'), tool_info) is True

    def test_version_equal_to_max(self):
        tool_info = {'min_version': '1.0.0', 'max_version': '3.0.0'}
        assert is_tool_compatible(Version.parse('3.0.0'), tool_info) is True

    def test_version_only_patch_not_provided(self):
        tool_info = {'min_version': '2.5', 'max_version': '3'}
        assert is_tool_compatible(Version.parse('2.5.1'), tool_info) is True
        assert is_tool_compatible(Version.parse('2.15.0'), tool_info) is True
        assert is_tool_compatible(Version.parse('3.0.0'), tool_info) is True

    def test_default_tool_info(self):
        # Should be True for almost any reasonable version
        assert is_tool_compatible(Version.parse('1.2.3')) is True
        assert is_tool_compatible(Version.parse('99.0.0')) is True
        assert is_tool_compatible(Version.parse('0.0.1')) is True

    def test_invalid_version_strings(self):
        # If min_version or max_version is not a valid semver, should raise ValueError
        with pytest.raises(ValueError):
            is_tool_compatible(Version.parse('1.0.0'), {'min_version': 'not_a_version'})
        with pytest.raises(ValueError):
            is_tool_compatible(Version.parse('1.0.0'), {'max_version': 'not_a_version'})


class TestGetTools:
    """Test cases for the get_tools function."""

    @pytest.fixture
    def mock_tool_registry(self):
        """Return a deep copy of the mock tool registry for isolation."""
        return copy.deepcopy(MOCK_TOOL_REGISTRY)

    @pytest.fixture
    def mock_patches(self):
        """Set up common patches for get_tools tests."""
        with patch('tools.tool_filter.get_opensearch_version') as mock_get_version, patch(
            'tools.tool_filter.is_tool_compatible'
        ) as mock_is_compatible:
            yield mock_get_version, mock_is_compatible

    def test_get_tools_multi_mode_returns_all_tools(self, mock_tool_registry):
        """Test that multi mode returns all tools with base fields intact."""
        result = get_tools(mock_tool_registry, mode='multi')
        assert result == mock_tool_registry
        assert 'param1' in result['ListIndexTool']['input_schema']['properties']
        assert (
            'opensearch_cluster_name'
            in result['SearchIndexTool']['input_schema']['properties']
        )

    def test_get_tools_single_mode_filters_and_removes_base_fields(
        self, mock_tool_registry, mock_patches
    ):
        """Test that single mode filters by version AND removes base fields."""
        mock_get_version, mock_is_compatible = mock_patches

        # Setup mocks
        mock_get_version.return_value = Version.parse('2.5.0')

        # Mock compatibility: only ListIndexTool should be compatible
        mock_is_compatible.side_effect = (
            lambda version, tool_info: tool_info['min_version'] == '1.0.0'
        )

        # Call get_tools in single mode
        result = get_tools(mock_tool_registry, mode='single')

        # Assertions
        assert 'ListIndexTool' in result
        assert 'SearchIndexTool' not in result
        assert 'param1' in result['ListIndexTool']['input_schema']['properties']
        assert (
            'opensearch_cluster_name'
            not in result['ListIndexTool']['input_schema']['properties']
        )

    @patch.dict('os.environ', {'AWS_OPENSEARCH_SERVERLESS': 'true'})
    def test_get_tools_single_mode_serverless_skips_version_check(
        self, mock_tool_registry, mock_patches
    ):
        """Test that serverless mode skips version compatibility checks."""
        mock_get_version, mock_is_compatible = mock_patches

        # Setup mocks
        mock_get_version.return_value = Version.parse('1.0.0')

        # Call get_tools in single mode with serverless environment
        result = get_tools(mock_tool_registry, mode='single')

        # is_tool_compatible should not be called
        mock_is_compatible.assert_not_called()

        # Both tools should be returned
        assert 'ListIndexTool' in result
        assert 'SearchIndexTool' in result

    def test_get_tools_single_mode_handles_missing_properties(self, mock_patches):
        """Test that single mode handles schemas without properties field."""
        mock_get_version, mock_is_compatible = mock_patches

        # Create tool with missing properties
        tool_without_properties = {
            'ListIndexTool': {
                'description': 'List indices',
                'input_schema': {'type': 'object', 'title': 'ListIndexArgs'},
                'function': MagicMock(),
                'args_model': MagicMock(),
                'min_version': '1.0.0',
                'max_version': '3.0.0',
            }
        }
        mock_get_version.return_value = Version.parse('2.5.0')
        mock_is_compatible.return_value = True

        # Call get_tools in single mode - should not raise error
        result = get_tools(tool_without_properties, mode='single')
        assert 'ListIndexTool' in result
        assert 'properties' not in result['ListIndexTool']['input_schema']

    def test_get_tools_default_mode_is_single(self, mock_tool_registry, mock_patches):
        """Test that get_tools defaults to single mode."""
        mock_get_version, mock_is_compatible = mock_patches

        mock_get_version.return_value = Version.parse('2.5.0')
        mock_is_compatible.return_value = True

        # Call get_tools without specifying mode
        result = get_tools(mock_tool_registry)
        assert 'opensearch_cluster_name' not in result['SearchIndexTool']['input_schema']['properties']

    def test_get_tools_logs_version_info(self, mock_tool_registry, mock_patches, caplog):
        """Test that get_tools logs version information in single mode."""
        mock_get_version, mock_is_compatible = mock_patches
        mock_get_version.return_value = Version.parse('2.5.0')
        mock_is_compatible.return_value = True

        # Call get_tools in single mode with logging capture
        with caplog.at_level('INFO'):
            get_tools(mock_tool_registry, mode='single')
            assert 'Connected OpenSearch version: 2.5.0' in caplog.text


class TestProcessToolFilter:
    """Test cases for the process_tool_filter function."""

    def setup_method(self):
        """Set up a fresh copy of the tool registry for each test."""
        self.tool_registry = {
            'ListIndexTool': {'http_methods': 'GET'},
            'SearchIndexTool': {'http_methods': 'GET, POST'},
            'MsearchTool': {'http_methods': 'GET, POST'},
            'ExplainTool': {'http_methods': 'GET, POST'},
            'ClusterHealthTool': {'http_methods': 'GET'},
            'IndicesCreateTool': {'http_methods': 'PUT'},
            'IndicesStatsTool': {'http_methods': 'GET'},
        }
        self.category_to_tools = {
            'critical': ['SearchIndexTool', 'ExplainTool'],
            'admin': ['ClusterHealthTool', 'IndicesStatsTool'],
        }

    def test_process_tool_filter_config(self, caplog):
        """Test processing tool filter from a YAML config file."""
        import logging

        caplog.set_level(logging.INFO)

        process_tool_filter(
            tool_registry=self.tool_registry,
            filter_path='tests/tools/test_config.yml',
            tool_categories=self.category_to_tools,
        )

        # Check the results
        assert 'ClusterHealthTool' in self.tool_registry
        assert 'ListIndexTool' in self.tool_registry
        assert 'MsearchTool' not in self.tool_registry
        # These tools are in the 'critical' category which is disabled in test_config.yml
        assert 'SearchIndexTool' not in self.tool_registry
        assert 'ExplainTool' not in self.tool_registry
        # This tool is in the 'admin' category which is not disabled
        assert 'IndicesStatsTool' in self.tool_registry

    def test_process_tool_filter_env(self, caplog):
        """Test processing tool filter from environment variables."""
        import logging

        caplog.set_level(logging.INFO)

        # Call the function with environment variables
        process_tool_filter(
            tool_registry=self.tool_registry,
            disabled_tools='ExplainTool',
            disabled_tools_regex='search.*',
            allow_write=True,
        )

        # Check the results
        assert 'ListIndexTool' in self.tool_registry
        assert 'ClusterHealthTool' in self.tool_registry
        assert 'IndicesCreateTool' in self.tool_registry
        assert 'MsearchTool' in self.tool_registry
        assert 'SearchIndexTool' not in self.tool_registry  # In disabled_tools_regex
        assert 'ExplainTool' not in self.tool_registry  # In disabled_tools
