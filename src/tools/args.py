"""Argument models for tools."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Any
import os


class ListIndicesArgs(BaseModel):
    """Arguments for listing all indices."""

    opensearch_url: str = Field(
        default=os.getenv("OPENSEARCH_URL", ""),
        description="OpenSearch cluster URL",
    )


class GetIndexMappingArgs(BaseModel):
    """Arguments for retrieving index mappings."""

    index: str = Field(..., description="Name of the index")
    opensearch_url: str = Field(
        default=os.getenv("OPENSEARCH_URL", ""),
        description="OpenSearch cluster URL",
    )


class SearchIndexArgs(BaseModel):
    """Arguments for the SearchIndexTool."""

    index: str = Field(..., description="Name of the index to search")
    query: dict[str, Any] = Field(
        ...,
        description=(
            "Query DSL describing which documents to match. Placed in the "
            "`query` section of the search request body."
        ),
    )
    size: int | None = Field(
        default=None,
        description=(
            "Maximum number of search hits to return. Defaults to 10 when"
            " omitted."
        ),
    )
    from_: int | None = Field(
        default=None,
        alias="from",
        description=(
            "How many search hits to skip before returning results. Useful "
            "for pagination."
        ),
    )
    sort: list[Any] | None = Field(
        default=None,
        description="List of sort directives for ordering search results",
    )
    aggs: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Aggregations to compute over the matched documents, keyed by "
            "aggregation name."
        ),
    )
    opensearch_url: str = Field(
        default=os.getenv("OPENSEARCH_URL", ""),
        description="OpenSearch cluster URL",
    )

    model_config = ConfigDict(populate_by_name=True)


class GetShardsArgs(BaseModel):
    """Arguments for retrieving shard information."""

    index: str = Field(..., description="Name of the index")
    opensearch_url: str = Field(
        default=os.getenv("OPENSEARCH_URL", ""),
        description="OpenSearch cluster URL",
    )
