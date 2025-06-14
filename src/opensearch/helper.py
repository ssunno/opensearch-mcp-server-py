# Copyright OpenSearch Contributors
# SPDX-License-Identifier: Apache-2.0

from .client import initialize_client
import json
from typing import Any
from semver import Version


# List all the helper functions, these functions perform a single rest call to opensearch
# these functions will be used in tools folder to eventually write more complex tools
def list_indices(opensearch_url: str) -> json:
    client = initialize_client(opensearch_url)
    response = client.cat.indices(format="json")
    return response


def get_index_mapping(opensearch_url: str, index: str) -> json:
    client = initialize_client(opensearch_url)
    response = client.indices.get_mapping(index=index)
    return response


def search_index(opensearch_url: str, index: str, query: Any) -> json:
    client = initialize_client(opensearch_url)
    response = client.search(index=index, body=query)
    return response


def aggregation_search(opensearch_url: str, index: str, query: Any) -> json:
    """
    Execute aggregation queries on OpenSearch index.

    This function is specifically designed for aggregation queries.
    It automatically sets size=0 to return only aggregation results without documents.

    Args:
        opensearch_url (str): The URL of the OpenSearch cluster
        index (str): The index name to search
        query (Any): The aggregation query (should contain 'aggs' field)

    Returns:
        json: The aggregation results from OpenSearch
    """
    client = initialize_client(opensearch_url)

    # Ensure size is 0 for aggregation-only queries
    if isinstance(query, dict):
        query = query.copy()
        query["size"] = 0

    response = client.search(index=index, body=query)
    return response


def get_shards(opensearch_url: str, index: str) -> json:
    client = initialize_client(opensearch_url)
    response = client.cat.shards(index=index, format="json")
    return response


def get_opensearch_version(opensearch_url: str) -> Version:
    """
    Get the version of OpenSearch cluster.

    Args:
        opensearch_url (str): The URL of the OpenSearch cluster

    Returns:
        Version: The version of OpenSearch cluster (SemVer style)
    """
    client = initialize_client(opensearch_url)
    response = client.info()
    return Version.parse(response["version"]["number"])
