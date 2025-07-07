#!/usr/bin/env python3  
import argparse, logging, sys  
from vllm_bench.orchestrator import run_all  
  
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")  
  
def main(argv=None):  
    parser = argparse.ArgumentParser("vllm-bench")
    parser.add_argument("-c", "--config", required=True, help="Path to yaml")
    args = parser.parse_args(argv)
    run_all(args.config)
  
if __name__ == "__main__":  
    sys.exit(main())