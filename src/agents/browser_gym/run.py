import argparse

# locally defined agent
from agent import DemoAgentArgs

# browsergym experiments utils
from browsergym.experiments import EnvArgs, ExpArgs, get_exp_result

from custom_action_mapping import custom_action_mapping


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected.")


def parse_args():
    parser = argparse.ArgumentParser(description="Run experiment with hyperparameters.")
    parser.add_argument(
        "--model_name",
        type=str,
        default="gpt-4o",
        help="OpenAI model name.",
    )
    parser.add_argument(
        "--task_name",
        type=str,
        default="openended",
        help="Name of the Browsergym task to run. If 'openended', you need to specify a 'start_url'",
    )
    parser.add_argument(
        "--start_url",
        type=str,
        default="https://wrds-www.wharton.upenn.edu/",
        help="Starting URL (only for the openended task).",
    )
    parser.add_argument(
        "--visual_effects",
        type=str2bool,
        default=True,
        help="Add visual effects when the agents performs actions.",
    )
    parser.add_argument(
        "--use_html",
        type=str2bool,
        default=False,
        help="Use HTML in the agent's observation space.",
    )
    parser.add_argument(
        "--use_axtree",
        type=str2bool,
        default=True,
        help="Use AXTree in the agent's observation space.",
    )
    parser.add_argument(
        "--use_screenshot",
        type=str2bool,
        default=False,
        help="Use screenshot in the agent's observation space.",
    )

    return parser.parse_args()


def main():
    print(
        """\
--- WARNING ---
This is a basic agent for demo purposes.
Visit AgentLab for more capable agents with advanced features.
https://github.com/ServiceNow/AgentLab"""
    )

    args = parse_args()

    # Import the custom action mapping here
    from custom_action_mapping import custom_action_mapping

    # Monkey patch the ExpArgs run method to use our custom action mapping
    original_run = ExpArgs.run
    def patched_run(self):
        # Store the original action mapping
        if hasattr(self, '_original_action_mapping'):
            original_action_mapping = self._original_action_mapping
        else:
            self._original_action_mapping = None
            original_action_mapping = None
            
        try:
            # Override the env_args make_env to use our custom mapping
            original_make_env = self.env_args.make_env
            def patched_make_env(*args, **kwargs):
                kwargs['action_mapping'] = custom_action_mapping
                return original_make_env(*args, **kwargs)
            self.env_args.make_env = patched_make_env
            
            # Run the original method
            return original_run(self)
        finally:
            # Restore original methods
            self.env_args.make_env = original_make_env
            if original_action_mapping is not None:
                self._original_action_mapping = original_action_mapping
    
    # Apply the monkey patch
    ExpArgs.run = patched_run

    # setting up agent config
    agent_args = DemoAgentArgs(
        model_name=args.model_name,
        chat_mode=False,
        demo_mode="default" if args.visual_effects else "off",
        use_html=args.use_html,
        use_axtree=args.use_axtree,
        use_screenshot=args.use_screenshot,
    )

    # setting up environment config
    env_args = EnvArgs(
        task_name=args.task_name,
        task_seed=None,
        max_steps=100,
        headless=False,  # keep the browser open
        storage_state="src/scripts/workflows/f821e2ca-a8a7-47fd-9379-c9bdf4c9ca8d/auth.json"
    )

    # for openended task, set environment and agent to interactive chat mode on a start url
    if args.task_name == "openended":
        agent_args.chat_mode = True
        env_args.wait_for_user_message = True
        env_args.task_kwargs = {"start_url": args.start_url}

    # setting up the experiment
    exp_args = ExpArgs(
        env_args=env_args,
        agent_args=agent_args,
    )

    exp_args.prepare("src/agents/browser_gym/results")
    exp_args.run()

    # loading and printing results 
    exp_result = get_exp_result(exp_args.exp_dir)
    exp_record = exp_result.get_exp_record()

    for key, val in exp_record.items():
        print(f"{key}: {val}")

if __name__ == "__main__":
    main()