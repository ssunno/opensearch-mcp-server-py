# Copyright OpenSearch Contributors
# SPDX-License-Identifier: Apache-2.0

from pydantic import BaseModel, Field
from typing import Any


class baseToolArgs(BaseModel):
    """Base class for all tool arguments that contains common OpenSearch connection parameters."""

    opensearch_cluster_name: str = Field(
        default='', description='The name of the OpenSearch cluster'
    )


class ListIndicesArgs(baseToolArgs):
    pass


class GetIndexMappingArgs(baseToolArgs):
    index: str = Field(description='The name of the index to get mapping information for')


class SearchIndexArgs(baseToolArgs):
    index: str = Field(description='The name of the index to search in')
    query: Any = Field(description='The search query in OpenSearch query DSL format')


class GetShardsArgs(baseToolArgs):
    index: str = Field(description='The name of the index to get shard information for')


class AggregationArgs(baseToolArgs):
    """
    Arguments for executing aggregation queries on an OpenSearch index.
    """

    index: str = Field(
        ..., description='Name of the OpenSearch index to run the aggregation query on.'
    )
    aggs: dict[str, Any] = Field(
        ...,
        description=(
            'Aggregations to compute, keyed by name. Common types: avg, sum, min, max, terms, histogram. '
            'You can nest aggregations. Example: {"avg_price": {"avg": {"field": "price"}}}'
            'This field is required.'
        ),
    )
    query: dict[str, Any] = Field(
        default_factory=lambda: {'match_all': {}},
        description=(
            'Query DSL to filter documents before aggregation. Defaults to match all documents. '
            'Example: {"range": {"price": {"gte": 100}}}'
        ),
    )
