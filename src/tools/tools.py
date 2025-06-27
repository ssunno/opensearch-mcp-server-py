# Copyright OpenSearch Contributors
# SPDX-License-Identifier: Apache-2.0

import json
from .tool_params import (
    GetIndexMappingArgs,
    GetShardsArgs,
    ListIndicesArgs,
    SearchIndexArgs,
    AggregationArgs,
    baseToolArgs,
)
from .utils import is_tool_compatible
from opensearch.helper import (
    get_index_mapping,
    get_opensearch_version,
    get_shards,
    list_indices,
    search_index,
    aggregation_search,
)


def check_tool_compatibility(tool_name: str, args: baseToolArgs = None):
    opensearch_version = get_opensearch_version(args)
    if not is_tool_compatible(opensearch_version, TOOL_REGISTRY[tool_name]):
        raise Exception(
            f'Tool {tool_name} is not supported for OpenSearch versions less than {TOOL_REGISTRY[tool_name]["min_version"]} and greater than {TOOL_REGISTRY[tool_name]["max_version"]}'
        )


async def list_indices_tool(args: ListIndicesArgs) -> list[dict]:
    try:
        check_tool_compatibility('ListIndexTool', args)
        indices = list_indices(args)
        indices_text = '\n'.join(index['index'] for index in indices)

        # Return in MCP expected format
        return [{'type': 'text', 'text': indices_text}]
    except Exception as e:
        return [{'type': 'text', 'text': f'Error listing indices: {str(e)}'}]


async def get_index_mapping_tool(args: GetIndexMappingArgs) -> list[dict]:
    try:
        check_tool_compatibility('IndexMappingTool', args)
        mapping = get_index_mapping(args)
        formatted_mapping = json.dumps(mapping, indent=2)

        return [{'type': 'text', 'text': f'Mapping for {args.index}:\n{formatted_mapping}'}]
    except Exception as e:
        return [{'type': 'text', 'text': f'Error getting mapping: {str(e)}'}]


async def search_index_tool(args: SearchIndexArgs) -> list[dict]:
    try:
        check_tool_compatibility('SearchIndexTool', args)
        result = search_index(args)
        formatted_result = json.dumps(result, indent=2)

        return [
            {
                'type': 'text',
                'text': f'Search results from {args.index}:\n{formatted_result}',
            }
        ]
    except Exception as e:
        return [{'type': 'text', 'text': f'Error searching index: {str(e)}'}]


async def aggregation_tool(args: AggregationArgs) -> list[dict]:
    try:
        result = aggregation_search(args)

        # Extract aggregation results from response
        aggregations = result.get('aggregations')
        return_msg = (
            f'Aggregation results from {args.index}:\n{json.dumps(aggregations, indent=2)}'
        )
        if not aggregations:
            return_msg = (
                f"No aggregation results found for index '{args.index}'. "
                "Please verify your aggregation query contains valid 'aggs' or 'aggregations' field."
            )
    except Exception as e:
        return_msg = f'Error executing aggregation query: {str(e)}'
    return [{'type': 'text', 'text': return_msg}]


async def get_shards_tool(args: GetShardsArgs) -> list[dict]:
    try:
        check_tool_compatibility('GetShardsTool', args)
        result = get_shards(args)

        if isinstance(result, dict) and 'error' in result:
            return [{'type': 'text', 'text': f'Error getting shards: {result["error"]}'}]
        formatted_text = 'index | shard | prirep | state | docs | store | ip | node\n'

        # Format each shard row
        for shard in result:
            formatted_text += f'{shard["index"]} | '
            formatted_text += f'{shard["shard"]} | '
            formatted_text += f'{shard["prirep"]} | '
            formatted_text += f'{shard["state"]} | '
            formatted_text += f'{shard["docs"]} | '
            formatted_text += f'{shard["store"]} | '
            formatted_text += f'{shard["ip"]} | '
            formatted_text += f'{shard["node"]}\n'

        return [{'type': 'text', 'text': formatted_text}]
    except Exception as e:
        return [{'type': 'text', 'text': f'Error getting shards information: {str(e)}'}]


# Registry of available OpenSearch tools with their metadata
TOOL_REGISTRY = {
    'ListIndexTool': {
        'description': 'Lists all indices in the OpenSearch cluster',
        'input_schema': ListIndicesArgs.model_json_schema(),
        'function': list_indices_tool,
        'args_model': ListIndicesArgs,
        'min_version': '1.0.0',
        'http_methods': 'GET',
    },
    'IndexMappingTool': {
        'description': 'Retrieves index mapping and setting information for an index in OpenSearch',
        'input_schema': GetIndexMappingArgs.model_json_schema(),
        'function': get_index_mapping_tool,
        'args_model': GetIndexMappingArgs,
        'http_methods': 'GET',
    },
    'SearchIndexTool': {
        'description': 'Searches an index using a query written in query domain-specific language (DSL) in OpenSearch',
        'input_schema': SearchIndexArgs.model_json_schema(),
        'function': search_index_tool,
        'args_model': SearchIndexArgs,
        'http_methods': 'GET, POST',
    },
    'AggregationTool': {
        'description': (
            'Executes aggregation queries (such as count, sum, avg, min, max, histogram) on an OpenSearch index. '
            'This tool returns only the aggregation results, not the matching documents. '
            'Ideal for questions that require aggregate insights rather than document details. '
        ),
        'input_schema': AggregationArgs.model_json_schema(),
        'function': aggregation_tool,
        'args_model': AggregationArgs,
        'http_methods': 'GET, POST',
    },
    'GetShardsTool': {
        'description': 'Gets information about shards in OpenSearch',
        'input_schema': GetShardsArgs.model_json_schema(),
        'function': get_shards_tool,
        'args_model': GetShardsArgs,
        'http_methods': 'GET',
    },
}
