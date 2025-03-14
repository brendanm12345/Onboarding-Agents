import os
import argparse
from agentlab.experiments.study import make_study
from agents.browser_gym.agent import DemoAgentArgs

AGENT_ROOT = os.path.dirname(os.path.abspath(__file__))
EXP_ROOT = os.path.join(AGENT_ROOT, "experiment_results")
os.makedirs(EXP_ROOT, exist_ok=True)
os.environ["AGENTLAB_EXP_ROOT"] = EXP_ROOT

def run_workarena_benchmark(task_ids=None):
    workflow_agent = DemoAgentArgs(
        model_name="gpt-4o-mini",
        use_axtree=True,
        chat_mode=False,
        demo_mode="on"
    )

    # Create the study with specific task IDs if provided
    study = make_study(
        benchmark="workarena_l1",
        agent_args=[workflow_agent],
        comment="Workflow Agent Evaluation",
        # task_ids=task_ids  # This filters to only run specified tasks
    )

    # Run the study
    study.run(n_jobs=1 if len(task_ids or []) == 1 else 5)  # Single job for single task

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--tasks",
        type=str,
        help="Comma-separated list of task IDs to run (e.g., 'order-ipad-pro,order-standard-laptop'). If not specified, runs all tasks."
    )
    args = parser.parse_args()

    task_ids = args.tasks.split(",") if args.tasks else None
    run_workarena_benchmark(task_ids)