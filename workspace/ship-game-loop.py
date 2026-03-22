"""
Ship Game Loop: Full tick-based simulation of a spaceship

Demonstrates the complete game loop concept from the spaceship framework
article: a multi-component ship ticking forward each frame, with power
generation, distribution, and consumption all driven by the stepper.

Ship Layout:
    Reactor --[cable]--> Shield
    Reactor --[cable]--> Weapons
    Reactor --[cable]--> Sensors --> [display]

Each tick:
    1. Reactor generates power at the current throttle
    2. Cables transmit (with loss) to each subsystem
    3. Each subsystem processes its input
    4. Status is printed to the "HUD"

Run:
    python ship-game-loop.py
"""

from hyperway.graph import Graph
from hyperway.nodes import as_unit
from hyperway.packer import argspack

import io
import contextlib


# -- Ship Components -----------------------------------------------------------

class Reactor:
    """Primary power reactor."""

    def __init__(self, max_output=200):
        self.max_output = max_output
        self.fuel = 100.0
        self.throttle = 1.0

    def generate(self, signal=None):
        """Generate power. Ignores incoming signal; uses internal throttle."""
        if self.fuel <= 0:
            return 0
        self.fuel -= self.throttle * 0.5
        self.fuel = max(0, self.fuel)
        return self.max_output * self.throttle


class Shield:
    """Forward shield array."""

    def __init__(self):
        self.charge = 0
        self.max_charge = 100

    def receive_power(self, watts=0):
        """Charge shields from incoming power."""
        self.charge = min(self.max_charge, self.charge + watts * 0.05)
        return self.charge


class Weapons:
    """Primary weapons array."""

    def __init__(self):
        self.charge = 0
        self.ready = False

    def receive_power(self, watts=0):
        """Charge weapons capacitor. Ready to fire at 50+."""
        self.charge = min(100, self.charge + watts * 0.03)
        self.ready = self.charge >= 50
        return self.charge


class Sensors:
    """Long-range sensor array."""

    def __init__(self):
        self.range = 0
        self.online = False

    def receive_power(self, watts=0):
        """Sensors need at least 30W to function."""
        self.online = watts >= 30
        self.range = watts * 2 if self.online else 0
        return self.range


# -- Cable Wire Functions ------------------------------------------------------

def power_cable(watts, *a, **kw):
    """Standard power cable: 10% loss."""
    return argspack(watts * 0.9, **kw)


def heavy_cable(watts, *a, **kw):
    """Heavy-duty cable for weapons: 5% loss."""
    return argspack(watts * 0.95, **kw)


def sensor_cable(watts, *a, **kw):
    """Lightweight data/power cable: 15% loss."""
    return argspack(watts * 0.85, **kw)


def display_readout(value, *a, **kw):
    """Wire function that logs sensor data in transit."""
    return argspack(value, **kw)


# -- HUD Display ---------------------------------------------------------------

def print_hud(tick, reactor, shield, weapons, sensors):
    """Print a compact status display."""
    fuel_bar = int(reactor.fuel / 5)
    shield_bar = int(shield.charge / 5)
    weapon_bar = int(weapons.charge / 5)

    print(f"  Tick {tick:3d} | "
          f"Fuel [{'#' * fuel_bar}{'.' * (20 - fuel_bar)}] {reactor.fuel:5.1f}% | "
          f"Shield [{'#' * shield_bar}{'.' * (20 - shield_bar)}] {shield.charge:5.1f} | "
          f"Weapons [{'#' * weapon_bar}{'.' * (20 - weapon_bar)}] "
          f"{'READY' if weapons.ready else f'{weapons.charge:.0f}':>5s} | "
          f"Sensors {'ON ' if sensors.online else 'OFF'} "
          f"(range: {sensors.range:.0f})")


# -- Build Ship ----------------------------------------------------------------

def build_ship():
    """Wire up all ship components and return the graph + components."""
    reactor = Reactor(max_output=200)
    shield = Shield()
    weapons = Weapons()
    sensors = Sensors()

    g = Graph(tuple)

    # Pre-wrap so the same Unit is shared across all connections
    reactor_unit = as_unit(reactor.generate)

    # Wire the reactor to all subsystems through their cables
    g.add(reactor_unit, shield.receive_power, through=power_cable)
    g.add(reactor_unit, weapons.receive_power, through=heavy_cable)
    g.add(reactor_unit, sensors.receive_power, through=sensor_cable)

    return g, reactor, reactor_unit, shield, weapons, sensors


# -- Game Loop -----------------------------------------------------------------

def run_game_loop(total_ticks=40):
    """Simulate the ship for N ticks."""
    g, reactor, reactor_unit, shield, weapons, sensors = build_ship()

    print("=" * 110)
    print("SHIP SYSTEMS ONLINE")
    print("=" * 110)

    for tick in range(1, total_ticks + 1):
        # Events at specific ticks
        if tick == 10:
            print("\n  >>> CAPTAIN: Reduce throttle to 60% to conserve fuel.")
            reactor.throttle = 0.6

        if tick == 20:
            print("\n  >>> CAPTAIN: Weapons charged! All power to shields!")
            reactor.throttle = 1.0

        if tick == 30:
            print("\n  >>> CAPTAIN: Fuel critical. Minimum power.")
            reactor.throttle = 0.3

        # Prepare stepper fresh each tick (reactor reads internal throttle)
        g.stepper_prepare(reactor_unit)
        s = g.stepper()

        # Step until all signals reach endpoints (suppress library debug output)
        with contextlib.redirect_stdout(io.StringIO()):
            while True:
                rows = s.step()
                if not rows:
                    break

        # Display status
        print_hud(tick, reactor, shield, weapons, sensors)

        # Check game-over condition
        if reactor.fuel <= 0:
            print(f"\n  >>> ENGINEERING: Reactor fuel depleted at tick {tick}!")
            break

    # Final report
    print()
    print("=" * 110)
    print("MISSION SUMMARY")
    print("=" * 110)
    print(f"  Ticks survived: {tick}")
    print(f"  Final fuel: {reactor.fuel:.1f}%")
    print(f"  Final shield charge: {shield.charge:.1f}/{shield.max_charge}")
    print(f"  Weapons ready: {'YES' if weapons.ready else 'NO'}"
          f" ({weapons.charge:.1f}/100)")
    print(f"  Sensors: {'ONLINE' if sensors.online else 'OFFLINE'}"
          f" (range: {sensors.range:.0f})")
    print()


# -- Main ----------------------------------------------------------------------

if __name__ == '__main__':
    print()
    print("*" * 110)
    print("SPACESHIP GAME LOOP: Tick-Based Simulation with Hyperway")
    print("*" * 110)
    print()

    run_game_loop(total_ticks=40)

    print("*" * 110)
    print("Done! See docs/spaceship-operating-framework.md for details.")
    print("*" * 110)
