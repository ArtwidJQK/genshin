# P2 Character Gacha Engine Specification

## 1. Objective

This document defines the formal, implementation-ready specification for the **Character Event Wish Gacha Engine (P2)** in the Gacha & Artifact RNG Simulator.

The engine models the probabilistic behavior of Genshin Impact's limited character banners (Character Event Wish and Character Event Wish-2) with mathematical rigor, seed-reproducible determinism, explicit state tracking, and full compliance with both official HoYoverse rules (Version 5.0+) and verified community empirical models.

---

## 2. Scope

The P2 Character Gacha Engine encompasses the following 22 capabilities:

1. **5★ Base Probability**: Evaluation of the base 0.600% pull probability.
2. **5★ Consolidated Rate Metadata**: Modeling and reporting of the official 1.600% consolidated rate.
3. **5★ Hard Pity**: Strict enforcement of a 5★ drop on or before the 90th pull.
4. **Empirical Soft-Pity Curve**: Pluggable, configurable mathematical models for probability escalation prior to hard pity.
5. **5★ Promotional vs. Standard Outcome**: Resolution of on-banner promotional character vs. standard 5★ pool.
6. **50/50 State Tracking**: Tracking whether the current 5★ outcome is subject to the 50/50 rule or guaranteed.
7. **Featured 5★ Guarantee**: Guaranteed promotional character on the next 5★ pull following a 50/50 loss.
8. **Character Event Wish (Banner 1)**: Primary limited promotional character banner.
9. **Character Event Wish-2 (Banner 2)**: Secondary concurrent promotional character banner.
10. **Shared Pity / Guarantee State**: Atomic state sharing across concurrent Character Event Wishes.
11. **4★ Hard Pity & Base Rates**: Evaluation of 5.100% base rate, 13.000% consolidated rate, and 10-pull guarantee.
12. **4★ Featured Guarantee**: Guaranteed promotional 4★ character on the next 4★ drop following a non-featured 4★ outcome.
13. **Equal 4★ Selection**: Uniform $\frac{1}{3}$ selection probability among the 3 featured 4★ characters.
14. **Capturing Radiance Mechanism**: State machine modeling of the Version 5.0+ 50/50 bad-luck mitigation system.
15. **Capturing Radiance Streak Counter**: Tracking consecutive 50/50 losses and triggering guaranteed activation.
16. **Deterministic RNG Integration**: Routing all entropy exclusively through `RNGInterface` (`PythonRNG`).
17. **Seeded Reproducibility**: Exact state save/restore and replayability from an arbitrary random seed.
18. **Pull History Audit Trail**: Structured event logging capturing every pull with metadata.
19. **Single-Pull Contract**: Atomic execution of `single_pull()`.
20. **Batch-Pull Contract**: Multi-pull execution guaranteed equivalent to sequential single pulls.
21. **Simulation Compatibility**: Engine output schema tailored for downstream Monte Carlo analysis.
22. **Configuration-Driven Banners**: Dynamic loading of banner dates, pools, and rules via JSON configuration.

---

## 3. Non-Goals

The following features are explicitly out of scope for P2:

- **Weapon Event Wish**: Epitomized Path, 80-pull hard pity, and weapon banner mechanics.
- **Standard Wish (Wanderlust Invocation)**: Static standard banner pool without promotional guarantees.
- **Chronicled Wish**: Fate Point mechanic and mixed regional pools.
- **Novice Wishes (Beginners' Wish)**: 20% discount and fixed Noelle drop.
- **Database Persistence**: ORM mapping, SQL migrations, or PostgreSQL integration.
- **HTTP / Web API**: FastAPI endpoint controllers and route handlers.
- **Frontend Presentation**: Wish animations, splash art rendering, and UI components.
- **In-Game Currency Economy**: Primogem tracking, Intertwined Fate purchases, and Starglitter/Stardust shops.

---

## 4. Evidence Boundary

To preserve intellectual honesty, all gacha mechanics are categorized strictly according to the project's epistemological protocol:

| Category | Definition | Mechanics Included |
| :--- | :--- | :--- |
| **OFFICIAL FACT (Level A)** | Explicitly disclosed by HoYoverse in-game Wish Details or official version announcements. | - 5★ base rate: 0.600%<br>- 5★ consolidated rate: 1.600%<br>- 5★ hard pity: 90 pulls<br>- 4★ base rate: 5.100%<br>- 4★ consolidated rate: 13.000%<br>- 4★ hard pity: 10 pulls<br>- 50/50 rule on 5★ and 4★<br>- 100% guarantee after losing 50/50<br>- Shared pity & guarantee between Character Event Wish and Character Event Wish-2<br>- Capturing Radiance: base trigger rate 0.018%, consolidated promotional rate 55.000%, applies only during 50/50, guaranteed after 3 consecutive losses. |
| **EMPIRICAL MODEL (Level C)** | Derived from large-scale player submission data (e.g. Paimon.moe, community aggregations); unconfirmed by server source code. | - 5★ soft-pity onset starting at pull 74 with linear slope (+6.0% per pull).<br>- 4★ soft-pity onset starting at pull 9 (+51.0% jump).<br>- 4★ standard pool split (50% character / 50% weapon) when non-featured. |
| **SIMULATOR DESIGN CHOICE** | Software engineering architecture internal to this simulator. | - Decoupled `BaseRateModel`, `EmpiricalSoftPityModel`, and `HardPityRule`.<br>- Explicit `GachaState` dataclass.<br>- Sequential RNG decision order.<br>- Full `PullResult` audit payload. |

---

## 5. Domain Model

The domain entities are modeled as immutable dataclasses:

```python
from enum import Enum
from typing import Optional, List
from dataclasses import dataclass

class Rarity(int, Enum):
    THREE_STAR = 3
    FOUR_STAR = 4
    FIVE_STAR = 5

class ItemType(str, Enum):
    CHARACTER = "CHARACTER"
    WEAPON = "WEAPON"

class BannerType(str, Enum):
    CHARACTER_EVENT = "CHARACTER_EVENT"
    CHARACTER_EVENT_2 = "CHARACTER_EVENT_2"

@dataclass(frozen=True)
class WishItem:
    """Represents an item that can be pulled from a banner."""
    id: str
    name: str
    rarity: Rarity
    item_type: ItemType
    element: Optional[str] = None
    weapon_type: Optional[str] = None

@dataclass(frozen=True)
class PullResult:
    """Audit payload returned for each resolved pull."""
    pull_index: int                    # Lifetime global pull number
    banner_id: str                     # Identifier of banner pulled on
    item: WishItem                     # The awarded item entity
    rarity: Rarity                     # 3, 4, or 5
    is_featured: bool                  # True if item is a promotional rate-up unit
    pity_count_5star: int              # 5★ pity count at time of pull (1-90)
    pity_count_4star: int              # 4★ pity count at time of pull (1-10)
    won_50_50: Optional[bool]          # True if won 50/50, False if lost, None if guaranteed or 3★
    capturing_radiance_triggered: bool # True if won via Capturing Radiance
    capturing_radiance_streak: int     # Failure streak count prior to this pull
```

---

## 6. GachaState

The mutable state governing banner progress is encapsulated in `GachaState`:

```python
@dataclass
class GachaState:
    """Encapsulates the complete progression state for a banner family."""
    pity_5star: int = 0
    pity_4star: int = 0
    featured_5star_guaranteed: bool = False
    featured_4star_guaranteed: bool = False
    capturing_radiance_streak: int = 0  # Number of consecutive 50/50 losses (0, 1, 2, 3)
    lifetime_pulls: int = 0
    lifetime_5star_count: int = 0
    lifetime_4star_count: int = 0
    banner_family: str = "CHARACTER_EVENT"

    def validate_state(self) -> None:
        """Enforces all domain invariants on the state."""
        if not (0 <= self.pity_5star < 90):
            raise ValueError(f"5★ pity must be in [0, 89], got {self.pity_5star}")
        if not (0 <= self.pity_4star < 10):
            raise ValueError(f"4★ pity must be in [0, 9], got {self.pity_4star}")
        if not (0 <= self.capturing_radiance_streak <= 3):
            raise ValueError(f"Capturing Radiance streak must be in [0, 3], got {self.capturing_radiance_streak}")
        if not isinstance(self.featured_5star_guaranteed, bool):
            raise TypeError("featured_5star_guaranteed must be a boolean")
        if not isinstance(self.featured_4star_guaranteed, bool):
            raise TypeError("featured_4star_guaranteed must be a boolean")
```

---

## 7. State Machine

### State Transition Table

| Event / Outcome | `pity_5star` | `pity_4star` | `featured_5star_guaranteed` | `featured_4star_guaranteed` | `capturing_radiance_streak` |
|---|---|---|---|---|---|
| **Initial State** | `0` | `0` | `False` | `False` | `0` |
| **3★ Weapon** | `+1` | `+1` | Unchanged | Unchanged | Unchanged |
| **4★ Featured Character** | `+1` | `0` (Reset) | Unchanged | `False` (Reset) | Unchanged |
| **4★ Non-Featured Item** | `+1` | `0` (Reset) | Unchanged | `True` (Guaranteed) | Unchanged |
| **5★ Guaranteed Promotional** | `0` (Reset) | `0` (Reset) | `False` (Reset) | Unchanged | Unchanged (Bypasses CR) |
| **5★ Won 50/50 (Standard Win)**| `0` (Reset) | `0` (Reset) | `False` | Unchanged | `0` (Reset to 0) |
| **5★ Won via Capturing Radiance**| `0` (Reset) | `0` (Reset) | `False` | Unchanged | `0` (Reset to 0) |
| **5★ Lost 50/50 (Standard Drop)**| `0` (Reset) | `0` (Reset) | `True` (Guaranteed) | Unchanged | `+1` (Increments streak) |

### Key State Machine Invariants
1. **Pity Reset on 5★**: Obtaining a 5★ item resets both `pity_5star` and `pity_4star` to 0 (since in official rules, pulling a 5★ satisfies the 10-pull "4★ or above" guarantee).
2. **Pity Reset on 4★**: Obtaining a 4★ item resets `pity_4star` to 0, while `pity_5star` continues incrementing.
3. **Guaranteed Bypasses CR**: When `featured_5star_guaranteed == True`, the outcome is 100% promotional; Capturing Radiance is **not evaluated**, does not roll, and leaves `capturing_radiance_streak` untouched.
4. **Streak Cap at 3**: When `capturing_radiance_streak == 3`, the next 50/50 pull triggers Capturing Radiance with probability 1.0 (100% certainty), awarding the promotional character and resetting the streak to 0.

---

## 8. Pull Algorithm

The complete deterministic pull execution algorithm:

```
Algorithm ExecuteSinglePull(state, banner, prob_model, rng):
    1. Validate state invariants.
    2. Determine current pull ordinal:
         current_5star_pity = state.pity_5star + 1
         current_4star_pity = state.pity_4star + 1
         lifetime_pull = state.lifetime_pulls + 1

    3. Calculate 5★ probability:
         p5 = prob_model.get_5star_probability(current_5star_pity)

    4. Roll for 5★:
         roll_val = rng.random_float(0.0, 1.0)
         if roll_val < p5:
             # Resolve 5★ Drop
             if state.featured_5star_guaranteed:
                 item = banner.featured_5star
                 is_featured = True
                 won_50_50 = None
                 cr_triggered = False
                 state.featured_5star_guaranteed = False
             else:
                 # Evaluate Capturing Radiance
                 if state.capturing_radiance_streak >= 3:
                     cr_triggered = True
                 else:
                     cr_roll = rng.random_float(0.0, 1.0)
                     cr_triggered = (cr_roll < banner.capturing_radiance_base_rate)

                 if cr_triggered:
                     item = banner.featured_5star
                     is_featured = True
                     won_50_50 = True
                     state.capturing_radiance_streak = 0
                     state.featured_5star_guaranteed = False
                 else:
                     # Standard 50/50 Roll
                     fifty_roll = rng.random_float(0.0, 1.0)
                     if fifty_roll < 0.50:
                         item = banner.featured_5star
                         is_featured = True
                         won_50_50 = True
                         state.capturing_radiance_streak = 0
                         state.featured_5star_guaranteed = False
                     else:
                         item = SelectRandomStandard5Star(banner.standard_5star_pool, rng)
                         is_featured = False
                         won_50_50 = False
                         state.capturing_radiance_streak += 1
                         state.featured_5star_guaranteed = True

             # Update 5★ State
             state.pity_5star = 0
             state.pity_4star = 0
             state.lifetime_5star_count += 1
             state.lifetime_pulls += 1
             return BuildPullResult(...)

    5. Calculate 4★ probability:
         p4 = prob_model.get_4star_probability(current_4star_pity)

    6. Roll for 4★:
         roll_val = rng.random_float(0.0, 1.0)
         if roll_val < p4:
             # Resolve 4★ Drop
             if state.featured_4star_guaranteed:
                 item = SelectRandomFeatured4Star(banner.featured_4star_pool, rng)
                 is_featured = True
                 state.featured_4star_guaranteed = False
             else:
                 fifty_roll = rng.random_float(0.0, 1.0)
                 if fifty_roll < 0.50:
                     item = SelectRandomFeatured4Star(banner.featured_4star_pool, rng)
                     is_featured = True
                     state.featured_4star_guaranteed = False
                 else:
                     item = SelectRandomStandard4Star(banner.standard_4star_pool, rng)
                     is_featured = False
                     state.featured_4star_guaranteed = True

             # Update 4★ State
             state.pity_5star += 1
             state.pity_4star = 0
             state.lifetime_4star_count += 1
             state.lifetime_pulls += 1
             return BuildPullResult(...)

    7. Resolve 3★ Drop:
         item = SelectRandom3Star(banner.three_star_pool, rng)
         state.pity_5star += 1
         state.pity_4star += 1
         state.lifetime_pulls += 1
         return BuildPullResult(...)
```

---

## 9. RNG Chronology

Every pull consumes entropy in a strict, predictable sequence to preserve seed replayability:

```
[Pull Starts]
       ↓
[Step 1: 5★ Rarity Roll] ---- (Draw 1: random_float)
       ↓
   Is it 5★?
   ├── YES ──> [Step 2A: Guaranteed 5★?]
   │                 ├── YES ──> Award featured 5★ (0 extra draws)
   │                 └── NO ───> [Step 2B: CR Streak >= 3?]
   │                                   ├── YES ──> Award featured 5★ (CR guaranteed, 0 extra draws)
   │                                   └── NO ───> [Step 2C: CR Base Rate Roll] ---- (Draw 2: random_float)
   │                                                     ├── Triggered ──> Award featured 5★
   │                                                     └── Not Triggered ──> [Step 2D: Standard 50/50 Roll] ---- (Draw 3: random_float)
   │                                                                               ├── Won ──> Award featured 5★
   │                                                                               └── Lost ──> Select standard 5★ ---- (Draw 4: choice)
   │
   └── NO ───> [Step 3: 4★ Rarity Roll] ---- (Draw 2: random_float)
                     │
                 Is it 4★?
                 ├── YES ──> [Step 4A: Guaranteed 4★?]
                 │                 ├── YES ──> Select 1 of 3 featured 4★ ---- (Draw 3: choice)
                 │                 └── NO ───> [Step 4B: 4★ 50/50 Roll] ---- (Draw 3: random_float)
                 │                                   ├── Won ──> Select 1 of 3 featured 4★ ---- (Draw 4: choice)
                 │                                   └── Lost ──> Select standard 4★ ---- (Draw 4: choice)
                 │
                 └── NO ───> [Step 5: 3★ Weapon Roll] ---- (Draw 3: choice)
```

**Rule**: No speculative or discarded RNG calls are permitted. If an outcome is guaranteed by pity or prior loss, the corresponding probability roll is bypassed.

---

## 10. Probability Model Abstraction

The probability calculation is decoupled from the state machine through an interface:

```python
from abc import ABC, abstractmethod

class GachaProbabilityModel(ABC):
    """Abstract interface defining pull probability curves."""

    @abstractmethod
    def get_5star_probability(self, pity_count: int) -> float:
        """Return 5★ probability for the given pity count (1 to 90)."""
        pass

    @abstractmethod
    def get_4star_probability(self, pity_count: int) -> float:
        """Return 4★ probability for the given pity count (1 to 10)."""
        pass
```

Implementations:
1. `ConstantRateModel`: Flat 0.6% and 5.1% rates with hard pity caps (for baseline unit testing).
2. `StandardEmpiricalPityModel`: The default community-accepted soft-pity model.
3. `CustomCurveModel`: Configurable piecewise linear or polynomial curve for research experiments.

---

## 11. Soft-Pity Model

### Default Empirical Model (`StandardEmpiricalPityModel`)
*Epistemological Status*: **EMPIRICAL COMMUNITY MODEL (Level C)**.

#### 5★ Curve Formulation:
$$P_5(\text{pity}) = \begin{cases} 
0.006 & \text{if } 1 \le \text{pity} \le 73 \\ 
0.006 + (\text{pity} - 73) \times 0.06 & \text{if } 74 \le \text{pity} \le 89 \\ 
1.000 & \text{if } \text{pity} = 90 
\end{cases}$$

- Pulls 1–73: Flat base rate of $0.6\%$.
- Pull 74: $6.6\%$
- Pull 75: $12.6\%$
- Pull 80: $42.6\%$
- Pull 85: $72.6\%$
- Pull 89: $96.6\%$
- Pull 90: $100.0\%$ (Official Hard Pity, Level A).

#### 4★ Curve Formulation:
$$P_4(\text{pity}) = \begin{cases} 
0.051 & \text{if } 1 \le \text{pity} \le 8 \\ 
0.561 & \text{if } \text{pity} = 9 \\ 
1.000 & \text{if } \text{pity} = 10 
\end{cases}$$

- Pulls 1–8: Flat base rate of $5.1\%$.
- Pull 9: Jump to $56.1\%$ (empirical ramp).
- Pull 10: $100.0\%$ (Official Hard Pity, Level A).

---

## 12. 5★ Rules

1. **Base Rate**: $0.006$ ($0.6\%$).
2. **Consolidated Rate**: $0.016$ ($1.6\%$) metadata property.
3. **Hard Pity**: Reaching pull 90 guarantees a 5★ item.
4. **Pool Structure**:
   - Exactly 1 featured promotional 5★ character.
   - Standard 5★ character pool: `["Jean", "Diluc", "Qiqi", "Mona", "Keqing", "Tighnari", "Dehya"]`.
5. **Deduplication**: Standard 5★ characters are drawn uniformly from the 7 standard units.

---

## 13. 4★ Rules

1. **Base Rate**: $0.051$ ($5.1\%$).
2. **Consolidated Rate**: $0.130$ ($13.0\%$) metadata property.
3. **Hard Pity**: Reaching pull 10 guarantees a 4★ or higher item.
4. **Pool Structure**:
   - Exactly 3 featured promotional 4★ characters.
   - Standard 4★ pool consisting of characters and weapons.
5. **Featured Selection**: When a featured 4★ is awarded, each of the 3 featured units has an exact $\frac{1}{3}$ ($33.\overline{3}\%$) selection probability.

---

## 14. 50/50 + Guarantee

1. **5★ Guarantee Rule**:
   - If an awarded 5★ is from the standard pool, `featured_5star_guaranteed` is set to `True`.
   - On the next 5★ pull, the promotional character is awarded with $100\%$ certainty.
   - Upon winning a promotional character (via guarantee, 50/50, or Capturing Radiance), `featured_5star_guaranteed` is reset to `False`.
2. **4★ Guarantee Rule**:
   - If an awarded 4★ is non-featured, `featured_4star_guaranteed` is set to `True`.
   - On the next 4★ pull, one of the 3 featured 4★ characters is guaranteed.
   - Upon winning a featured 4★, `featured_4star_guaranteed` is reset to `False`.

---

## 15. Capturing Radiance

### Specifications (Version 5.0+)
1. **Applicability**: Applies **exclusively** during non-guaranteed 5★ pulls (`featured_5star_guaranteed == False`).
2. **Base Trigger Rate**: $0.018\%$ ($0.00018$).
3. **Consolidated Promotional Rate**: $55.000\%$ (overall effective rate of obtaining promotional 5★ on applicable pulls).
4. **Streak Threshold & Guarantee**:
   - `capturing_radiance_streak` counts consecutive 50/50 losses.
   - Initial value: `0`.
   - Increments by `+1` whenever a 5★ 50/50 is lost.
   - If `capturing_radiance_streak == 3`, Capturing Radiance is **guaranteed** to trigger on the next applicable 5★ pull ($P_{\text{CR}} = 1.0$).
5. **Reset Condition**:
   - When Capturing Radiance triggers, the promotional character is awarded, and `capturing_radiance_streak` resets to `0`.
   - When a standard 50/50 is won without Capturing Radiance, `capturing_radiance_streak` resets to `0`.
6. **Non-Interference with Guarantees**:
   - Capturing Radiance never applies when `featured_5star_guaranteed == True`.
   - It does not consume or alter an active promotional guarantee.

---

## 16. Banner Carry-Over

1. **Concurrent Banner Sharing**:
   - Character Event Wish (Banner 1) and Character Event Wish-2 (Banner 2) point to the exact same mutable `GachaState` reference.
   - Pulling on Banner 1 updates the state identically for subsequent pulls on Banner 2.
2. **Banner Rotation Persistence**:
   - When a banner phase ends and a new character banner begins, all state attributes (`pity_5star`, `pity_4star`, `featured_5star_guaranteed`, `featured_4star_guaranteed`, `capturing_radiance_streak`) remain strictly intact.
   - Only the banner configuration (`featured_5star`, `featured_4star_pool`) updates.

---

## 17. Configuration Schema

Configuration is serialized in `config/gacha/`:

### 17.1 `config/gacha/rules.json`
```json
{
  "ruleset_version": "5.0",
  "five_star": {
    "base_rate": 0.006,
    "consolidated_rate": 0.016,
    "hard_pity": 90
  },
  "four_star": {
    "base_rate": 0.051,
    "consolidated_rate": 0.130,
    "hard_pity": 10
  },
  "capturing_radiance": {
    "base_rate": 0.00018,
    "consolidated_promotional_rate": 0.55,
    "guaranteed_streak_threshold": 3
  }
}
```

### 17.2 `config/gacha/banners.json`
```json
[
  {
    "banner_id": "character_event_5_0_p1_kinich",
    "name": "Flame-Turned Steps",
    "banner_type": "CHARACTER_EVENT",
    "version": "5.0",
    "featured_5star_id": "kinich",
    "featured_4star_ids": ["chevreuse", "sara", "thoma"]
  },
  {
    "banner_id": "character_event_5_0_p1_raiden",
    "name": "Reign of Serenity",
    "banner_type": "CHARACTER_EVENT_2",
    "version": "5.0",
    "featured_5star_id": "raiden_shogun",
    "featured_4star_ids": ["chevreuse", "sara", "thoma"]
  }
]
```

### 17.3 `config/gacha/pools.json`
Contains complete registries of standard 5★ characters, standard 4★ characters, standard 4★ weapons, and 3★ weapons.

---

## 18. Invariants

The engine enforces the following non-negotiable invariants:

1. **Pity Bound Invariants**:
   - $0 \le \text{pity\_5star} < 90$
   - $0 \le \text{pity\_4star} < 10$
2. **Hard Pity Invariants**:
   - A pull initiated at $\text{pity\_5star} = 89$ MUST yield a 5★ item.
   - A pull initiated at $\text{pity\_4star} = 9$ MUST yield a 4★ or 5★ item.
3. **Streak Invariant**:
   - $0 \le \text{capturing\_radiance\_streak} \le 3$.
   - A 50/50 pull initiated at $\text{capturing\_radiance\_streak} = 3$ MUST trigger Capturing Radiance.
4. **Guarantee Invariant**:
   - When $\text{featured\_5star\_guaranteed} == \text{True}$, an awarded 5★ item MUST be the promotional character.
   - When $\text{featured\_4star\_guaranteed} == \text{True}$, an awarded 4★ item MUST be one of the 3 featured 4★ characters.
5. **State Conservation**:
   - `lifetime_pulls` equals the sum of all resolved pull events.

---

## 19. Error & Invalid-State Behavior

- **Corrupted State Rejection**: If `GachaState` is initialized or restored with negative pity, pity $\ge \text{hard\_pity}$, or streak $> 3$, `validate_state()` raises `ValueError`.
- **Invalid Banner Selection**: Attempting to pull on an unconfigured or unregistered banner raises `KeyError` or `ValueError`.
- **Corrupted Configuration**: Missing featured characters or pool sizes $< 3$ in configuration raises `ValueError` at load time.
- **Fail Fast**: The engine never silently repairs or normalizes corrupted state.

---

## 20. Single-Pull Contract

```python
def single_pull(self, banner_id: str) -> PullResult:
    """Executes a single wish transaction on the specified banner.
    
    Guarantees:
    - Exactly one item is awarded.
    - Pity counters and guarantees are updated atomically.
    - RNG stream advances deterministically.
    - Full audit payload (PullResult) is returned.
    """
```

---

## 21. Batch-Pull Contract

```python
def pull(self, banner_id: str, count: int) -> List[PullResult]:
    """Executes a batch of `count` consecutive wishes on the specified banner.
    
    Guarantees:
    - Strict mathematical equivalence: identical to executing `single_pull()` `count` times in a loop.
    - No bulk probability shortcut or separate statistical algorithm is permitted.
    - Invariants are preserved after every individual pull within the batch.
    """
```

---

## 22. Simulation Contract

The engine returns `PullResult` objects containing all metadata needed for downstream Monte Carlo analysis:
- Pull index and banner identity
- Item rarity, identity, and promotional status
- Exact 5★ and 4★ pity counts at the moment of draw
- 50/50 outcome (`won_50_50`: True, False, None)
- Capturing Radiance trigger indicator and historical streak counter

This allows simulation modules to compute arbitrary analytics (mean pulls to C6, median pity, standard deviation, Capturing Radiance empirical activation rate, worst-case scenarios) without modifying the core engine.

---

## 23. API Boundary

```
[Presentation / Frontend]
          ↓ HTTP JSON
[API Transport Layer (app/api/v1/gacha.py)]
          ↓ Dependency Injection
[Gacha Engine (app/core/gacha/engine.py)]
          ↓
[State Management (GachaState)]  &  [Probability Engine (app/core/probability)]
                                                  ↓
                                     [RNG Interface (app/core/rng)]
```

- API routes receive `{ "banner_id": str, "count": int }`, validate request syntax, delegate to `GachaEngine`, and serialize `List[PullResult]`.
- API controllers contain **zero** business logic, pity calculations, or RNG calls.

---

## 24. Frontend Boundary

The frontend MUST NOT implement:
- Pity counters or roll increments
- 50/50 evaluation or guarantee tracking
- Capturing Radiance logic or streak counting
- RNG generation or character selection
- Soft-pity curve calculations

The frontend is strictly a presentation layer rendering server-returned pull results and audit history.

---

## 25. Deterministic Test Vectors

The test suite must implement the following deterministic seeded scenarios:

1. **5★ Hard Pity**:
   - Mock probability model returning $P_5 = 0.0$ for pulls 1–89 and $P_5 = 1.0$ at pull 90.
   - Assert: Pulls 1–89 yield non-5★; pull 90 yields 5★ with `pity_count_5star == 90`.
2. **4★ Hard Pity**:
   - Mock probability model returning $P_4 = 0.0$ for pulls 1–9 and $P_4 = 1.0$ at pull 10.
   - Assert: Pull 10 yields 4★+ with `pity_count_4star == 10`.
3. **50/50 Loss and Guarantee**:
   - Force 5★ drop with 50/50 loss ($r \ge 0.5$, CR not triggered).
   - Assert: Standard 5★ awarded, `featured_5star_guaranteed == True`, `capturing_radiance_streak == 1`.
   - Next 5★ drop: Assert promotional character awarded, `featured_5star_guaranteed == False`.
4. **Capturing Radiance Streak Guarantee**:
   - Force 3 consecutive 50/50 losses (interspersed with guaranteed pulls).
   - Assert: `capturing_radiance_streak == 3`.
   - Next 50/50 pull: Assert Capturing Radiance triggers ($P_{\text{CR}} = 1.0$), promotional character awarded, `capturing_radiance_streak == 0`.
5. **Capturing Radiance Base Rate Trigger**:
   - Seeded pull where CR roll $< 0.00018$ on 50/50.
   - Assert: Promotional character awarded with `capturing_radiance_triggered == True`, streak reset to 0.
6. **Concurrent Banner Carry-Over**:
   - Execute 50 pulls on Banner 1 (`pity_5star == 50`).
   - Execute 1 pull on Banner 2.
   - Assert: Pull on Banner 2 is evaluated at `pity_count_5star == 51`; `state.pity_5star == 51`.
7. **Batch Equivalence**:
   - Seed engine with seed $S$, execute `pull(banner_id, 10)`.
   - Re-seed independent engine with seed $S$, execute `single_pull(banner_id)` 10 times.
   - Assert: Item identities, pity counts, and guarantee states match 100% item-for-item.

---

## 26. Statistical Test Strategy

Large-sample Monte Carlo verification ($N \ge 100{,}000$ pulls):

1. **5★ Consolidated Rate**:
   - Run $N = 200{,}000$ pulls under `StandardEmpiricalPityModel`.
   - Assert total 5★ items divided by $N$ converges to $1.600\% \pm 0.100\%$.
2. **4★ Consolidated Rate**:
   - Assert total 4★ items divided by $N$ converges to $13.000\% \pm 0.500\%$.
3. **Consolidated Promotional 5★ Rate (Capturing Radiance)**:
   - On all non-guaranteed 5★ drops, assert promotional character share converges to approximately $55.0\% \pm 1.0\%$.

---

## 27. Regression Strategy

- All existing 93 automated unit tests in `tests/test_artifact.py`, `tests/test_probability.py`, `tests/test_rng.py`, and `tests/test_api.py` must remain 100% passing.
- Gacha engine tests must reside in a dedicated test module (`tests/test_gacha_engine.py`) without modifying existing test fixtures.

---

## 28. Acceptance Criteria

P2 implementation will be approved for sign-off only if:

- [ ] All 22 scope items are implemented in domain and engine code.
- [ ] No hardcoded character names or drop weights exist in engine logic.
- [ ] Capturing Radiance is modeled as an explicit state machine with failure streak tracking.
- [ ] Empirical soft-pity model is decoupled from hard pity and rate calculation.
- [ ] State validation rejects corrupted inputs and invalid pity counts.
- [ ] Character Event Wish and Character Event Wish-2 share identical atomic state.
- [ ] Batch execution is mathematically identical to sequential single pulls.
- [ ] All deterministic test vectors pass.
- [ ] Monte Carlo test confirms consolidated rate convergence.
- [ ] Zero production changes to Artifact Engine or core RNG abstractions.

---

## 29. Known Research Limitations

1. **Proprietary Server PRNG**: HoYoverse's exact server-side random number generator and floating-point comparison sequence are proprietary and unobservable.
2. **Soft-Pity Formula**: The linear $+6\%$ escalation from pull 74 to 89 is an empirical community model (Level C) that matches observed drop frequencies, but is not an officially published formula.
3. **4★ Non-Featured Weapon vs. Character Split**: The exact ratio between 4★ weapons and 4★ standard characters on character banners is modeled as 50/50 per community consensus.

---

## 30. Implementation Order

When implementation commences in subsequent prompts, work will proceed in the following strict order:

1. **Step 1: Domain Models & State (`app/core/gacha/models.py`)**
   - Enums: `Rarity`, `ItemType`, `BannerType`.
   - Dataclasses: `WishItem`, `PullResult`, `GachaState` with `validate_state()`.
2. **Step 2: Configuration Schemas & Loader (`app/core/gacha/config.py`)**
   - Dataclasses: `GachaBannerConfig`, `GachaRulesConfig`.
   - JSON data files in `config/gacha/` (`rules.json`, `banners.json`, `pools.json`).
3. **Step 3: Probability Models (`app/core/gacha/probability_model.py`)**
   - `GachaProbabilityModel` interface.
   - `ConstantRateModel`, `StandardEmpiricalPityModel`.
4. **Step 4: Gacha Engine (`app/core/gacha/engine.py`)**
   - Core `GachaEngine` class.
   - Methods: `single_pull()`, `pull()`, `save_state()`, `restore_state()`.
   - Full Capturing Radiance and 50/50 state transitions.
5. **Step 5: Automated Unit & Deterministic Tests (`tests/test_gacha_engine.py`)**
   - Implementation of all deterministic test vectors and boundary checks.
6. **Step 6: Statistical Verification & Sign-Off**
   - Monte Carlo convergence verification.
