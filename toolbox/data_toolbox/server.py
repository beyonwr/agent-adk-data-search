from fastmcp import FastMCP
from .query_data import query_data
from .search_similar_columns import search_similar_columns

data_toolbox = FastMCP(name="data_toolbox")

data_toolbox.tool(query_data)
data_toolbox.tool(search_similar_columns)
