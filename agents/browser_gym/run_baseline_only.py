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

def parse_args():
    parser = argparse.ArgumentParser(description="Run WorkArena benchmark comparison.")
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

    # we would later add our agent to this list if baseline works
    agents = [AGENT_4o]

    benchmark = "workarena_l1"

    print("Creating benchmark study...")
    study = make_study(
        benchmark=benchmark,
        agent_args=agents,
        logging_level_stdout=logging.INFO,
        comment="WorkArena L1 Benchmark: Baseline"
    )

    print(f"Running study with {len(agents)} agent(s) using {args.n_jobs} parallel job(s)")
    study.run(n_jobs=args.n_jobs)

    print("\nResults Summary:")
    study.print_summary()
    print(f"\nDetailed results saved to: {study.study_dir}")
    print("To analyze results in detail, run: agentlab-xray")

if __name__ == "__main__":
    main()