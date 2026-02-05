import os

from google.adk.agents import LlmAgent, SequentialAgent, LoopAgent
from google.adk.models.lite_llm import LiteLlm 
from pydantic import BaseModel, Field

from agents.constants.constants import BGA_COLUMN_NAMES_STATES
from agents.sub_agents.data_search_agent.tools import (
    exit_column_extraction_loop,
    query_bga_database,
    get_sql_query_references_before_model_callback,
)

from ...utils.file_utils import save_file_artifact_after_tool_callback
from ...utils.prompt_utils import get_prompt_yaml

MODEL = LiteLlm(
        model='openai/',
        api_base=os.getenv("ROOT_AGENT_API_BASE"),
        extra_headers={
            "Authorization": os.getenv("PADO_API_KEY")
        },
)


COLUMN_NAME_EXTRACTOR_DESCRIPTION = get_prompt_yaml(
    tag="column_name_extractor_description"
)
COLUMN_NAME_EXTRACTOR_INSTRUCTION = get_prompt_yaml(
    tag="column_name_extractor_instruction"
)
COLUMN_NAME_REVIEWER_DESCRIPTION = get_prompt_yaml(
    tag="column_name_reviewer_description"
)
COLUMN_NAME_REVIEWER_INSTRUCTION = get_prompt_yaml(
    tag="column_name_reviewer_instruction"
)
COLUMN_NAME_STANDARDIZER_DESCRIPTION = get_prompt_yaml(
    tag="column_name_standardizer_description"
)
COLUMN_NAME_STANDARDIZER_INSTRUCTION = get_prompt_yaml(
    tag="column_name_standardizer_instruction"
)
COLUMN_NAME_STANDARD_REVIEWER_DESCRIPTION = get_prompt_yaml(
    tag="column_name_standard_reviewer_description"
)
COLUMN_NAME_STANDARD_REVIEWER_INSTRUCTION = get_prompt_yaml(
    tag="column_name_standard_reviewer_instruction"
)

SQL_GENERATOR_DESCRIPTION = get_prompt_yaml(tag="sql_generator_description")
SQL_GENERATOR_INSTRUCTION = get_prompt_yaml(tag="sql_generator_instruction")
SQL_REVIEWER_DESCRIPTION = get_prompt_yaml(tag="sql_reviewer_description")
SQL_REVIEWER_INSTRUCTION = get_prompt_yaml(tag="sql_reviewer_instruction")

class ExtractedSingleColumnName(BaseModel):
    extracted_column_name: str = Field(
        description="The name of a single column name extracted from user natural language query."
    )

class ExtractedColumnNames(BaseModel):
    items: list[ExtractedSingleColumnName] = Field(
        description="The list of column names extracted from user query."
    )

_column_name_extractor = LlmAgent(
    name="column_name_extractor",
    description=COLUMN_NAME_EXTRACTOR_DESCRIPTION,
    model=MODEL,
    output_key=BGA_COLUMN_NAMES_STATES,
    output_schema=ExtractedColumnNames,
    instruction=COLUMN_NAME_EXTRACTOR_INSTRUCTION,
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)

_column_name_reviewer = LlmAgent(
    name="column_name_reviewer",
    description=COLUMN_NAME_REVIEWER_DESCRIPTION,
    model=MODEL,
    instruction=COLUMN_NAME_REVIEWER_INSTRUCTION,
    tools=[exit_column_extraction_loop]
)

column_name_extraction_loop_agent = LoopAgent(
    name="column_name_extraction_loop",
    sub_agents=[_column_name_extractor, _column_name_reviewer],
    max_iterations=3,
)

_sql_generator = LlmAgent(
    name="sqk_generator",
    description=SQL_GENERATOR_DESCRIPTION,
    model = MODEL,
    instruction=(SQL_GENERATOR_INSTRUCTION),
)

_sql_reviewer = LlmAgent(
    name="sql_reviewer",
    description=SQL_REVIEWER_DESCRIPTION,
    model=MODEL,
    instruction=(SQL_REVIEWER_INSTRUCTION),
    tools=[query_bga_database],
    after_tool_callback=[save_file_artifact_after_tool_callback],
)

sql_generation_loop_agent = LoopAgent(
    name="sql_generation_loop_agent",
    sub_agents=[_sql_generator, _sql_reviewer],
    max_iterations=3,
)

data_search_agent = SequentialAgent(
    name="data_search_agent",
    sub_agents=[
        column_name_extraction_loop_agent,
        sql_generation_loop_agent,
    ],
)
