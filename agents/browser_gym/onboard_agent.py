from copy import deepcopy
from dataclasses import dataclass
import inspect
import logging
import re
from typing import Optional
import bgym
from agentlab.agents.agent_args import AgentArgs
from agentlab.llm.chat_api import BaseModelArgs
from agentlab.agents import dynamic_prompting as dp
from agentlab.agents.generic_agent.generic_agent import GenericAgent, GenericPromptFlags
from browsergym.core.action.highlevel import HighLevelActionSet
from browsergym.experiments.benchmark.base import HighLevelActionSetArgs
from load_workflow_functions import load_workflow_functions

logger = logging.getLogger(__name__)


class ExtendedActionSet(HighLevelActionSet):
    """Extends HighLevelActionSet to support workflow actions"""

    def __init__(self, *args, current_url: Optional[str] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._current_url = current_url
        self._base_description = None
        self.show_source = False
        # Load workflow functions when initializing
        self._workflow_functions = load_workflow_functions()

    def _set_current_url(self, url: str):
        """Update the current URL context"""
        self._current_url = url

    def _clean_source_code(self, source_code: str) -> str:
        """
        Remove docstring and empty lines from beginning of source code.
        """
        lines = source_code.split('\n')
        clean_lines = []
        in_docstring = False
        triple_quote = None
        found_code = False

        for line in lines[1:]:  # Skip function definition line
            stripped = line.strip()

            # Handle docstring detection
            if not in_docstring and (stripped.startswith('"""') or stripped.startswith("'''")):
                in_docstring = True
                triple_quote = stripped[:3]
                continue
            elif in_docstring and triple_quote in stripped:
                in_docstring = False
                continue
            elif in_docstring:
                continue

            # Skip empty lines at the beginning
            if not found_code and not stripped:
                continue

            # We've found actual code
            if stripped:
                found_code = True

            # Add the line if we're not in a docstring
            if not in_docstring:
                clean_lines.append(line)

        return '\n'.join(clean_lines)

    def describe(self, with_long_description: bool = True, with_examples: bool = True) -> str:
        """Override describe to include workflow actions based on current URL"""
        # Get base description from parent
        base_description = super().describe(with_long_description, with_examples)

        # Add workflow actions description
        logger.info("Executing describe")
        logger.info(
            f"Number of workflow functions loaded: {len(self._workflow_functions)}")

        if not self._workflow_functions:
            return base_description

        workflow_description = "\nWorkflow Actions:\n"

        for func_name, func_obj in self._workflow_functions.items():
            original_func = func_obj.original_func
            sig = func_obj.__signature__
            params = [p for p in sig.parameters.values()]
            sig_str = f"({', '.join(str(p) for p in params)})"
            docstring = inspect.getdoc(
                original_func) or "No description available"

            # Use the stored source code
            source_code = func_obj._source_code
            url_match = re.search(r'expect\(page\).to_have_url\("([^"]+)"\)',
                                  source_code)
            url_constraint = url_match.group(1) if url_match else None

            # Skip if URL doesn't match constraint
            # if self._current_url and url_constraint and not (self._current_url == url_constraint):
            #     continue

            # Add function signature and description
            workflow_description += f"\nWORKFLOW.{func_name}{sig_str}\n"

            if with_long_description:
                # Split docstring into lines and format
                doc_lines = docstring.split('\n')
                for line in doc_lines:
                    workflow_description += f"    {line.strip()}\n"

            if with_examples:
                # Generate example based on parameters
                example_args = []
                for param in params:
                    if param.annotation == str:
                        example_args.append(
                            f"{param.name}='example_{param.name}'")
                    elif param.annotation == int:
                        example_args.append(f"{param.name}=42")
                    elif param.annotation == float:
                        example_args.append(f"{param.name}=3.14")
                    elif param.annotation == bool:
                        example_args.append(f"{param.name}=True")
                    elif param.annotation == list:
                        example_args.append(f"{param.name}=['item1', 'item2']")
                    else:
                        example_args.append(f"{param.name}='value'")

                example = f"WORKFLOW.{func_name}({', '.join(example_args)})"
                workflow_description += "    Examples:\n"
                workflow_description += f"        {example}\n"

            if self.show_source:
                # Clean and add source code with proper indentation
                clean_code = self._clean_source_code(source_code)
                if clean_code.strip():  # Only add if there's code after cleaning
                    workflow_description += "\n    Source Code:\n"
                    for line in clean_code.split('\n'):
                        if line.strip():  # Only show non-empty lines
                            workflow_description += f"        {line}\n"
                    workflow_description += "\n"

        return base_description + workflow_description

    def to_python_code(self, action_str: str) -> str:
        """Convert action string to Python code"""
        logger.info(
            f"Executing to_python_code with action string: {action_str}")
        if action_str.startswith("WORKFLOW."):
            # Parse workflow action using similar approach to HighLevelActionSet
            try:
                action_part = action_str[len("WORKFLOW."):]
                if '(' not in action_part:
                    raise ValueError(
                        f"Invalid WORKFLOW action format: {action_str}")

                workflow_name, args_str = action_part.split('(', 1)
                args_str = args_str.rstrip(')')
                workflow_name = workflow_name.strip()

                logger.info(f"Extracted workflow name: {workflow_name}")

                if workflow_name not in self._workflow_functions:
                    raise ValueError(
                        f"Unknown workflow action: {workflow_name}")

                # Parse arguments similar to HighLevelActionSet's parser
                kwargs = {}
                if args_str.strip():
                    for arg_pair in args_str.split(','):
                        arg_pair = arg_pair.strip()
                        if '=' in arg_pair:
                            key, value = arg_pair.split('=', 1)
                            kwargs[key.strip()] = eval(value.strip())

                logger.info(f"Kwags for extracted workflow: {kwargs}")

                return self._workflow_functions[workflow_name](**kwargs)

            except Exception as e:
                raise ValueError(f"Error parsing workflow action: {e}")
        else:
            # This is a standard action, use parent class's parsing for standard actions
            return super().to_python_code(action_str)


@dataclass
class ExtendedActionSetArgs(HighLevelActionSetArgs):
    """Arguments for creating an ExtendedActionSet"""
    current_url: Optional[str] = None
    show_source: bool = True  # show source code for workflow actions in action space

    def make_action_set(self) -> ExtendedActionSet:
        """Create an ExtendedActionSet instance"""
        action_set = ExtendedActionSet(
            subsets=self.subsets,
            multiaction=self.multiaction,
            strict=self.strict,
            demo_mode=self.demo_mode,
            current_url=self.current_url
        )

        action_set.show_source = self.show_source

        return action_set


@dataclass
class OnboardAgentArgs(AgentArgs):
    chat_model_args: BaseModelArgs = None
    flags: GenericPromptFlags = None
    max_retry: int = 4
    show_source: bool = False

    def __post_init__(self):
        try:
            self.agent_name = f"OnboardAgent-{self.chat_model_args.model_name}".replace(
                "/", "_")

            if self.flags:
                self.flags.enable_chat = True

            # Initialize action set if it's not set
            if self.flags and self.flags.action and self.flags.action.action_set is None:
                action_set_args = ExtendedActionSetArgs(
                    subsets=["chat", "tab", "nav", "bid", "infeas"],
                    multiaction=False,
                    strict=False,
                    demo_mode="off",
                    show_source=self.show_source  # Use the stored value
                )
                self.flags.action.action_set = action_set_args

        except AttributeError as e:
            logger.info(f"AttributeError in __post_init__: {e}")
            pass

    def set_benchmark(self, benchmark: bgym.Benchmark, demo_mode):
        """Override flags based on the benchmark."""

        if benchmark.name.startswith("miniwob"):
            self.flags.obs.use_html = True

        self.flags.obs.use_tabs = benchmark.is_multi_tab

        # Update existing action set or create new one
        action_set_args = ExtendedActionSetArgs(
            subsets=["chat", "tab", "nav", "bid", "infeas"],
            multiaction=False,
            strict=False,
            demo_mode="all_blue" if demo_mode else "off",
            show_source=self.show_source
        )

        self.flags.action.action_set = action_set_args

    def make_agent(self):
        return OnboardAgent(
            chat_model_args=self.chat_model_args,
            flags=self.flags,
            max_retry=self.max_retry
        )


class OnboardAgent(GenericAgent):
    def __init__(
        self,
        chat_model_args: BaseModelArgs,
        flags: GenericPromptFlags,
        max_retry: int = 4,
    ):
        super().__init__(chat_model_args=chat_model_args, flags=flags, max_retry=max_retry)

    def _format_chat_message(self, msg):
        """Format a single chat message with proper indentation and formatting."""
        role = msg.get("role", "unknown")
        content = msg.get("content", "")

        # Handle both string and list content
        if isinstance(content, list):
            # For list content, process each item
            formatted_content = []
            for item in content:
                if isinstance(item, dict):
                    # Handle dict items (like type/text pairs)
                    for key, value in item.items():
                        if isinstance(value, str):
                            lines = value.split('\n')
                            formatted_content.extend(lines)
                elif isinstance(item, str):
                    # Handle string items directly
                    lines = item.split('\n')
                    formatted_content.extend(lines)
        else:
            # Handle string content
            formatted_content = content.split('\n')

        # Indent all lines
        indented_content = '\n    '.join(
            line.rstrip() for line in formatted_content)

        return f"[{role}]:\n    {indented_content}"

    def get_action(self, obs):
        # Update action set with current URL context
        current_url = None
        if len(obs["open_pages_urls"]) > 0:
            active_idx = obs.get("active_page_index", 0)
            if 0 <= active_idx < len(obs["open_pages_urls"]):
                current_url = obs["open_pages_urls"][int(active_idx)]

        # Update URL context in action set
        if isinstance(self.action_set, ExtendedActionSet):
            self.action_set._set_current_url(current_url)
            logger.info(f"Current URL context: {current_url}")

        # Get action using parent implementation
        action, agent_info = super().get_action(obs)

        # Log the conversation with improved formatting
        if agent_info.chat_messages:
            logger.info("\n" + "="*50)
            logger.info("Conversation")
            logger.info("="*50)

            for msg in agent_info.chat_messages:
                logger.info("\n" + self._format_chat_message(msg))

            logger.info("\n" + "="*50 + "\n")

        # Log thinking process if available
        if agent_info.think:
            logger.info("\n" + "="*50)
            logger.info("Thinking Process")
            logger.info("="*50)
            logger.info(agent_info.think)
            logger.info("="*50 + "\n")

        # Log action and stats
        logger.info("="*50)
        logger.info("Action and Stats")
        logger.info("="*50)
        logger.info(f"Action: {action}")
        logger.info(f"Stats: {agent_info.stats}")
        logger.info("="*50 + "\n")

        return action, agent_info
