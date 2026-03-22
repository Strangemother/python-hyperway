"""
Ship Damage: Runtime reconfiguration of the wiring graph

Demonstrates how cables can degrade or be rerouted during gameplay,
as described in the spaceship framework article.

    Phase 1: Normal operation
        Reactor --[standard cable]--> Shield

    Phase 2: Battle damage
        Reactor --[damaged cable]--> Shield  (intermittent, lossy)

    Phase 3: Emergency reroute
        Backup Reactor --[emergency cable]--> Shield

Run:
    python ship-damage.py
"""

import random
from hyperway.graph import Graph
from hyperway.edges import make_edge
from hyperway.packer import argspack


# Fix random seed for reproducible demo output
random.seed(42)


# -- Ship Components -----------------------------------------------------------

class Reactor:
    """A power reactor."""

    def __init__(self, name, max_output=100):
        self.name = name
        self.max_output = max_output

    def generate(self, throttle=1.0):
        """Generate power."""
        watts = self.max_output * throttle
        print(f"  [{self.name}] Generating {watts:.1f}W")
        return watts


class Shield:
    """Shield generator tracking charge over time."""

    def __init__(self):
        self.charge = 0
        self.history = []

    def receive_power(self, watts=0):
        """Absorb power."""
        self.charge += watts * 0.1
        self.history.append(watts)
        print(f"  [Shields] Received {watts:.1f}W, charge: {self.charge:.1f}")
        return self.charge


# -- Cable Types ---------------------------------------------------------------

def standard_cable(watts, *a, **kw):
    """Normal cable: 10% loss."""
    delivered = watts * 0.9
    print(f"    [standard cable] {watts:.1f}W -> {delivered:.1f}W")
    return argspack(delivered, **kw)


def damaged_cable(watts, *a, **kw):
    """Battle-damaged cable: 40% loss + 30% dropout chance."""
    if random.random() < 0.3:
        print(f"    [damaged cable] {watts:.1f}W -> 0W (DROPOUT!)")
        return argspack(0, **kw)
    delivered = watts * 0.6
    print(f"    [damaged cable] {watts:.1f}W -> {delivered:.1f}W (degraded)")
    return argspack(delivered, **kw)


def emergency_cable(watts, *a, **kw):
    """Emergency bypass cable: 20% loss but reliable."""
    delivered = watts * 0.8
    print(f"    [emergency cable] {watts:.1f}W -> {delivered:.1f}W (bypass)")
    return argspack(delivered, **kw)


# -- Simulation ----------------------------------------------------------------

def run_phase(label, reactor, shield, cable_func, ticks=5):
    """Run several ticks with a given wiring configuration."""
    print(f"\n{'='*60}")
    print(f"Phase: {label}")
    print(f"{'='*60}")

    for tick in range(ticks):
        print(f"\n  Tick {tick + 1}:")
        # Build a fresh single-edge connection each tick
        conn = make_edge(reactor.generate, shield.receive_power,
                         through=cable_func)
        conn.pluck(1.0)

    print(f"\n  Shield charge after {ticks} ticks: {shield.charge:.1f}")
    print(f"  Power deliveries: {[f'{w:.0f}W' for w in shield.history[-ticks:]]}")


def main():
    print()
    print("*" * 60)
    print("SPACESHIP DAMAGE: Runtime Reconfiguration")
    print("*" * 60)

    main_reactor = Reactor('Main Reactor', max_output=100)
    backup_reactor = Reactor('Backup Reactor', max_output=80)
    shield = Shield()

    # Phase 1: Normal operation
    run_phase(
        "Normal Operation",
        main_reactor, shield, standard_cable, ticks=3,
    )

    # Phase 2: Cable takes battle damage
    print(f"\n{'!'*60}")
    print("!! IMPACT !! Main power cable damaged!")
    print(f"{'!'*60}")

    run_phase(
        "Battle Damage (degraded cable)",
        main_reactor, shield, damaged_cable, ticks=5,
    )

    # Phase 3: Engineering reroutes to backup reactor
    print(f"\n{'~'*60}")
    print("Engineering: Rerouting to backup reactor via emergency cable")
    print(f"{'~'*60}")

    run_phase(
        "Emergency Reroute (backup reactor + bypass cable)",
        backup_reactor, shield, emergency_cable, ticks=3,
    )

    # Summary
    print(f"\n{'='*60}")
    print("DAMAGE REPORT")
    print(f"{'='*60}")
    print(f"  Total ticks simulated: {len(shield.history)}")
    print(f"  Final shield charge: {shield.charge:.1f}")
    print(f"  Power delivery history:")

    phases = [
        ("Normal (3 ticks)", shield.history[:3]),
        ("Damaged (5 ticks)", shield.history[3:8]),
        ("Rerouted (3 ticks)", shield.history[8:]),
    ]
    for phase_name, deliveries in phases:
        avg = sum(deliveries) / len(deliveries) if deliveries else 0
        dropouts = sum(1 for w in deliveries if w == 0)
        print(f"    {phase_name}: avg {avg:.1f}W"
              f"{f', {dropouts} dropouts' if dropouts else ''}")

    print()


if __name__ == '__main__':
    main()
    print("*" * 60)
    print("Done! See docs/spaceship-operating-framework.md for details.")
    print("*" * 60)
