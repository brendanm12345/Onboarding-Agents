from dataclasses import dataclass
from typing import Optional
import bgym
from agentlab.agents.agent_args import AgentArgs
from agentlab.llm.chat_api import BaseModelArgs
from agentlab.agents import dynamic_prompting as dp
from agentlab.agents.generic_agent import GenericAgent, GenericPromptFlags
from custom_action_mapping import custom_action_mapping, get_workflow_action_space_description

@dataclass
class CustomAgentArgs(AgentArgs):
    chat_model_args: BaseModelArgs = None
    flags: GenericPromptFlags = None
    max_retry: int = 4

    def __post_init__(self):
        try:
            self.agent_name = f"CustomAgent-{self.chat_model_args.model_name}".replace("/", "_")
        except AttributeError:
            pass

    def set_benchmark(self, benchmark: bgym.Benchmark, demo_mode):
        """Override flags based on the benchmark."""
        if benchmark.name.startswith("miniwob"):
            self.flags.obs.use_html = True

        self.flags.obs.use_tabs = benchmark.is_multi_tab
        self.flags.action.action_set = benchmark.high_level_action_set_args

        if self.flags.action.multi_actions is not None:
            self.flags.action.action_set.multiaction = self.flags.action.multi_actions
        if self.flags.action.is_strict is not None:
            self.flags.action.action_set.strict = self.flags.action.is_strict

        if demo_mode:
            self.flags.action.action_set.demo_mode = "all_blue"

    def make_agent(self):
        return CustomAgent(
            chat_model_args=self.chat_model_args,
            flags=self.flags,
            max_retry=self.max_retry
        )

class CustomAgent(GenericAgent):
    """Custom agent that extends GenericAgent with workflow actions."""
    
    def __init__(
        self,
        chat_model_args: BaseModelArgs,
        flags: GenericPromptFlags,
        max_retry: int = 4,
    ):
        super().__init__(chat_model_args=chat_model_args, flags=flags, max_retry=max_retry)
        
        # Override the action set's to_python_code method with our custom mapping
        self.action_set.to_python_code = lambda action_str: custom_action_mapping(action_str)

    def get_action(self, obs):
        # Get current URL from observation
        current_url = None
        if len(obs["open_pages_urls"]) > 0:
            active_idx = obs.get("active_page_index", 0)
            if 0 <= active_idx < len(obs["open_pages_urls"]):
                current_url = obs["open_pages_urls"][active_idx]

        # Extend the action space description with workflow actions
        workflow_actions = get_workflow_action_space_description(url=current_url)
        
        # Inject the workflow actions into the action space description
        original_desc = self.action_set.describe(with_long_description=False, with_examples=True)
        extended_desc = f"{original_desc}\n\n# Workflow Actions\n{workflow_actions}"
        self.action_set._description = extended_desc

        # Get action using parent implementation
        action, agent_info = super().get_action(obs)
        
        return action, agent_info