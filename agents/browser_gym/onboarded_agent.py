# from copy import deepcopy
# from dataclasses import dataclass
# from typing import Optional
# import bgym
# from agentlab.agents.agent_args import AgentArgs
# from agentlab.llm.chat_api import BaseModelArgs
# from agentlab.agents import dynamic_prompting as dp
# from agentlab.agents.generic_agent.generic_agent import GenericAgent, GenericPromptFlags
# from custom_action_mapping import custom_action_mapping, get_workflow_action_space_description
# from browsergym.core.action.highlevel import HighLevelActionSet
# from browsergym.experiments.benchmark.base import HighLevelActionSetArgs

from copy import deepcopy
from dataclasses import dataclass
from typing import Optional
import bgym
from agentlab.agents.agent_args import AgentArgs
from agentlab.llm.chat_api import BaseModelArgs
from agentlab.agents import dynamic_prompting as dp
from agentlab.agents.generic_agent.generic_agent import GenericAgent, GenericPromptFlags
from browsergym.core.action.highlevel import HighLevelActionSet
from browsergym.experiments.benchmark.base import HighLevelActionSetArgs
from custom_action_mapping import custom_action_mapping, get_workflow_action_space_description

class ExtendedActionSet(HighLevelActionSet):
    """Extends HighLevelActionSet to support workflow actions"""
    
    def __init__(self, *args, current_url: Optional[str] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._current_url = current_url
        self._base_description = None
        # Load workflow functions when initializing
        self._workflow_functions = load_workflow_functions()
    
    def set_current_url(self, url: str):
        """Update the current URL context"""
        self._current_url = url
        
    def describe(self, with_long_description: bool = True, with_examples: bool = True) -> str:
        """Override describe to include workflow actions based on current URL"""
        # Get base description from parent
        base_description = super().describe(with_long_description, with_examples)
        
        # Add workflow actions description
        workflow_description = "\nWorkflow Actions:\n"
        
        for func_name, func_obj in self._workflow_functions.items():
            original_func = func_obj.original_func
            sig = func_obj.__signature__
            params = [p for p in sig.parameters.values()]
            sig_str = f"({', '.join(str(p) for p in params)})"
            docstring = inspect.getdoc(original_func) or "No description available"
            
            url_match = re.search(r'expect\(page\).to_have_url\("([^"]+)"\)', 
                                inspect.getsource(original_func))
            url_constraint = url_match.group(1) if url_match else None
            
            # Skip if URL doesn't match constraint
            if self._current_url and url_constraint and not (self._current_url == url_constraint):
                continue
                
            workflow_description += f"\nWORKFLOW.{func_name}{sig_str}\n"
            if with_long_description:
                workflow_description += f"    Description: {docstring}\n"
            if with_examples:
                workflow_description += "    Examples:\n"
                workflow_description += f"        WORKFLOW.{func_name}(arg1='value1')\n"
        
        return base_description + workflow_description

    def to_python_code(self, action_str: str) -> str:
        """Convert action string to Python code"""
        if action_str.startswith("WORKFLOW."):
            # Parse workflow action using similar approach to HighLevelActionSet
            try:
                action_part = action_str[len("WORKFLOW."):]
                if '(' not in action_part:
                    raise ValueError(f"Invalid WORKFLOW action format: {action_str}")
                
                workflow_name, args_str = action_part.split('(', 1)
                args_str = args_str.rstrip(')')
                workflow_name = workflow_name.strip()
                
                if workflow_name not in self._workflow_functions:
                    raise ValueError(f"Unknown workflow action: {workflow_name}")
                
                # Parse arguments similar to HighLevelActionSet's parser
                kwargs = {}
                if args_str.strip():
                    for arg_pair in args_str.split(','):
                        arg_pair = arg_pair.strip()
                        if '=' in arg_pair:
                            key, value = arg_pair.split('=', 1)
                            kwargs[key.strip()] = eval(value.strip())
                
                return self._workflow_functions[workflow_name](**kwargs)
                
            except Exception as e:
                raise ValueError(f"Error parsing workflow action: {e}")
        else:
            # Use parent class's parsing for standard actions
            return super().to_python_code(action_str)

@dataclass
class ExtendedActionSetArgs(HighLevelActionSetArgs):
    """Arguments for creating an ExtendedActionSet"""
    current_url: Optional[str] = None
    
    def make_action_set(self) -> ExtendedActionSet:
        """Create an ExtendedActionSet instance"""
        return ExtendedActionSet(
            subsets=self.subsets,
            multiaction=self.multiaction,
            strict=self.strict,
            demo_mode=self.demo_mode,
            current_url=self.current_url
        )
@dataclass
class CustomAgentArgs(AgentArgs):
    chat_model_args: BaseModelArgs = None
    flags: GenericPromptFlags = None
    max_retry: int = 4

    def __post_init__(self):
        print("CustomAgentArgs.__post_init__ called")
        try:
            self.agent_name = f"CustomAgent-{self.chat_model_args.model_name}".replace("/", "_")
            
            # Initialize action set if it's not set
            if self.flags and self.flags.action and self.flags.action.action_set is None:
                print("Initializing default action set in __post_init__")
                action_set_args = ExtendedActionSetArgs(
                    subsets=["chat", "tab", "nav", "bid", "infeas"],
                    multiaction=False,
                    strict=False,
                    demo_mode="off"
                )
                self.flags.action.action_set = action_set_args
                print(f"Action set initialized: {self.flags.action.action_set}")
                
        except AttributeError as e:
            print(f"AttributeError in __post_init__: {e}")
            pass

    def set_benchmark(self, benchmark: bgym.Benchmark, demo_mode):
        """Override flags based on the benchmark."""
        print(f"\nset_benchmark called with benchmark: {benchmark.name}")
        print(f"Initial flags.action.action_set: {self.flags.action.action_set}")
        
        if benchmark.name.startswith("miniwob"):
            self.flags.obs.use_html = True

        self.flags.obs.use_tabs = benchmark.is_multi_tab
        
        # Update existing action set or create new one
        action_set_args = ExtendedActionSetArgs(
            subsets=["chat", "tab", "nav", "bid", "infeas"],
            multiaction=False,
            strict=False,
            demo_mode="all_blue" if demo_mode else "off"
        )
        
        print(f"Created action_set_args: {action_set_args}")
        self.flags.action.action_set = action_set_args
        print(f"After setting, flags.action.action_set: {self.flags.action.action_set}")

    def make_agent(self):
        print("\nmaking agent...")
        print(f"flags.action.action_set before agent creation: {self.flags.action.action_set}")
        return CustomAgent(
            chat_model_args=self.chat_model_args,
            flags=self.flags,
            max_retry=self.max_retry
        )

class CustomAgent(GenericAgent):
    def __init__(
        self,
        chat_model_args: BaseModelArgs,
        flags: GenericPromptFlags,
        max_retry: int = 4,
    ):
        print("\nCustomAgent.__init__ called")
        print(f"flags.action.action_set before super().__init__: {flags.action.action_set}")
        super().__init__(chat_model_args=chat_model_args, flags=flags, max_retry=max_retry)

    def get_action(self, obs):
        # Update action set with current URL context
        current_url = None
        if len(obs["open_pages_urls"]) > 0:
            active_idx = obs.get("active_page_index", 0)
            if 0 <= active_idx < len(obs["open_pages_urls"]):
                current_url = obs["open_pages_urls"][int(active_idx,)]
        
        # Update URL context in action set
        if isinstance(self.action_set, ExtendedActionSet):
            self.action_set.set_current_url(current_url)

        # Get action using parent implementation 
        action, agent_info = super().get_action(obs)
        return action, agent_info