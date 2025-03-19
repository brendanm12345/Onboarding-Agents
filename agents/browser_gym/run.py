import argparse
import random
from browsergym.experiments import EnvArgs, ExpArgs, get_exp_result
from browsergym.workarena import ALL_WORKARENA_TASKS
from agentlab.llm.chat_api import OpenAIModelArgs, OpenRouterModelArgs
from agentlab.agents.generic_agent.generic_agent_prompt import GenericPromptFlags
from agentlab.agents import dynamic_prompting as dp

from agents.browser_gym.onboarded_agent import CustomAgentArgs

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
    parser = argparse.ArgumentParser(description="Run experiment with custom agent.")
    parser.add_argument(
        "--model_name",
        type=str,
        default="gpt-4o",
        help="Model name to use",
    )
    parser.add_argument(
        "--visual_effects",
        type=str2bool,
        default=True,
        help="Add visual effects when the agent performs actions.",
    )
    parser.add_argument(
        "--use_html",
        type=str2bool,
        default=False,
        help="Use HTML in observation space",
    )
    parser.add_argument(
        "--use_axtree",
        type=str2bool,
        default=True,
        help="Use AXTree in observation space",
    )
    parser.add_argument(
        "--use_screenshot",
        type=str2bool,
        default=False,
        help="Use screenshot in observation space",
    )
    return parser.parse_args()

def main():
    args = parse_args()

    # Sample a random WorkArena L1 task
    sampled_task = random.choice(ALL_WORKARENA_TASKS)
    task_name = sampled_task.get_task_id()
    print(f"Sampled task: {sampled_task}")
    print(f"Randomly sampled WorkArena task: {task_name}")

    # Create model args based on the model name
    if args.model_name.startswith("gpt"):
        model_args = OpenAIModelArgs(
            model_name=args.model_name,
            temperature=0,  # Set temperature to 0 for deterministic output
        )
    elif "claude" in args.model_name.lower():
        model_args = OpenRouterModelArgs(
            model_name=args.model_name,
            temperature=0,
        )
    else:
        raise ValueError(f"Unsupported model: {args.model_name}. Please specify a supported model.")

    # Create prompt flags
    prompt_flags = GenericPromptFlags(
        obs=dp.ObsFlags(
            use_html=args.use_html,
            use_ax_tree=args.use_axtree,
            use_screenshot=args.use_screenshot,
        ),
        action=dp.ActionFlags(
            action_set=None,  # Will be set by set_benchmark
            multi_actions=False,
            is_strict=False,
        ),
    )

    # Create agent args
    agent_args = CustomAgentArgs(
        chat_model_args=model_args,
        flags=prompt_flags,
        max_retry=4,
    )

    # Create environment args
    env_args = EnvArgs(
        task_name=task_name,
        task_seed=None,
        max_steps=100,
        headless=False,
        storage_state="auth/auth.json",
    )

    # Create and run experiment
    exp_args = ExpArgs(
        env_args=env_args,
        agent_args=agent_args,
    )

    exp_args.prepare("results")
    exp_args.run()

    # Print results
    exp_result = get_exp_result(exp_args.exp_dir)
    exp_record = exp_result.get_exp_record()
    for key, val in exp_record.items():
        print(f"{key}: {val}")

if __name__ == "__main__":
    main()