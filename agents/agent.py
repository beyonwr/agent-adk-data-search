import os

from google.adk.agents import Agent 
from google.adk.models.lite_llm import LiteLlm 
from google.adk.tools.agent_tool import AgentTool 

from .utils.prompt_utils import get_prompt_yaml
# from .utils.file_utils import save_imgfile_artifact_before_agent_callback
# from .utils.file_utils import remove_non_text_part_from_llmrequest_before_model_callback
from .sub_agents import data_search_agent

ROOT_AGENT_PROMPT = get_prompt_yaml(tag="prompt")
GLOBAL_INSTRUCTION = get_prompt_yaml(tag="global_instruction")

root_agent = Agent(
    name = "root_agent",
    model=LiteLlm(
        model=os.getenv("ROOT_AGENT_MODEL", ""),
        api_base=os.getenv("ROOT_AGENT_API_BASE"),
        stream=False,
    ),
    instruction=ROOT_AGENT_PROMPT,

    sub_agents=[data_search_agent],
    # before_agent_callback = save_imgfile_artifact_before_agent_callback,
    # before_model_callback = remove_non_text_part_from_llmrequest_before_model_callback,
    output_key="result",
    global_instruction=GLOBAL_INSTRUCTION,
)


