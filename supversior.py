from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from langgraph_supervisor import create_supervisor
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_handoff_tool
from config.model_config import get_model_config
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from tools.file_search import query_to_file
from tools.rag_context import query_context
from tools.code_runner import code_generate
from tools.debug_care import debug_care
from tools.eval_doctor import eval_doctor
from prompts.agent_prompt_templates import FILE_AGENT_PROMPT, RAG_AGENT_PROMPT, CODE_AGENT_PROMPT, DEBUG_AGENT_PROMPT, EVAL_AGENT_TEMPLATE, SUPERVISOR_PROMPT


checkpointer = InMemorySaver()
store = InMemoryStore()

model = ChatOpenAI(
    base_url="<openai-base-url>",
    api_key="<openai-api-key>",
    model_name="gpt-4o-mini"
    )

file_agent = create_react_agent(
    model=model,
    tools=[query_to_file],
    name="file_search_expert",
    prompt=FILE_AGENT_PROMPT
)

rag_agent = create_react_agent(
    model=model,
    tools=[query_context],
    name="rag_expert",
    prompt=RAG_AGENT_PROMPT
)

code_agent = create_react_agent(
    model=model,
    tools=[code_generate],
    name="code_generation_expert",
    prompt=CODE_AGENT_PROMPT
)

debug_agent = create_react_agent(
    model=model,
    tools=[debug_care],
    name="debug_expert",
    prompt=DEBUG_AGENT_PROMPT
)

eval_agent = create_react_agent(
    model=model,
    tools=[eval_doctor],
    name="evaluation_expert",
    prompt=EVAL_AGENT_TEMPLATE
)


# Create supervisor workflow
workflow = create_supervisor(
    agents=[file_agent, rag_agent, code_agent, debug_agent, eval_agent],
    tools=[
        create_handoff_tool(agent_name="file_search_expert", name="assign_to_file_search_expert", description=""),
        create_handoff_tool(agent_name="rag_expert", name="assign_to_rag_expert", description=""),
        create_handoff_tool(agent_name="code_generation_expert", name="assign_to_code_generation_expert", description=""),
        create_handoff_tool(agent_name="debug_expert", name="assign_to_debug_expert", description=""),
        create_handoff_tool(agent_name="evaluation_expert", name="assign_to_evaluation_expert", description="")
    ],
    model=model,
    prompt=SUPERVISOR_PROMPT,
    output_mode="last_message",
    include_agent_name="inline",
    parallel_tool_calls=False
    
)

# Compile and run
app = workflow.compile(
    checkpointer=checkpointer,
    store=store
)
