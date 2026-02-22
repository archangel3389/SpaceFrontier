#!/usr/bin/env python3
"""
Space Frontier - Unified Edition
A comprehensive real-time space strategy game combining the best features
from all previous implementations.

Features:
- Real-time gameplay with pygame
- Multiple star systems with explorable planets
- Diverse ship types (Scout, Fighter, Colony, Science, Cargo, Miner)
- Technology upgrade system (30+ levels)
- Real-time travel, combat, scanning, and mining
- Resource and fuel management
- Enemy encounters and combat
- Colonization mechanics
- Save/load functionality
- Touch-optimized mobile interface
"""

import pygame
import numpy as np
import json
import os
import math
import time
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
from datetime import datetime, timedelta


# ==================== CONSTANTS ====================

# Screen dimensions (adaptable for mobile/desktop)
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 1280

# Colors
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_SPACE_BLUE = (10, 20, 40)
COLOR_UI_BG = (20, 30, 50)
COLOR_UI_BORDER = (0, 200, 255)
COLOR_BUTTON = (30, 50, 80)
COLOR_BUTTON_HOVER = (50, 70, 100)
COLOR_BUTTON_ACTIVE = (70, 100, 140)
COLOR_TEXT = (200, 230, 255)
COLOR_TEXT_DIM = (120, 140, 160)
COLOR_SUCCESS = (0, 255, 100)
COLOR_DANGER = (255, 50, 50)
COLOR_WARNING = (255, 200, 0)
COLOR_GOLD = (255, 215, 0)

# Planet colors
COLOR_PLANET_COLONIZED = (0, 255, 100)
COLOR_PLANET_UNCOLONIZED = (100, 100, 100)
COLOR_PLANET_SCANNED = (150, 200, 255)

# Ship colors by type
COLOR_SHIP_SCOUT = (0, 255, 255)
COLOR_SHIP_FIGHTER = (255, 50, 50)
COLOR_SHIP_COLONY = (255, 255, 0)
COLOR_SHIP_SCIENCE = (150, 100, 255)
COLOR_SHIP_CARGO = (255, 150, 0)
COLOR_SHIP_MINER = (180, 120, 50)
COLOR_SHIP_CAPITAL = (255, 100, 200)

COLOR_ENEMY = (255, 0, 100)

# Star colors
COLOR_STAR_YELLOW = (255, 255, 200)
COLOR_STAR_BLUE = (150, 200, 255)
COLOR_STAR_RED = (255, 150, 150)

# Game state file
SAVE_FILE = "space_frontier_save.json"

# Game parameters
SCAN_BASE_TIME = 10.0  # seconds
MINE_BASE_TIME = 15.0  # seconds
COMBAT_TICK_RATE = 1.0  # seconds between combat rounds


# ==================== ENUMS AND DATA CLASSES ====================

class ShipType(Enum):
    SCOUT = "Scout Ship"
    FIGHTER = "Fighter"
    DESTROYER = "Destroyer"
    CAPITAL = "Capital Ship"
    COLONY = "Colony Ship"
    SCIENCE = "Science Vessel"
    CARGO = "Cargo Transport"
    MINER = "Mining Ship"


class TechType(Enum):
    WEAPONS = "Weapons"
    SHIELDS = "Shields"
    ENGINES = "Engines"
    SCANNERS = "Scanners"
    HYPERDRIVE = "Hyperdrive"
    MINING = "Mining"
    TELEPORT = "Teleportation"


class EnemyType(Enum):
    SCOUT = "Enemy Scout"
    FIGHTER = "Enemy Fighter"
    CRUISER = "Enemy Cruiser"
    HIVE = "Hive Ship"
    MOTHER_HIVE = "Mother-Hive"


@dataclass
class Technology:
    """Technology upgrade system with progressive levels"""
    weapons: int = 1
    shields: int = 0
    engines: int = 1
    scanners: int = 1
    hyperdrive: int = 1
    mining: int = 1
    teleport: int = 0
    
    def get_cost(self, tech_type: TechType) -> int:
        """Calculate cost for next level upgrade"""
        current_level = getattr(self, tech_type.name.lower())
        base_cost = 200
        return int(base_cost * (1.5 ** current_level))
    
    def get_name(self, tech_type: TechType) -> str:
        """Get descriptive name for technology level"""
        level = getattr(self, tech_type.name.lower())
        names = {
            TechType.WEAPONS: [
                "Plasma Cannons Mk1", "Laser Weapons", "Particle Beams",
                "Ion Cannons", "Antimatter Guns", "Quantum Annihilators"
            ],
            TechType.SHIELDS: [
                "No Shields", "Basic Shields", "Energy Shields",
                "Advanced Shields", "Super Shields", "Reality Shields"
            ],
            TechType.ENGINES: [
                "Ion Drives", "Fusion Drives", "Antimatter Drives",
                "Quantum Drives", "Subspace Engines", "Reality Drives"
            ],
            TechType.SCANNERS: [
                "Basic Sensors", "Enhanced Sensors", "Deep Space Sensors",
                "Quantum Sensors", "Subspace Sensors", "Omniscient Arrays"
            ],
            TechType.HYPERDRIVE: [
                "Warp Drive Mk1", "Enhanced Warp", "Quantum Warp",
                "Hyperspace Drive", "Subspace Drive", "Instant Jump"
            ],
            TechType.MINING: [
                "Basic Extractors", "Enhanced Drills", "Plasma Extractors",
                "Quantum Extractors", "Matter Converters", "Reality Harvesters"
            ],
            TechType.TELEPORT: [
                "No Teleport", "Experimental Teleport", "Basic Teleport",
                "Advanced Teleport", "Quantum Teleport", "Reality Shift"
            ]
        }
        
        name_list = names.get(tech_type, [f"Level {level}"])
        idx = min(level, len(name_list) - 1)
        if idx >= len(name_list) - 1 and level > len(name_list) - 1:
            return f"{name_list[-1]} Mk{level - len(name_list) + 2}"
        return name_list[idx] if idx < len(name_list) else f"Level {level}"


@dataclass
class Ship:
    """Player ship with real-time mechanics"""
    id: str
    name: str
    ship_type: ShipType
    system: str
    position: Tuple[float, float]
    
    health: int = 100
    max_health: int = 100
    fuel: int = 100
    max_fuel: int = 100
    
    # Travel state
    target_system: Optional[str] = None
    travel_progress: float = 0.0
    travel_start_time: Optional[float] = None
    travel_duration: float = 0.0
    
    # Action state
    scanning_target: Optional[str] = None
    scan_progress: float = 0.0
    scan_start_time: Optional[float] = None
    
    mining_target: Optional[str] = None
    mining_progress: float = 0.0
    mining_start_time: Optional[float] = None
    
    combat_target: Optional[str] = None
    last_combat_time: Optional[float] = None
    
    # UI state
    selected: bool = False
    
    def get_color(self) -> Tuple[int, int, int]:
        """Get ship display color"""
        colors = {
            ShipType.SCOUT: COLOR_SHIP_SCOUT,
            ShipType.FIGHTER: COLOR_SHIP_FIGHTER,
            ShipType.DESTROYER: COLOR_SHIP_FIGHTER,
            ShipType.CAPITAL: COLOR_SHIP_CAPITAL,
            ShipType.COLONY: COLOR_SHIP_COLONY,
            ShipType.SCIENCE: COLOR_SHIP_SCIENCE,
            ShipType.CARGO: COLOR_SHIP_CARGO,
            ShipType.MINER: COLOR_SHIP_MINER,
        }
        return colors.get(self.ship_type, COLOR_WHITE)
    
    def is_combat_capable(self) -> bool:
        """Check if ship can fight"""
        return self.ship_type in [ShipType.FIGHTER, ShipType.DESTROYER, ShipType.CAPITAL]
    
    def can_scan(self) -> bool:
        """Check if ship can scan"""
        return self.ship_type in [ShipType.SCOUT, ShipType.SCIENCE]
    
    def can_mine(self) -> bool:
        """Check if ship can mine"""
        return self.ship_type in [ShipType.MINER, ShipType.CARGO]
    
    def can_colonize(self) -> bool:
        """Check if ship can colonize"""
        return self.ship_type == ShipType.COLONY
    
    def get_combat_power(self, tech_level: int) -> int:
        """Get ship's combat power"""
        base_power = {
            ShipType.SCOUT: 3,
            ShipType.FIGHTER: 10,
            ShipType.DESTROYER: 20,
            ShipType.CAPITAL: 40,
            ShipType.COLONY: 2,
            ShipType.SCIENCE: 5,
            ShipType.CARGO: 3,
            ShipType.MINER: 5,
        }
        return base_power.get(self.ship_type, 1) + tech_level


@dataclass
class Planet:
    """Planet in a star system"""
    id: str
    name: str
    system: str
    position: Tuple[float, float]
    radius: int = 20
    
    # State
    colonized: bool = False
    scanned: bool = False
    
    # Resources
    population: int = 0
    resources: int = 0
    deuterium: int = 0
    
    # Infrastructure
    mining_stations: int = 0
    defenses: int = 0
    
    def get_color(self) -> Tuple[int, int, int]:
        """Get planet display color"""
        if self.colonized:
            return COLOR_PLANET_COLONIZED
        elif self.scanned:
            return COLOR_PLANET_SCANNED
        else:
            return COLOR_PLANET_UNCOLONIZED


@dataclass
class StarSystem:
    """Star system containing planets and objects"""
    id: str
    name: str
    position: Tuple[float, float]  # Galaxy map position
    discovered: bool = False
    planets: List[str] = field(default_factory=list)
    star_color: Tuple[int, int, int] = COLOR_STAR_YELLOW


@dataclass
class Enemy:
    """Enemy ship"""
    id: str
    name: str
    enemy_type: EnemyType
    system: str
    position: Tuple[float, float]
    health: int = 100
    max_health: int = 100
    weapons: int = 10
    shields: int = 5
    
    def get_combat_power(self) -> int:
        """Get enemy combat power"""
        return self.weapons


@dataclass
class GameState:
    """Main game state container"""
    # Player info
    player_name: str = "Commander"
    
    # Resources
    resources: int = 1000
    deuterium: int = 500
    
    # Technology
    tech: Technology = field(default_factory=Technology)
    
    # Game objects
    star_systems: Dict[str, StarSystem] = field(default_factory=dict)
    planets: Dict[str, Planet] = field(default_factory=dict)
    ships: Dict[str, Ship] = field(default_factory=dict)
    enemies: Dict[str, Enemy] = field(default_factory=dict)
    
    # Current view
    current_system: str = "sys_0"
    view_mode: str = "galaxy"  # galaxy, system, ship, planet, tech
    
    # Time tracking
    last_update_time: float = 0.0
    game_start_time: float = 0.0
    
    # UI state
    selected_ship_id: Optional[str] = None
    selected_planet_id: Optional[str] = None
    
    # Logs
    log: List[str] = field(default_factory=list)
    
    def add_log(self, message: str):
        """Add timestamped log entry"""
        timestamp = time.strftime("%H:%M:%S")
        self.log.append(f"[{timestamp}] {message}")
        if len(self.log) > 100:
            self.log = self.log[-100:]


# ==================== GAME INITIALIZATION ====================

def create_new_game(player_name: str) -> GameState:
    """Create new game with initial state"""
    game = GameState()
    game.player_name = player_name
    game.game_start_time = time.time()
    game.last_update_time = time.time()
    
    # Create 5 star systems
    systems_config = [
        ("Sol", (500, 500), True, COLOR_STAR_YELLOW),
        ("Alpha Centauri", (300, 700), False, COLOR_STAR_YELLOW),
        ("Sirius", (700, 300), False, COLOR_STAR_BLUE),
        ("Betelgeuse", (250, 300), False, COLOR_STAR_RED),
        ("Vega", (750, 750), False, COLOR_STAR_BLUE),
    ]
    
    planet_id_counter = 0
    
    for sys_id, (sys_name, sys_pos, discovered, star_color) in enumerate(systems_config):
        system = StarSystem(
            id=f"sys_{sys_id}",
            name=sys_name,
            position=sys_pos,
            discovered=discovered,
            star_color=star_color
        )
        game.star_systems[system.id] = system
        
        # Create 6-9 planets per system
        num_planets = 6 + (sys_id % 4)
        for p_idx in range(num_planets):
            angle = (p_idx * 360 / num_planets) * math.pi / 180
            distance = 150 + (p_idx * 60)
            px = 400 + distance * math.cos(angle)
            py = 640 + distance * math.sin(angle)
            
            planet = Planet(
                id=f"planet_{planet_id_counter}",
                name=f"{sys_name} {chr(65+p_idx)}",
                system=system.id,
                position=(px, py),
                radius=12 + (p_idx % 4) * 3,
                colonized=(sys_id == 0 and p_idx == 0),
                scanned=(sys_id == 0),
                population=1000000 if (sys_id == 0 and p_idx == 0) else 0,
                resources=30 + np.random.randint(20, 100),
                deuterium=20 + np.random.randint(10, 60),
            )
            
            game.planets[planet.id] = planet
            system.planets.append(planet.id)
            planet_id_counter += 1
    
    game.current_system = "sys_0"
    
    # Create starting fleet
    starting_ships = [
        ("USS Enterprise", ShipType.SCOUT, (350, 600)),
        ("USS Defender", ShipType.FIGHTER, (370, 620)),
        ("USS Pioneer", ShipType.COLONY, (330, 580)),
        ("USS Discovery", ShipType.SCIENCE, (390, 640)),
        ("USS Prospector", ShipType.MINER, (310, 560)),
    ]
    
    for idx, (name, ship_type, pos) in enumerate(starting_ships):
        ship = Ship(
            id=f"ship_{idx}",
            name=name,
            ship_type=ship_type,
            system="sys_0",
            position=pos
        )
        game.ships[ship.id] = ship
    
    # Add some enemies to explore systems
    for sys_id in range(1, len(systems_config)):
        if np.random.random() < 0.6:  # 60% chance
            enemy = Enemy(
                id=f"enemy_{sys_id}",
                name=f"Hostile {chr(65+sys_id)}",
                enemy_type=np.random.choice([EnemyType.SCOUT, EnemyType.FIGHTER, EnemyType.CRUISER]),
                system=f"sys_{sys_id}",
                position=(400 + np.random.randint(-100, 100), 640 + np.random.randint(-100, 100)),
                health=50 + sys_id * 20,
                max_health=50 + sys_id * 20,
                weapons=5 + sys_id * 3,
                shields=2 + sys_id * 2
            )
            game.enemies[enemy.id] = enemy
    
    game.add_log(f"Welcome, Commander {player_name}!")
    game.add_log("Space Frontier Command System initialized.")
    game.add_log("Starting from Sol System.")
    
    return game


# ==================== GAME LOGIC ====================

def update_game_state(game: GameState, dt: float):
    """Update all game state based on elapsed time"""
    current_time = time.time()
    
    # Update ships
    for ship_id, ship in list(game.ships.items()):
        # Travel updates
        if ship.target_system and ship.travel_start_time:
            elapsed = current_time - ship.travel_start_time
            ship.travel_progress = min(1.0, elapsed / ship.travel_duration)
            
            if ship.travel_progress >= 1.0:
                # Arrival
                old_system = game.star_systems[ship.system].name
                ship.system = ship.target_system
                new_system = game.star_systems[ship.system].name
                ship.target_system = None
                ship.travel_start_time = None
                ship.travel_progress = 0.0
                ship.position = (400, 640)
                
                game.add_log(f"{ship.name} arrived at {new_system}")
                
                # Discover system
                if not game.star_systems[ship.system].discovered:
                    game.star_systems[ship.system].discovered = True
                    game.add_log(f"System {new_system} discovered!")
        
        # Scanning updates
        if ship.scanning_target and ship.scan_start_time:
            elapsed = current_time - ship.scan_start_time
            scan_duration = SCAN_BASE_TIME / (1 + game.tech.scanners * 0.15)
            ship.scan_progress = min(1.0, elapsed / scan_duration)
            
            if ship.scan_progress >= 1.0:
                planet = game.planets[ship.scanning_target]
                planet.scanned = True
                ship.scanning_target = None
                ship.scan_start_time = None
                ship.scan_progress = 0.0
                game.add_log(f"{ship.name} scan complete: {planet.name}")
                game.add_log(f"  Resources: {planet.resources} | Deuterium: {planet.deuterium}")
        
        # Mining updates
        if ship.mining_target and ship.mining_start_time:
            elapsed = current_time - ship.mining_start_time
            mine_duration = MINE_BASE_TIME / (1 + game.tech.mining * 0.2)
            ship.mining_progress = min(1.0, elapsed / mine_duration)
            
            if ship.mining_progress >= 1.0:
                planet = game.planets.get(ship.mining_target)
                if planet and planet.resources > 0:
                    amount = 15 + game.tech.mining * 3
                    game.resources += amount
                    planet.resources = max(0, planet.resources - amount)
                    ship.mining_progress = 0.0
                    ship.mining_start_time = time.time()
                    game.add_log(f"{ship.name} mined {amount} resources")
        
        # Combat updates
        if ship.combat_target:
            enemy = game.enemies.get(ship.combat_target)
            if enemy and enemy.system == ship.system and ship.health > 0:
                # Combat round every COMBAT_TICK_RATE seconds
                if not ship.last_combat_time or (current_time - ship.last_combat_time) >= COMBAT_TICK_RATE:
                    ship.last_combat_time = current_time
                    
                    # Ship attacks enemy
                    ship_power = ship.get_combat_power(game.tech.weapons)
                    damage_to_enemy = max(1, ship_power - enemy.shields)
                    enemy.health -= damage_to_enemy
                    
                    # Enemy attacks ship
                    enemy_power = enemy.get_combat_power()
                    damage_to_ship = max(1, enemy_power - game.tech.shields)
                    ship.health -= damage_to_ship
                    
                    # Check results
                    if enemy.health <= 0:
                        game.add_log(f"{ship.name} destroyed {enemy.name}!")
                        del game.enemies[enemy.id]
                        ship.combat_target = None
                        ship.last_combat_time = None
                        reward = 100 + np.random.randint(50, 200)
                        game.resources += reward
                        game.add_log(f"Salvaged {reward} resources")
                    elif ship.health <= 0:
                        game.add_log(f"{ship.name} was destroyed!")
                        del game.ships[ship_id]
                        if game.selected_ship_id == ship_id:
                            game.selected_ship_id = None
            else:
                ship.combat_target = None
                ship.last_combat_time = None
    
    # Resource generation from colonies
    for planet in game.planets.values():
        if planet.colonized and planet.population > 0:
            res_per_min = (planet.population // 100000) + (planet.mining_stations * 3)
            game.resources += int(res_per_min * dt / 60.0)
    
    # Random events (low probability)
    if np.random.random() < 0.0005 * dt:
        events = [
            "Space anomaly detected on long-range sensors.",
            "Trading convoy spotted in nearby system.",
            "Unusual energy signature detected.",
            "Cosmic storm warning issued.",
        ]
        game.add_log(f"EVENT: {np.random.choice(events)}")


def calculate_travel_time(game: GameState, from_sys: str, to_sys: str) -> float:
    """Calculate travel time in seconds"""
    sys1 = game.star_systems[from_sys]
    sys2 = game.star_systems[to_sys]
    
    dx = sys2.position[0] - sys1.position[0]
    dy = sys2.position[1] - sys1.position[1]
    distance = math.sqrt(dx*dx + dy*dy)
    
    base_time = distance * 0.2
    time_reduction = game.tech.hyperdrive * 0.1
    actual_time = base_time * (1 - min(0.9, time_reduction))
    
    return max(5.0, actual_time)


def calculate_fuel_cost(game: GameState, from_sys: str, to_sys: str) -> int:
    """Calculate fuel cost for travel"""
    sys1 = game.star_systems[from_sys]
    sys2 = game.star_systems[to_sys]
    
    dx = sys2.position[0] - sys1.position[0]
    dy = sys2.position[1] - sys1.position[1]
    distance = math.sqrt(dx*dx + dy*dy)
    
    base_cost = int(distance * 0.15)
    cost_reduction = game.tech.engines * 0.03
    actual_cost = int(base_cost * (1 - min(0.8, cost_reduction)))
    
    return max(5, actual_cost)


def initiate_ship_travel(game: GameState, ship_id: str, target_system: str):
    """Start ship travel to another system"""
    ship = game.ships[ship_id]
    
    if ship.system == target_system:
        game.add_log(f"{ship.name} is already in that system!")
        return False
    
    travel_time = calculate_travel_time(game, ship.system, target_system)
    fuel_cost = calculate_fuel_cost(game, ship.system, target_system)
    
    if ship.fuel < fuel_cost:
        game.add_log(f"{ship.name} needs {fuel_cost} fuel (has {ship.fuel})")
        return False
    
    ship.fuel -= fuel_cost
    ship.target_system = target_system
    ship.travel_start_time = time.time()
    ship.travel_duration = travel_time
    ship.travel_progress = 0.0
    
    target_name = game.star_systems[target_system].name
    game.add_log(f"{ship.name} traveling to {target_name} (ETA: {int(travel_time)}s)")
    return True


def initiate_planet_scan(game: GameState, ship_id: str, planet_id: str):
    """Start scanning a planet"""
    ship = game.ships[ship_id]
    planet = game.planets[planet_id]
    
    if not ship.can_scan():
        game.add_log(f"{ship.name} cannot perform scans (needs Scout/Science)")
        return False
    
    if planet.system != ship.system:
        game.add_log(f"{planet.name} is in a different system!")
        return False
    
    if planet.scanned:
        game.add_log(f"{planet.name} is already scanned!")
        return False
    
    ship.scanning_target = planet.id
    ship.scan_start_time = time.time()
    ship.scan_progress = 0.0
    game.add_log(f"{ship.name} scanning {planet.name}...")
    return True


def initiate_mining(game: GameState, ship_id: str, planet_id: str):
    """Start mining a planet"""
    ship = game.ships[ship_id]
    planet = game.planets[planet_id]
    
    if not ship.can_mine():
        game.add_log(f"{ship.name} cannot mine (needs Miner/Cargo)")
        return False
    
    if planet.system != ship.system:
        game.add_log(f"{planet.name} is in a different system!")
        return False
    
    if not planet.scanned:
        game.add_log(f"{planet.name} must be scanned first!")
        return False
    
    if planet.resources <= 0:
        game.add_log(f"{planet.name} has no resources left!")
        return False
    
    ship.mining_target = planet.id
    ship.mining_start_time = time.time()
    ship.mining_progress = 0.0
    game.add_log(f"{ship.name} mining {planet.name}...")
    return True


def colonize_planet(game: GameState, ship_id: str, planet_id: str) -> bool:
    """Colonize a planet with colony ship"""
    ship = game.ships[ship_id]
    planet = game.planets[planet_id]
    
    if not ship.can_colonize():
        game.add_log(f"{ship.name} is not a Colony Ship!")
        return False
    
    if planet.system != ship.system:
        game.add_log(f"{planet.name} is in a different system!")
        return False
    
    if planet.colonized:
        game.add_log(f"{planet.name} is already colonized!")
        return False
    
    if not planet.scanned:
        game.add_log(f"{planet.name} must be scanned first!")
        return False
    
    cost = 500
    if game.resources < cost:
        game.add_log(f"Need {cost} resources (have {game.resources})")
        return False
    
    game.resources -= cost
    planet.colonized = True
    planet.population = 10000
    game.add_log(f"{ship.name} colonized {planet.name}!")
    return True


def engage_enemy(game: GameState, ship_id: str, enemy_id: str) -> bool:
    """Engage enemy in combat"""
    ship = game.ships[ship_id]
    enemy = game.enemies.get(enemy_id)
    
    if not enemy:
        game.add_log("Enemy not found!")
        return False
    
    if not ship.is_combat_capable():
        game.add_log(f"{ship.name} is not combat-capable!")
        return False
    
    if enemy.system != ship.system:
        game.add_log("Enemy is in a different system!")
        return False
    
    ship.combat_target = enemy.id
    ship.last_combat_time = None  # Will trigger immediately
    game.add_log(f"{ship.name} engaging {enemy.name}!")
    return True


def upgrade_technology(game: GameState, tech_type: TechType) -> bool:
    """Upgrade a technology"""
    cost = game.tech.get_cost(tech_type)
    
    if game.resources < cost:
        game.add_log(f"Need {cost} resources (have {game.resources})")
        return False
    
    game.resources -= cost
    current_level = getattr(game.tech, tech_type.name.lower())
    setattr(game.tech, tech_type.name.lower(), current_level + 1)
    new_name = game.tech.get_name(tech_type)
    game.add_log(f"Upgraded {tech_type.value} to level {current_level + 1}: {new_name}")
    return True


def build_mining_station(game: GameState, planet_id: str) -> bool:
    """Build mining station on planet"""
    planet = game.planets[planet_id]
    cost = 300
    
    if not planet.colonized:
        game.add_log(f"{planet.name} must be colonized first!")
        return False
    
    if game.resources < cost:
        game.add_log(f"Need {cost} resources (have {game.resources})")
        return False
    
    game.resources -= cost
    planet.mining_stations += 1
    game.add_log(f"Built mining station on {planet.name}!")
    return True


def build_defenses(game: GameState, planet_id: str) -> bool:
    """Build planetary defenses"""
    planet = game.planets[planet_id]
    cost = 200
    
    if not planet.colonized:
        game.add_log(f"{planet.name} must be colonized first!")
        return False
    
    if game.resources < cost:
        game.add_log(f"Need {cost} resources (have {game.resources})")
        return False
    
    game.resources -= cost
    planet.defenses += 10
    game.add_log(f"Built defenses on {planet.name}! (+10)")
    return True


def build_ship(game: GameState, ship_type: ShipType, system_id: str) -> bool:
    """Build a new ship"""
    costs = {
        ShipType.SCOUT: 150,
        ShipType.FIGHTER: 200,
        ShipType.DESTROYER: 400,
        ShipType.CAPITAL: 800,
        ShipType.COLONY: 500,
        ShipType.SCIENCE: 300,
        ShipType.CARGO: 250,
        ShipType.MINER: 300,
    }
    
    cost = costs.get(ship_type, 100)
    
    if game.resources < cost:
        game.add_log(f"Need {cost} resources (have {game.resources})")
        return False
    
    # Find colonized planet in system
    colonized_planets = [p for p in game.planets.values() 
                        if p.system == system_id and p.colonized]
    
    if not colonized_planets:
        game.add_log("Need a colonized planet in this system to build ships!")
        return False
    
    game.resources -= cost
    
    # Create new ship
    ship_id = f"ship_{len(game.ships)}"
    ship_name = f"{ship_type.value} {len(game.ships) + 1}"
    
    ship = Ship(
        id=ship_id,
        name=ship_name,
        ship_type=ship_type,
        system=system_id,
        position=(400 + np.random.randint(-50, 50), 640 + np.random.randint(-50, 50))
    )
    
    game.ships[ship_id] = ship
    game.add_log(f"Built {ship.name}!")
    return True


# ==================== SAVE/LOAD ====================

def save_game(game: GameState) -> bool:
    """Save game to file"""
    try:
        # Convert dataclasses to dicts
        save_data = {
            'player_name': game.player_name,
            'resources': game.resources,
            'deuterium': game.deuterium,
            'tech': asdict(game.tech),
            'star_systems': {k: asdict(v) for k, v in game.star_systems.items()},
            'planets': {k: asdict(v) for k, v in game.planets.items()},
            'ships': {k: asdict(v) for k, v in game.ships.items()},
            'enemies': {k: asdict(v) for k, v in game.enemies.items()},
            'current_system': game.current_system,
            'game_start_time': game.game_start_time,
            'log': game.log[-20:]  # Save last 20 logs
        }
        
        with open(SAVE_FILE, 'w') as f:
            json.dump(save_data, f, indent=2)
        
        return True
    except Exception as e:
        print(f"Save error: {e}")
        return False


def load_game() -> Optional[GameState]:
    """Load game from file"""
    try:
        if not os.path.exists(SAVE_FILE):
            return None
        
        with open(SAVE_FILE, 'r') as f:
            data = json.load(f)
        
        game = GameState()
        game.player_name = data['player_name']
        game.resources = data['resources']
        game.deuterium = data['deuterium']
        game.tech = Technology(**data['tech'])
        
        # Reconstruct star systems
        for sys_id, sys_data in data['star_systems'].items():
            system = StarSystem(**sys_data)
            game.star_systems[sys_id] = system
        
        # Reconstruct planets
        for planet_id, planet_data in data['planets'].items():
            planet = Planet(**planet_data)
            game.planets[planet_id] = planet
        
        # Reconstruct ships
        for ship_id, ship_data in data['ships'].items():
            # Convert ship_type string back to enum
            ship_data['ship_type'] = ShipType[ship_data['ship_type'].split('.')[1]]
            ship = Ship(**ship_data)
            game.ships[ship_id] = ship
        
        # Reconstruct enemies
        for enemy_id, enemy_data in data['enemies'].items():
            enemy_data['enemy_type'] = EnemyType[enemy_data['enemy_type'].split('.')[1]]
            enemy = Enemy(**enemy_data)
            game.enemies[enemy_id] = enemy
        
        game.current_system = data['current_system']
        game.game_start_time = data['game_start_time']
        game.last_update_time = time.time()
        game.log = data['log']
        
        return game
    except Exception as e:
        print(f"Load error: {e}")
        return None


# ==================== UI COMPONENTS ====================

class Button:
    """Simple button UI element"""
    def __init__(self, rect: pygame.Rect, text: str, color: Tuple[int, int, int] = COLOR_BUTTON):
        self.rect = rect
        self.text = text
        self.color = color
        self.hover = False
        self.active = False
    
    def draw(self, screen: pygame.Surface, font: pygame.font.Font):
        """Draw button"""
        color = COLOR_BUTTON_ACTIVE if self.active else (COLOR_BUTTON_HOVER if self.hover else self.color)
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, COLOR_UI_BORDER, self.rect, 2)
        
        text_surf = font.render(self.text, True, COLOR_TEXT)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle mouse events, return True if clicked"""
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                return True
        return False


def draw_text(screen: pygame.Surface, text: str, pos: Tuple[int, int], 
              font: pygame.font.Font, color: Tuple[int, int, int] = COLOR_TEXT):
    """Draw text at position"""
    surf = font.render(text, True, color)
    screen.blit(surf, pos)


def draw_progress_bar(screen: pygame.Surface, rect: pygame.Rect, progress: float, 
                     color: Tuple[int, int, int] = COLOR_SUCCESS):
    """Draw a progress bar"""
    pygame.draw.rect(screen, COLOR_UI_BG, rect)
    pygame.draw.rect(screen, COLOR_UI_BORDER, rect, 1)
    
    if progress > 0:
        fill_width = int(rect.width * min(1.0, progress))
        fill_rect = pygame.Rect(rect.x, rect.y, fill_width, rect.height)
        pygame.draw.rect(screen, color, fill_rect)


# ==================== MAIN GAME CLASS ====================

class SpaceFrontier:
    """Main game class"""
    
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Space Frontier")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Fonts
        self.font_large = pygame.font.Font(None, 36)
        self.font_medium = pygame.font.Font(None, 28)
        self.font_small = pygame.font.Font(None, 20)
        
        # Game state
        self.game: Optional[GameState] = None
        self.view_mode = "menu"  # menu, galaxy, system, ship, planet, tech
        
        # UI elements
        self.buttons: List[Button] = []
        
        # Camera for maps
        self.camera_offset = [0, 0]
        self.zoom = 1.0
    
    def run(self):
        """Main game loop"""
        while self.running:
            dt = self.clock.tick(60) / 1000.0  # Delta time in seconds
            
            self.handle_events()
            self.update(dt)
            self.render()
        
        pygame.quit()
    
    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            # Button handling
            for button in self.buttons:
                if button.handle_event(event):
                    self.handle_button_click(button)
            
            # Custom event handling based on view
            if self.view_mode == "galaxy":
                self.handle_galaxy_events(event)
            elif self.view_mode == "system":
                self.handle_system_events(event)
    
    def handle_button_click(self, button: Button):
        """Handle button clicks"""
        text = button.text
        
        # Menu buttons
        if text == "New Game":
            self.game = create_new_game("Commander")
            self.view_mode = "galaxy"
        elif text == "Load Game":
            loaded = load_game()
            if loaded:
                self.game = loaded
                self.view_mode = "galaxy"
                self.game.add_log("Game loaded successfully!")
            else:
                print("No save file found")
        elif text == "Quit":
            self.running = False
        
        # View navigation
        elif text == "Galaxy Map":
            self.view_mode = "galaxy"
        elif text == "System View":
            self.view_mode = "system"
        elif text == "Tech":
            self.view_mode = "tech"
        elif text == "Ships":
            self.view_mode = "ships"
        elif text == "Save":
            if save_game(self.game):
                self.game.add_log("Game saved!")
        elif text == "Back":
            if self.view_mode == "tech":
                self.view_mode = "galaxy"
            elif self.view_mode == "ship_detail":
                self.view_mode = "ships"
            elif self.view_mode == "planet_detail":
                self.view_mode = "system"
        
        # Tech upgrades
        elif text.startswith("Upgrade"):
            for tech_type in TechType:
                if tech_type.value in text:
                    upgrade_technology(self.game, tech_type)
                    break
        
        # Ship actions
        elif text == "Scan":
            if self.game.selected_ship_id:
                system = self.game.star_systems[self.game.ships[self.game.selected_ship_id].system]
                unscanned = [self.game.planets[pid] for pid in system.planets 
                           if not self.game.planets[pid].scanned]
                if unscanned:
                    initiate_planet_scan(self.game, self.game.selected_ship_id, unscanned[0].id)
        
        elif text == "Mine":
            if self.game.selected_ship_id and self.game.selected_planet_id:
                initiate_mining(self.game, self.game.selected_ship_id, self.game.selected_planet_id)
        
        elif text == "Colonize":
            if self.game.selected_ship_id and self.game.selected_planet_id:
                colonize_planet(self.game, self.game.selected_ship_id, self.game.selected_planet_id)
        
        elif text == "Attack":
            if self.game.selected_ship_id:
                ship = self.game.ships[self.game.selected_ship_id]
                enemies = [e for e in self.game.enemies.values() if e.system == ship.system]
                if enemies:
                    engage_enemy(self.game, self.game.selected_ship_id, enemies[0].id)
        
        # Planet actions
        elif text == "Build Mine":
            if self.game.selected_planet_id:
                build_mining_station(self.game, self.game.selected_planet_id)
        
        elif text == "Build Defense":
            if self.game.selected_planet_id:
                build_defenses(self.game, self.game.selected_planet_id)
        
        # Ship building
        elif text.startswith("Build"):
            for ship_type in ShipType:
                if ship_type.value in text:
                    build_ship(self.game, ship_type, self.game.current_system)
                    break
    
    def handle_galaxy_events(self, event: pygame.event.Event):
        """Handle events in galaxy view"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            
            # Check if clicking on a star system
            for system in self.game.star_systems.values():
                if system.discovered:
                    sx = 100 + system.position[0] * 0.6
                    sy = 200 + system.position[1] * 0.6
                    dist = math.sqrt((mx - sx)**2 + (my - sy)**2)
                    
                    if dist < 20:
                        self.game.current_system = system.id
                        self.view_mode = "system"
                        break
    
    def handle_system_events(self, event: pygame.event.Event):
        """Handle events in system view"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            
            system = self.game.star_systems[self.game.current_system]
            
            # Check if clicking on a planet
            for planet_id in system.planets:
                planet = self.game.planets[planet_id]
                px, py = planet.position
                dist = math.sqrt((mx - px)**2 + (my - py)**2)
                
                if dist < planet.radius:
                    self.game.selected_planet_id = planet.id
                    break
            
            # Check if clicking on a ship
            for ship in self.game.ships.values():
                if ship.system == system.id:
                    sx, sy = ship.position
                    dist = math.sqrt((mx - sx)**2 + (my - sy)**2)
                    
                    if dist < 15:
                        self.game.selected_ship_id = ship.id
                        for other_ship in self.game.ships.values():
                            other_ship.selected = False
                        ship.selected = True
                        break
    
    def update(self, dt: float):
        """Update game state"""
        if self.game and self.view_mode not in ["menu"]:
            update_game_state(self.game, dt)
    
    def render(self):
        """Render current view"""
        self.screen.fill(COLOR_BLACK)
        
        if self.view_mode == "menu":
            self.render_menu()
        elif self.view_mode == "galaxy":
            self.render_galaxy_view()
        elif self.view_mode == "system":
            self.render_system_view()
        elif self.view_mode == "tech":
            self.render_tech_view()
        elif self.view_mode == "ships":
            self.render_ships_view()
        
        pygame.display.flip()
    
    def render_menu(self):
        """Render main menu"""
        self.buttons = []
        
        # Title
        title = self.font_large.render("SPACE FRONTIER", True, COLOR_UI_BORDER)
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 200))
        
        # Subtitle
        subtitle = self.font_small.render("A Real-Time Space Strategy Game", True, COLOR_TEXT_DIM)
        self.screen.blit(subtitle, (SCREEN_WIDTH//2 - subtitle.get_width()//2, 250))
        
        # Buttons
        button_width = 300
        button_height = 60
        button_x = SCREEN_WIDTH//2 - button_width//2
        
        buttons_config = [
            ("New Game", 400),
            ("Load Game", 480),
            ("Quit", 560),
        ]
        
        for text, y in buttons_config:
            btn = Button(pygame.Rect(button_x, y, button_width, button_height), text)
            btn.draw(self.screen, self.font_medium)
            self.buttons.append(btn)
    
    def render_galaxy_view(self):
        """Render galaxy map"""
        self.buttons = []
        
        # Background
        self.screen.fill(COLOR_SPACE_BLUE)
        
        # Draw stars (background decoration)
        for i in range(100):
            x = (i * 73) % SCREEN_WIDTH
            y = (i * 117 + 200) % (SCREEN_HEIGHT - 300)
            pygame.draw.circle(self.screen, COLOR_WHITE, (x, y), 1)
        
        # Header
        pygame.draw.rect(self.screen, COLOR_UI_BG, (0, 0, SCREEN_WIDTH, 150))
        draw_text(self.screen, "GALAXY MAP", (20, 20), self.font_large, COLOR_UI_BORDER)
        draw_text(self.screen, f"Resources: {self.game.resources}", (20, 60), self.font_medium, COLOR_GOLD)
        draw_text(self.screen, f"Deuterium: {self.game.deuterium}", (20, 90), self.font_medium, COLOR_SHIP_SCOUT)
        
        # Navigation buttons
        nav_buttons = [
            ("System View", 520, 20),
            ("Tech", 660, 20),
            ("Save", 520, 70),
            ("Ships", 660, 70),
        ]
        
        for text, x, y in nav_buttons:
            btn = Button(pygame.Rect(x, y, 120, 40), text)
            btn.draw(self.screen, self.font_small)
            self.buttons.append(btn)
        
        # Draw star systems
        for system in self.game.star_systems.values():
            if system.discovered:
                sx = 100 + system.position[0] * 0.6
                sy = 200 + system.position[1] * 0.6
                
                # Draw star
                pygame.draw.circle(self.screen, system.star_color, (int(sx), int(sy)), 15)
                pygame.draw.circle(self.screen, COLOR_WHITE, (int(sx), int(sy)), 15, 2)
                
                # Draw name
                name_surf = self.font_small.render(system.name, True, COLOR_TEXT)
                self.screen.blit(name_surf, (int(sx) - name_surf.get_width()//2, int(sy) + 20))
                
                # Draw connection lines to other discovered systems
                for other_system in self.game.star_systems.values():
                    if other_system.discovered and other_system.id != system.id:
                        ox = 100 + other_system.position[0] * 0.6
                        oy = 200 + other_system.position[1] * 0.6
                        pygame.draw.line(self.screen, COLOR_TEXT_DIM, (int(sx), int(sy)), (int(ox), int(oy)), 1)
        
        # Current system indicator
        current_sys = self.game.star_systems[self.game.current_system]
        cx = 100 + current_sys.position[0] * 0.6
        cy = 200 + current_sys.position[1] * 0.6
        pygame.draw.circle(self.screen, COLOR_SUCCESS, (int(cx), int(cy)), 20, 3)
        
        # Log area
        self.render_log_area(SCREEN_HEIGHT - 200, 200)
    
    def render_system_view(self):
        """Render current star system"""
        self.buttons = []
        
        # Background
        self.screen.fill(COLOR_BLACK)
        
        system = self.game.star_systems[self.game.current_system]
        
        # Draw star at center
        star_x, star_y = 400, 200
        pygame.draw.circle(self.screen, system.star_color, (star_x, star_y), 30)
        
        # System name
        draw_text(self.screen, system.name, (10, 10), self.font_large, COLOR_UI_BORDER)
        
        # Draw planets
        for planet_id in system.planets:
            planet = self.game.planets[planet_id]
            px, py = planet.position
            
            # Planet circle
            pygame.draw.circle(self.screen, planet.get_color(), (int(px), int(py)), planet.radius)
            pygame.draw.circle(self.screen, COLOR_WHITE, (int(px), int(py)), planet.radius, 2)
            
            # Selected indicator
            if self.game.selected_planet_id == planet.id:
                pygame.draw.circle(self.screen, COLOR_WARNING, (int(px), int(py)), planet.radius + 5, 2)
            
            # Planet name
            name_surf = self.font_small.render(planet.name, True, COLOR_TEXT)
            self.screen.blit(name_surf, (int(px) - name_surf.get_width()//2, int(py) + planet.radius + 5))
        
        # Draw ships
        for ship in self.game.ships.values():
            if ship.system == system.id:
                sx, sy = ship.position
                
                # Ship indicator
                color = ship.get_color()
                if ship.selected:
                    pygame.draw.circle(self.screen, COLOR_WARNING, (int(sx), int(sy)), 12, 2)
                
                pygame.draw.polygon(self.screen, color, [
                    (int(sx), int(sy) - 10),
                    (int(sx) - 8, int(sy) + 10),
                    (int(sx) + 8, int(sy) + 10)
                ])
                
                # Travel progress
                if ship.target_system:
                    bar_rect = pygame.Rect(int(sx) - 20, int(sy) + 15, 40, 5)
                    draw_progress_bar(self.screen, bar_rect, ship.travel_progress, COLOR_SHIP_SCOUT)
                
                # Scan progress
                if ship.scanning_target:
                    bar_rect = pygame.Rect(int(sx) - 20, int(sy) + 22, 40, 5)
                    draw_progress_bar(self.screen, bar_rect, ship.scan_progress, COLOR_SUCCESS)
                
                # Mining progress
                if ship.mining_target:
                    bar_rect = pygame.Rect(int(sx) - 20, int(sy) + 29, 40, 5)
                    draw_progress_bar(self.screen, bar_rect, ship.mining_progress, COLOR_GOLD)
        
        # Draw enemies
        for enemy in self.game.enemies.values():
            if enemy.system == system.id:
                ex, ey = enemy.position
                pygame.draw.circle(self.screen, COLOR_ENEMY, (int(ex), int(ey)), 15)
                
                # Health bar
                bar_rect = pygame.Rect(int(ex) - 20, int(ey) + 20, 40, 5)
                draw_progress_bar(self.screen, bar_rect, enemy.health / enemy.max_health, COLOR_DANGER)
        
        # UI Panel
        panel_y = SCREEN_HEIGHT - 400
        pygame.draw.rect(self.screen, COLOR_UI_BG, (0, panel_y, SCREEN_WIDTH, 400))
        pygame.draw.line(self.screen, COLOR_UI_BORDER, (0, panel_y), (SCREEN_WIDTH, panel_y), 2)
        
        # Selected ship info
        if self.game.selected_ship_id:
            ship = self.game.ships.get(self.game.selected_ship_id)
            if ship:
                y_offset = panel_y + 10
                draw_text(self.screen, f"Ship: {ship.name}", (10, y_offset), self.font_medium, COLOR_WARNING)
                draw_text(self.screen, f"Type: {ship.ship_type.value}", (10, y_offset + 30), self.font_small)
                draw_text(self.screen, f"Health: {ship.health}/{ship.max_health}", (10, y_offset + 55), self.font_small)
                draw_text(self.screen, f"Fuel: {ship.fuel}/{ship.max_fuel}", (10, y_offset + 80), self.font_small)
                
                # Action buttons
                btn_y = y_offset + 110
                action_buttons = []
                
                if ship.can_scan():
                    action_buttons.append("Scan")
                if ship.can_mine():
                    action_buttons.append("Mine")
                if ship.can_colonize():
                    action_buttons.append("Colonize")
                if ship.is_combat_capable():
                    action_buttons.append("Attack")
                
                for i, text in enumerate(action_buttons):
                    btn = Button(pygame.Rect(10 + i * 95, btn_y, 90, 35), text)
                    btn.draw(self.screen, self.font_small)
                    self.buttons.append(btn)
        
        # Selected planet info
        if self.game.selected_planet_id:
            planet = self.game.planets.get(self.game.selected_planet_id)
            if planet:
                y_offset = panel_y + 10
                x_offset = 400
                draw_text(self.screen, f"Planet: {planet.name}", (x_offset, y_offset), self.font_medium, COLOR_SUCCESS)
                
                if planet.scanned:
                    draw_text(self.screen, f"Resources: {planet.resources}", (x_offset, y_offset + 30), self.font_small)
                    draw_text(self.screen, f"Deuterium: {planet.deuterium}", (x_offset, y_offset + 55), self.font_small)
                    
                    if planet.colonized:
                        draw_text(self.screen, f"Population: {planet.population:,}", (x_offset, y_offset + 80), self.font_small)
                        draw_text(self.screen, f"Mines: {planet.mining_stations}", (x_offset, y_offset + 105), self.font_small)
                        draw_text(self.screen, f"Defenses: {planet.defenses}", (x_offset, y_offset + 130), self.font_small)
                        
                        # Planet action buttons
                        btn_y = y_offset + 160
                        btn1 = Button(pygame.Rect(x_offset, btn_y, 110, 35), "Build Mine")
                        btn2 = Button(pygame.Rect(x_offset + 120, btn_y, 110, 35), "Build Defense")
                        btn1.draw(self.screen, self.font_small)
                        btn2.draw(self.screen, self.font_small)
                        self.buttons.append(btn1)
                        self.buttons.append(btn2)
                else:
                    draw_text(self.screen, "Not scanned", (x_offset, y_offset + 30), self.font_small, COLOR_TEXT_DIM)
        
        # Navigation buttons
        nav_y = panel_y + 10
        nav_buttons = [
            ("Galaxy Map", 10, SCREEN_HEIGHT - 50),
            ("Tech", 130, SCREEN_HEIGHT - 50),
            ("Ships", 230, SCREEN_HEIGHT - 50),
        ]
        
        for text, x, y in nav_buttons:
            btn = Button(pygame.Rect(x, y, 90, 35), text)
            btn.draw(self.screen, self.font_small)
            self.buttons.append(btn)
    
    def render_tech_view(self):
        """Render technology screen"""
        self.buttons = []
        
        self.screen.fill(COLOR_SPACE_BLUE)
        
        # Header
        draw_text(self.screen, "TECHNOLOGY", (20, 20), self.font_large, COLOR_UI_BORDER)
        draw_text(self.screen, f"Resources: {self.game.resources}", (20, 70), self.font_medium, COLOR_GOLD)
        
        # Technology list
        y_offset = 150
        for tech_type in TechType:
            level = getattr(self.game.tech, tech_type.name.lower())
            name = self.game.tech.get_name(tech_type)
            cost = self.game.tech.get_cost(tech_type)
            
            # Tech info
            draw_text(self.screen, f"{tech_type.value}: Level {level}", (20, y_offset), self.font_medium)
            draw_text(self.screen, name, (20, y_offset + 30), self.font_small, COLOR_TEXT_DIM)
            
            # Upgrade button
            btn = Button(pygame.Rect(500, y_offset, 250, 40), f"Upgrade ({cost} res)")
            if self.game.resources >= cost:
                btn.draw(self.screen, self.font_small)
                self.buttons.append(btn)
            else:
                # Disabled button
                pygame.draw.rect(self.screen, COLOR_UI_BG, btn.rect)
                pygame.draw.rect(self.screen, COLOR_TEXT_DIM, btn.rect, 2)
                text_surf = self.font_small.render(btn.text, True, COLOR_TEXT_DIM)
                self.screen.blit(text_surf, text_surf.get_rect(center=btn.rect.center))
            
            y_offset += 80
        
        # Back button
        btn = Button(pygame.Rect(20, SCREEN_HEIGHT - 70, 120, 50), "Back")
        btn.draw(self.screen, self.font_medium)
        self.buttons.append(btn)
    
    def render_ships_view(self):
        """Render ships list"""
        self.buttons = []
        
        self.screen.fill(COLOR_SPACE_BLUE)
        
        # Header
        draw_text(self.screen, "FLEET COMMAND", (20, 20), self.font_large, COLOR_UI_BORDER)
        draw_text(self.screen, f"Resources: {self.game.resources}", (20, 70), self.font_medium, COLOR_GOLD)
        draw_text(self.screen, f"Total Ships: {len(self.game.ships)}", (20, 100), self.font_small)
        
        # Ship list
        y_offset = 150
        for ship in list(self.game.ships.values())[:15]:  # Show first 15
            system_name = self.game.star_systems[ship.system].name
            
            # Ship info
            color = ship.get_color()
            pygame.draw.circle(self.screen, color, (30, y_offset + 15), 8)
            
            draw_text(self.screen, f"{ship.name} ({ship.ship_type.value})", (50, y_offset), self.font_small)
            draw_text(self.screen, f"Location: {system_name}", (50, y_offset + 20), self.font_small, COLOR_TEXT_DIM)
            draw_text(self.screen, f"HP: {ship.health}  Fuel: {ship.fuel}", (400, y_offset + 10), self.font_small)
            
            y_offset += 50
        
        # Build ships section
        build_y = SCREEN_HEIGHT - 400
        pygame.draw.rect(self.screen, COLOR_UI_BG, (0, build_y, SCREEN_WIDTH, 400))
        draw_text(self.screen, "BUILD SHIPS", (20, build_y + 10), self.font_medium, COLOR_UI_BORDER)
        
        # Build buttons
        button_y = build_y + 50
        ship_types_to_build = [
            (ShipType.SCOUT, 150),
            (ShipType.FIGHTER, 200),
            (ShipType.COLONY, 500),
            (ShipType.MINER, 300),
        ]
        
        for i, (ship_type, cost) in enumerate(ship_types_to_build):
            row = i // 2
            col = i % 2
            x = 20 + col * 380
            y = button_y + row * 60
            
            btn = Button(pygame.Rect(x, y, 360, 45), f"Build {ship_type.value} ({cost} res)")
            btn.draw(self.screen, self.font_small)
            self.buttons.append(btn)
        
        # Back button
        btn = Button(pygame.Rect(20, SCREEN_HEIGHT - 70, 120, 50), "Back")
        btn.draw(self.screen, self.font_medium)
        self.buttons.append(btn)
    
    def render_log_area(self, y: int, height: int):
        """Render log messages"""
        pygame.draw.rect(self.screen, COLOR_UI_BG, (0, y, SCREEN_WIDTH, height))
        pygame.draw.line(self.screen, COLOR_UI_BORDER, (0, y), (SCREEN_WIDTH, y), 2)
        
        draw_text(self.screen, "LOG", (10, y + 5), self.font_small, COLOR_UI_BORDER)
        
        # Show last few log entries
        log_y = y + 30
        for log_entry in self.game.log[-8:]:
            draw_text(self.screen, log_entry, (10, log_y), self.font_small, COLOR_TEXT_DIM)
            log_y += 20


# ==================== MAIN ====================

def main():
    """Main entry point"""
    game = SpaceFrontier()
    game.run()


if __name__ == "__main__":
    main()
