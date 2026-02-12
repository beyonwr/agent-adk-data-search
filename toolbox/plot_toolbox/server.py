from fastmcp import FastMCP 
from .bar_chart import bar_chart

plot_toolbox = FastMCP(name="plot_toolbox")

plot_toolbox.tool(bar_chart)