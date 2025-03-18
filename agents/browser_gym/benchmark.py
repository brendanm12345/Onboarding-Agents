#!/usr/bin/env python
import dataclasses
import os
import sys
import logging
import argparse
from pathlib import Path

from agentlab.experiments.study import make_study
from agentlab.agents.generic_agent import AGENT_4o
import browsergym as bgym

from agents.browser_gym.agent import DemoAgentArgs

def parse_args():
    parser = argparse.ArgumentParser(description="Run WorkArena benchmark comparison.")
    parser.add_argument(
        "--workflows_dir", 
        type=str, 
        default="workflows",
        help="Directory containing workflow definitions"
    )
    parser.add_argument(
        "--n_jobs", 
        type=int, 
        default=1,
        help="Number of parallel jobs to run"
    )
    parser.add_argument(
        "--run_baseline", 
        action="store_true",
        help="Include baseline agent in the benchmark"
    )
    parser.add_argument(
        "--model_name", 
        type=str, 
        default="gpt-4o",
        help="OpenAI model name to use"
    )
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Check environment setup
    if "OPENAI_API_KEY" not in os.environ:
        print("ERROR: OPENAI_API_KEY environment variable not set")
        sys.exit(1)

    if not os.path.exists(args.workflows_dir):
        print(f"ERROR: Workflows directory not found at {args.workflows_dir}")
        sys.exit(1)

    # Configure workflow agent
    workflow_agent = DemoAgentArgs(
        model_name=args.model_name,
        chat_mode=True,  # WorkArena uses chat mode
        demo_mode="off",
        use_html=False,
        use_axtree=True,
        use_screenshot=False,
    )

    # Set up agents list
    agents = [workflow_agent]
    if args.run_baseline:
        agents.append(AGENT_4o)

    agents = [AGENT_4o]

    # Get the benchmark
    benchmark = "workarena_l1"

    # Create and run study
    print("Creating benchmark study...")
    study = make_study(
        benchmark=benchmark,
        agent_args=agents,
        logging_level_stdout=logging.INFO,
        comment="WorkArena L1 Benchmark: Workflow Agent vs Baseline"
    )

    print(f"Running study with {len(agents)} agent(s) using {args.n_jobs} parallel job(s)")
    study.run(n_jobs=args.n_jobs)

    # Print results
    print("\nResults Summary:")
    study.print_summary()
    print(f"\nDetailed results saved to: {study.study_dir}")
    print("To analyze results in detail, run: agentlab-xray")

if __name__ == "__main__":
    main()