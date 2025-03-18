import argparse
import random
from browsergym.experiments import EnvArgs, ExpArgs, get_exp_result
from browsergym.workarena import ALL_WORKARENA_TASKS

from agents.browser_gym.agent import DemoAgentArgs
from agents.browser_gym.custom_action_mapping import (
    load_workflow_functions,
    get_workflow_action_space_description
)

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

    sampled_task = random.choice(ALL_WORKARENA_TASKS)
    task_name = sampled_task.get_task_id()
    print(f"Randomly sampled WorkArena task: {task_name}")

    # setting up agent config
    agent_args = DemoAgentArgs(
        model_name=args.model_name,
        chat_mode=True,
        demo_mode="default" if args.visual_effects else "off",
        use_html=args.use_html,
        use_axtree=args.use_axtree,
        use_screenshot=args.use_screenshot,
    )

    # print("\n=== Debugging Workflow Action Space ===")
    # workflow_funcs = load_workflow_functions()
    # print(f"Found workflow functions: {list(workflow_funcs.keys())}")

    # print("\n=== Debug Workflow Description ===")
    # print(get_workflow_action_space_description())
    # print("=================================\n")


    # setting up environment config
    env_args = EnvArgs(
        task_name=task_name,
        task_seed=None,
        max_steps=100,
        headless=False,  # keep the browser open
        storage_state="auth/auth.json",
    )

    # # for openended task, set environment and agent to interactive chat mode on a start url
    # if args.task_name == "openended":
    #     agent_args.chat_mode = True
    #     env_args.wait_for_user_message = True
    #     env_args.task_kwargs = {"start_url": args.start_url}

    # setting up the experiment
    exp_args = ExpArgs(
        env_args=env_args,
        agent_args=agent_args,
    )

    exp_args.prepare("agents/browser_gym/results")
    exp_args.run()

    # loading and printing results 
    exp_result = get_exp_result(exp_args.exp_dir)
    exp_record = exp_result.get_exp_record()

    for key, val in exp_record.items():
        print(f"{key}: {val}")

if __name__ == "__main__":
    main()