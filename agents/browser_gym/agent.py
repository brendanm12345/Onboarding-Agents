
import dataclasses
import logging
import openai
from browsergym.core.action.highlevel import HighLevelActionSet
from browsergym.core.action.python import PythonActionSet
from browsergym.experiments import AbstractAgentArgs, Agent
from browsergym.utils.obs import flatten_axtree_to_str, flatten_dom_to_str, prune_html
from custom_action_mapping import custom_action_mapping

from agents.browser_gym.utils import deduplicate_axtree, image_to_jpg_base64_url
from agents.browser_gym.custom_action_mapping import get_workflow_action_space_description

logger = logging.getLogger(__name__)

class DemoAgent(Agent):
    """A basic agent using OpenAI API, to demonstrate BrowserGym's functionalities."""

    def obs_preprocessor(self, obs: dict) -> dict:

        return {
            "chat_messages": obs["chat_messages"],
            "screenshot": obs["screenshot"],
            "goal_object": obs["goal_object"],
            "last_action": obs["last_action"],
            "last_action_error": obs["last_action_error"],
            "open_pages_urls": obs["open_pages_urls"],
            "open_pages_titles": obs["open_pages_titles"],
            "active_page_index": obs["active_page_index"],
            "axtree_txt": deduplicate_axtree(flatten_axtree_to_str(obs["axtree_object"]), threshold=50),
            "pruned_html": prune_html(flatten_dom_to_str(obs["dom_object"])),
        }

    def __init__(
        self,
        model_name: str,
        chat_mode: bool,
        demo_mode: str,
        use_html: bool,
        use_axtree: bool,
        use_screenshot: bool,
    ) -> None:
        super().__init__()
        self.model_name = model_name
        self.chat_mode = chat_mode
        self.use_html = use_html
        self.use_axtree = use_axtree
        self.use_screenshot = use_screenshot

        if not (use_html or use_axtree):
            raise ValueError(f"Either use_html or use_axtree must be set to True.")

        self.openai_client = openai.OpenAI()

        self.action_set = HighLevelActionSet(
            subsets=["chat", "tab", "nav", "bid", "infeas"],  # define a subset of the action space
            # subsets=["chat", "bid", "coord", "infeas"] # allow the agent to also use x,y coordinates
            strict=False,  # less strict on the parsing of the actions
            multiaction=False,  # does not enable the agent to take multiple actions at once
            demo_mode=demo_mode,  # add visual effects
        )

        self.action_history = []

    def get_action(self, obs: dict) -> tuple[str, dict]:
        system_msgs = []
        user_msgs = []

        current_url = None
        if "open_page_urls" in obs and "active_page_index" in obs:
            active_page_index = obs["active_page_index"]
            if 0 <= active_page_index < len(obs["open_pages_urls"]):
                current_url = obs["open_pages_urls"][active_page_index]

        if self.chat_mode:
            system_msgs.append(
                {
                    "type": "text",
                    "text": f"""\
# Instructions

You are a UI Assistant, your goal is to help the user perform tasks using a web browser. You can
communicate with the user via a chat, to which the user gives you instructions and to which you
can send back messages. You have access to a web browser that both you and the user can see,
and with which only you can interact via specific commands.

Review the instructions from the user, the current state of the page and all other information
to find the best possible next action to accomplish your goal. Your answer will be interpreted
and executed by a program, make sure to follow the formatting instructions.
""",
                }
            )
            # append chat messages
            user_msgs.append(
                {
                    "type": "text",
                    "text": f"""\
# Chat Messages
""",
                }
            )
            for msg in obs["chat_messages"]:
                if msg["role"] in ("user", "assistant", "infeasible"):
                    user_msgs.append(
                        {
                            "type": "text",
                            "text": f"""\
- [{msg['role']}] {msg['message']}
""",
                        }
                    )
                elif msg["role"] == "user_image":
                    user_msgs.append({"type": "image_url", "image_url": msg["message"]})
                else:
                    raise ValueError(f"Unexpected chat message role {repr(msg['role'])}")

        else:
            assert obs["goal_object"], "The goal is missing."
            system_msgs.append(
                {
                    "type": "text",
                    "text": f"""\
# Instructions

Review the current state of the page and all other information to find the best
possible next action to accomplish your goal. Your answer will be interpreted
and executed by a program, make sure to follow the formatting instructions.
""",
                }
            )
            # append goal
            user_msgs.append(
                {
                    "type": "text",
                    "text": f"""\
# Goal
""",
                }
            )
            # goal_object is directly presented as a list of openai-style messages
            user_msgs.extend(obs["goal_object"])

        # append url of all open tabs
        user_msgs.append(
            {
                "type": "text",
                "text": f"""\
# Currently open tabs
""",
            }
        )
        for page_index, (page_url, page_title) in enumerate(
            zip(obs["open_pages_urls"], obs["open_pages_titles"])
        ):
            user_msgs.append(
                {
                    "type": "text",
                    "text": f"""\
Tab {page_index}{" (active tab)" if page_index == obs["active_page_index"] else ""}
  Title: {page_title}
  URL: {page_url}
""",
                }
            )

        # append page AXTree (if asked)
        if self.use_axtree:
            user_msgs.append(
                {
                    "type": "text",
                    "text": f"""\
# Current page Accessibility Tree

{obs["axtree_txt"][:1048500]}

""",
                }
            )
        # append page HTML (if asked)
        if self.use_html:
            user_msgs.append(
                {
                    "type": "text",
                    "text": f"""\
# Current page DOM

{obs["pruned_html"][:1048500]}

""",
                }
            )

        # append page screenshot (if asked)
        if self.use_screenshot:
            user_msgs.append(
                {
                    "type": "text",
                    "text": """\
# Current page Screenshot
""",
                }
            )
            user_msgs.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_to_jpg_base64_url(obs["screenshot"]),
                        "detail": "auto",
                    },  # Literal["low", "high", "auto"] = "auto"
                }
            )

        # append action space description
        action_space_raw = r"""# Standard Action Space
{action_space_description}

# Workflow Action Space - A library atomic subworkflows that your employer demonstrated to you that might be relevant to this task.

{workflow_action_space_description}

Please use the following format to select an action from either the standard action space or the workflow action space:
- For standard actions: STANDARD.<action_name>(<args>)  e.g., STANDARD.click(bid='123')
- For workflow actions: WORKFLOW.<action_name>(<args>) e.g., WORKFLOW.open_page(url='https://example.com')    

Please also prepend your action choice with chain-of-thought reasoning and wrap your action choice in triple backticks on a newline like these examples:

I now need to click on the Submit button to send the form. I will use the click action on the button, which has bid 12.
```STANDARD.click("12")```

I found the information requested by the user, I will send it to the chat.
```STANDARD.send_msg_to_user("The price for a 15\\" laptop is 1499 USD.")```

I see date input fields in the query build form and it looks the set_date_range function in our workflow libary was written for this so I'll just use that directly.
```WORKFLOW.set_date_range(start_date='2020-01', end_date='2024-12')```
"""
        user_msgs.append(
            {
                "type": "text",
                "text": f"{action_space_raw}".format(
                    action_space_description=self.action_set.describe(with_long_description=False, with_examples=True),
                    workflow_action_space_description=get_workflow_action_space_description(url=current_url)
                )
            }
        )

        # append past actions (and last error message) if any
        if self.action_history:
            user_msgs.append(
                {
                    "type": "text",
                    "text": f"""\
# History of past actions
""",
                }
            )
            user_msgs.extend(
                [
                    {
                        "type": "text",
                        "text": f"""\

{action}
""",
                    }
                    for action in self.action_history
                ]
            )

            if obs["last_action_error"]:
                user_msgs.append(
                    {
                        "type": "text",
                        "text": f"""\
# Error message from last action

{obs["last_action_error"]}

""",
                    }
                )

        # ask for the next action
        user_msgs.append(
            {
                "type": "text",
                "text": f"""\
# Next action

You will now think step by step and produce your next best action. Reflect on your past actions, any resulting error message, and the current state of the page before deciding on your next action.
""",
            }
        )

        prompt_text_strings = []
        for message in system_msgs + user_msgs:
            match message["type"]:
                case "text":
                    prompt_text_strings.append(message["text"])
                case "image_url":
                    image_url = message["image_url"]
                    if isinstance(message["image_url"], dict):
                        image_url = image_url["url"]
                    if image_url.startswith("data:image"):
                        prompt_text_strings.append(
                            "image_url: " + image_url[:30] + "... (truncated)"
                        )
                    else:
                        prompt_text_strings.append("image_url: " + image_url)
                case _:
                    raise ValueError(
                        f"Unknown message type {repr(message['type'])} in the task goal."
                    )
        full_prompt_txt = "\n".join(prompt_text_strings)
        logger.info(full_prompt_txt)

        # query OpenAI model
        response = self.openai_client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_msgs},
                {"role": "user", "content": user_msgs},
            ],
        )
        action = response.choices[0].message.content

        self.action_history.append(f"{action}")

        return action, {}


@dataclasses.dataclass
class DemoAgentArgs(AbstractAgentArgs):
    """
    This class is meant to store the arguments that define the agent.

    By isolating them in a dataclass, this ensures serialization without storing
    internal states of the agent.
    """

    model_name: str = "gpt-4o-mini"
    chat_mode: bool = False
    demo_mode: str = "off"
    use_html: bool = False
    use_axtree: bool = True
    use_screenshot: bool = False

    def make_agent(self):
        return DemoAgent(
            model_name=self.model_name,
            chat_mode=self.chat_mode,
            demo_mode=self.demo_mode,
            use_html=self.use_html,
            use_axtree=self.use_axtree,
            use_screenshot=self.use_screenshot,
        )
