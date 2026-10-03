from pathlib import Path
import json
from dynamica.lab.experiments import experiment_known_solutions, experiment_convergence, experiment_spin_ringdown

def main():
    out = Path("results")
    out.mkdir(exist_ok=True)
    data = {
        "known_solutions": experiment_known_solutions(),
        "convergence": experiment_convergence(),
        "spin_ringdown": experiment_spin_ringdown(),
    }
    (out / "validate.json").write_text(json.dumps(data, indent=2))
    print("wrote results/validate.json")
    print("QNM residual Re:", data["known_solutions"]["qnm_re_error"])
    print("observed order (energy):", data["convergence"]["observed_order_energy"])

if __name__ == "__main__":
    main()
