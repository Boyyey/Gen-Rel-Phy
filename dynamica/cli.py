"""Command-line entry: spacetime-lab campaign|serve|validate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="spacetime-lab")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("campaign", help="run the full computational campaign")
    c.add_argument("--quick", action="store_true")
    c.add_argument("-o", "--out", default="results/campaign.json")

    sub.add_parser("validate", help="analytic-solution and self-convergence checks")

    s = sub.add_parser("serve", help="launch the interactive laboratory")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8000)

    args = p.parse_args(argv)
    if args.cmd == "campaign":
        from dynamica.lab.experiments import run_full_campaign

        data = run_full_campaign(quick=args.quick)
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2))
        print(f"wrote {path}")
    elif args.cmd == "validate":
        from dynamica.lab.experiments import experiment_known_solutions, experiment_convergence

        print(json.dumps({"known": experiment_known_solutions(), "conv": experiment_convergence()}, indent=2))
    elif args.cmd == "serve":
        import uvicorn

        uvicorn.run("app.server:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
