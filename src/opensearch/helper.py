# Copyright OpenSearch Contributors
# SPDX-License-Identifier: Apache-2.0

import json
from semver import Version
from tools.tool_params import *
from typing import Any


# List all the helper functions, these functions perform a single rest call to opensearch
# these functions will be used in tools folder to eventually write more complex tools
def list_indices(args: ListIndicesArgs) -> json:
    from .client import initialize_client

    client = initialize_client(args)
    response = client.cat.indices(format='json')
    return response


def get_index_mapping(args: GetIndexMappingArgs) -> json:
    from .client import initialize_client

    client = initialize_client(args)
    response = client.indices.get_mapping(index=args.index)
    return response


def search_index(args: SearchIndexArgs) -> json:
    from .client import initialize_client

    client = initialize_client(args)
    response = client.search(index=args.index, body=args.query)
    return response


def aggregation_search(args: AggregationArgs) -> json:
    """
    Execute optimized aggregation queries on OpenSearch index.
    This function is specifically designed for high-performance aggregation queries.

    Args:
        args (AggregationArgs): The aggregation arguments containing cluster, index, and query info

    Returns:
        json: The optimized aggregation results from OpenSearch
    """
    from .client import initialize_client

    client = initialize_client(args)

    # Build the OpenSearch aggregation query body
    body = {'aggs': args.aggs}
    if args.query:
        body['query'] = args.query

    # Apply essential aggregation optimizations
    body['size'] = 0  # No document results needed
    body['_source'] = False  # Reduce memory usage
    body['track_total_hits'] = False
    body['timeout'] = '30s'  # Prevent long-running queries

    # Execute with performance optimizations
    search_params = {
        'index': args.index,
        'body': body,
        'request_cache': True,
        'allow_partial_search_results': False,
    }

    response = client.search(**search_params)
    return response


def get_shards(args: GetShardsArgs) -> json:
    from .client import initialize_client

    client = initialize_client(args)
    response = client.cat.shards(index=args.index, format='json')
    return response


def get_opensearch_version(args: baseToolArgs) -> Version:
    """Get the version of OpenSearch cluster.

    Returns:
        Version: The version of OpenSearch cluster (SemVer style)
    """
    from .client import initialize_client

    client = initialize_client(args)
    response = client.info()
    return Version.parse(response['version']['number'])
