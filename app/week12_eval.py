"""
Week 12 Capstone Evaluation Suite.

Week 12 is the Capstone project (Tier-1 Deflection Assistant).
This module aliases `app.capstone_eval` so both:
  python -m app.week12_eval
and
  python -m app.capstone_eval
run the complete 30-case integrated evaluation benchmark.
"""

from app.capstone_eval import *

if __name__ == "__main__":
    run_capstone_eval_suite(verbose=True)