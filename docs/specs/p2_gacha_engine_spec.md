# P2 Character Gacha Engine Specification

## 1. Objective

This document defines the formal, implementation-ready specification for the **Character Event Wish Gacha Engine (P2)** in the Gacha & Artifact RNG Simulator.

The engine models the probabilistic behavior of Genshin Impact's limited character banners (Character Event Wish and Character Event Wish-2) with mathematical rigor, seed-reproducible determinism, explicit state tracking, and clear epistemological boundaries distinguishing official rules (Version 5.0+), empirical community models, and simulator design choices.

---

## 2. Scope

The P2 Character Gacha Engine encompasses the following 22 capabilities:

1. **5★ Base Probability**: Evaluation of the base 0.600% pull probability.
2. **5★ Consolidated Rate Metadata**: Modeling and reporting of the official 1.600% consolidated rate.
3. **5★ Hard Pity**: Strict enforcement of a 5★ drop on or before the 90th pull.
4. **Pluggable Soft-Pity Curves**: Decoupled `RarityProbabilityModel` interface supporting baseline constant rate and empirical soft-pity curves.
5. **5★ Promotional vs. Standard Outcome**: Resolution of on-banner promotional character vs. standard 5★ pool via `FiveStarOutcomeModel`.
6. **50/50 State Tracking**: Tracking whether the current 5★ outcome is subject to the 50/50 rule or guaranteed.
7. **Featured 5★ Guarantee**: Guaranteed promotional character on the next 5★ pull following a 50/50 loss.
8. **Character Event Wish (Banner 1)**: Primary limited promotional character banner.
9. **Character Event Wish-2 (Banner 2)**: Secondary concurrent promotional character banner.
10. **Shared Pity / Guarantee State**: Atomic state sharing across concurrent Character Event Wishes.
11. **4★ Hard Pity & Base Rates**: Evaluation of 5.100% base rate, 13.000% consolidated rate, and 10-pull guarantee.
12. **Independent 4★ Pity Tracking**: Tracking `pity_4star` independently from `pity_5star` (5★ drops do not reset 4★ pity).
13. **4★ Featured Guarantee**: Guaranteed promotional 4★ character on the next 4★ drop following a non-featured 4★ outcome.
14. **Equal 4★ Selection**: Uniform $\frac{1}{3}$ selection probability among the 3 featured 4★ characters.
15. **Capturing Radiance Pluggable Abstraction**: State machine modeling of the Version 5.0+ bad-luck mitigation system via `CapturingRadianceModel`.
16. **Capturing Radiance Streak Counter**: Tracking consecutive 50/50 losses and enforcing guaranteed activation upon reaching the streak threshold.
17. **Deterministic RNG Integration**: Routing all entropy exclusively through `RNGInterface` (`PythonRNG`).
18. **Seeded Reproducibility**: Exact state save/restore and replayability from an arbitrary random seed.
19. **Pull History Audit Trail**: Structured event logging capturing every pull with metadata.
20. **Single-Pull Contract**: Atomic execution of `single_pull()`.
21. **Batch-Pull Contract**: Multi-pull execution guaranteed equivalent to sequential single pulls.
22. **Simulation Compatibility**: Engine output schema tailored for downstream Monte Carlo analysis.

---

## 3. Non-Goals

The following features are explicitly out of scope for P2:

- **Weapon Event Wish**: Epitomized Path, 80-pull hard pity, and weapon banner mechanics.
- **Standard Wish (Wanderlust Invocation)**: Static standard banner pool without promotional guarantees.
- **Chronicled Wish**: Fate Point mechanic and mixed regional pools.
- **Novice Wishes (Beginners' Wish)**: 20% discount and fixed Noelle drop.
- **Database Persistence**: ORM mapping, SQL migrations, or PostgreSQL integration.
- **HTTP / Web API Implementation**: FastAPI endpoint controllers and route handlers (interface contracts specified only).
- **Frontend Presentation**: Wish animations, splash art rendering, and UI components.
- **In-Game Currency Economy**: Primogem tracking, Intertwined Fate purchases, and Starglitter/Stardust shops.

---

## 4. Evidence Boundary

To preserve intellectual honesty, all gacha mechanics are categorized strictly according to the project's epistemological protocol:

| Category | Definition | Mechanics Included |
| :--- | :--- | :--- |
| **OFFICIAL FACT (Level A)** | Explicitly disclosed by HoYoverse in-game Wish Details or official announcements. | - 5★ base rate: 0.600%<br>- 5★ consolidated rate: 1.600%<br>- 5★ hard pity: 90 pulls<br>- 4★ base rate: 5.100%<br>- 4★ consolidated rate: 13.000%<br>- 4★ hard pity: "4★ or higher item guaranteed at least once per 10 attempts"<br>- 50/50 rule on 5★ and 4★<br>- 100% guarantee after losing 50/50<br>- Shared pity & guarantee between Character Event Wish and Character Event Wish-2<br>- Capturing Radiance published parameters: base trigger rate 0.018%, consolidated promotional rate 55.000%, applies only during 50/50, guaranteed after 3 consecutive occasions where promotional 5★ is the second 5★ obtained. |
| **EMPIRICAL MODEL — NOT OFFICIAL (Level C)** | Derived from large-scale player submission data (e.g. Paimon.moe, community aggregations); unconfirmed by server source code. | - 5★ soft-pity onset starting at pull 74 with linear slope (+6.0% per pull through 89).<br>- 4★ soft-pity onset starting at pull 9 (+51.0% jump to 56.1%).<br>- 4★ standard pool split (50% character / 50% weapon) when non-featured.<br>- Capturing Radiance empirical distribution models attempting to reconcile the published 0.018% base rate and 55% consolidated rate. |
| **SIMULATOR DESIGN CHOICE** | Software engineering architecture internal to this simulator. | - Decoupled `RarityProbabilityModel`, `FiveStarOutcomeModel`, `FourStarOutcomeModel`, and `CapturingRadianceModel`.<br>- Independent 4★ and 5★ pity counters (5★ pulls do NOT reset 4★ pity).<br>- Configurable `PityCollisionPolicy` when 5★ is drawn at 4★ pity = 9.<br>- Explicit `GachaState` and `PullResult` schemas.<br>- Sequential RNG decision order. |

---

## 5. Domain Model

The domain entities are modeled as immutable dataclasses and enums:

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

class PityCollisionPolicy(str, Enum):
    """Governs 4★ pity progression when a 5★ item is rolled at 4★ pity = 9."""
    DEFER_AT_CAP = "DEFER_AT_CAP"          # Preserve pity_4star at 9; next non-5★ is guaranteed 4★
    ALLOW_OVERFLOW = "ALLOW_OVERFLOW"      # Increment pity_4star to 10; next non-5★ is guaranteed 4★

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
    pull_index: int                         # Lifetime global pull number
    banner_id: str                          # Identifier of banner pulled on
    item: WishItem                          # The awarded item entity
    rarity: Rarity                          # 3, 4, or 5
    is_featured: bool                       # True if item is a promotional rate-up unit
    pity_count_5star: int                   # 5★ pity count at time of pull (1-90)
    pity_count_4star: int                   # 4★ pity count at time of pull (1-10+)
    won_50_50: Optional[bool]               # True if won 50/50, False if lost, None if guaranteed or 3★
    capturing_radiance_triggered: bool      # True if won via Capturing Radiance
    capturing_radiance_streak: int          # Failure streak count prior to this pull
    capturing_radiance_model_id: Optional[str] = None  # Model identifier evaluating CR
```

---

## 6. GachaState & Pity Independence

The mutable state governing banner progress is encapsulated in `GachaState`.

### Pity Counter Independence
In official Wish rules, "a 4★ or higher item is guaranteed at least once every 10 attempts." Obtaining a 5★ item satisfies the "4★ or higher" guarantee clause for that specific pull. However, community analysis and wish history tracking establish that **pulling a 5★ does not reset 4★ pity progress to 0**. 

Therefore:
- `pity_5star` and `pity_4star` are modeled as **strictly independent state variables**.
- An awarded 5★ item resets `pity_5star = 0`, but does **NOT** reset `pity_4star`.
- An awarded 4★ item resets `pity_4star = 0`, but does **NOT** reset `pity_5star`.
- An awarded 3★ item increments both counters.

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

    def validate_state(self, max_pity_4star: int = 10) -> None:
        """Enforces all domain invariants on the state."""
        if not (0 <= self.pity_5star < 90):
            raise ValueError(f"5★ pity must be in [0, 89], got {self.pity_5star}")
        if not (0 <= self.pity_4star <= max_pity_4star):
            raise ValueError(f"4★ pity must be in [0, {max_pity_4star}], got {self.pity_4star}")
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
| **5★ Guaranteed Promotional** | `0` (Reset) | Handled per Policy | `False` (Reset) | Unchanged | Unchanged (Bypasses CR) |
| **5★ Won 50/50 (Standard Win)**| `0` (Reset) | Handled per Policy | `False` | Unchanged | `0` (Reset to 0) |
| **5★ Won via Capturing Radiance**| `0` (Reset) | Handled per Policy | `False` | Unchanged | `0` (Reset to 0) |
| **5★ Lost 50/50 (Standard Drop)**| `0` (Reset) | Handled per Policy | `True` (Guaranteed) | Unchanged | `+1` (Increments streak) |

### Key State Machine Invariants
1. **Independent Pity Counters**: Obtaining a 5★ resets `pity_5star = 0`, but does not reset `pity_4star`. Obtaining a 4★ resets `pity_4star = 0`, but does not reset `pity_5star`.
2. **Guaranteed 5★ Bypasses CR**: When `featured_5star_guaranteed == True`, the outcome is 100% promotional; Capturing Radiance is **not evaluated**, does not roll, does not alter guarantees, and leaves `capturing_radiance_streak` untouched.
3. **Streak Cap at 3**: When `capturing_radiance_streak == 3`, the next 50/50 pull triggers Capturing Radiance with certainty ($P_{\text{CR}} = 1.0$), awarding the promotional character and resetting the streak to 0.
4. **Collision Handling (`SIMULATOR DESIGN CHOICE`)**:
   - The exact server collision behavior when a 5★ item is pulled at `pity_4star == 9` (the 10th pull) is not explicitly published by HoYoverse.
   - Because the 5★ satisfies the official "4★ or higher item at least once per 10 attempts" rule, resetting 4★ pity would destroy player pity equity.
   - The simulator isolates this resolution behind `PityCollisionPolicy`:
     - **`DEFER_AT_CAP` (Default Simulator Choice)**: `pity_4star` remains at 9. On the immediate next non-5★ pull, 4★ hard pity ($P_4 = 1.0$) is triggered.
     - **`ALLOW_OVERFLOW`**: `pity_4star` increments to 10. Any subsequent pull with `pity_4star >= 9` triggers 4★ hard pity ($P_4 = 1.0$) until a 4★ item drops.
   - Under no policy does a 5★ pull reset `pity_4star` to 0.

---

## 8. Pull Algorithm

The complete deterministic pull execution algorithm:

```
Algorithm ExecuteSinglePull(state, banner, rarity_model, outcome_5star_model, outcome_4star_model, cr_model, collision_policy, rng):
    1. Validate state invariants.
    2. Determine current pull ordinals:
         current_5star_pity = state.pity_5star + 1
         current_4star_pity = state.pity_4star + 1
         lifetime_pull = state.lifetime_pulls + 1

    3. Calculate 5★ probability:
         p5 = rarity_model.get_5star_probability(current_5star_pity)

    4. Roll for 5★:
         roll_val = rng.random_float(0.0, 1.0)
         if roll_val < p5:
             # Resolve 5★ Outcome via FiveStarOutcomeModel & CapturingRadianceModel
             outcome = outcome_5star_model.resolve_5star(state, banner, cr_model, rng)
             
             # Apply State Transitions
             state.pity_5star = 0
             if current_4star_pity >= 10:
                 if collision_policy == PityCollisionPolicy.DEFER_AT_CAP:
                     state.pity_4star = 9
                 else:
                     state.pity_4star = state.pity_4star + 1
             else:
                 state.pity_4star += 1

             if outcome.is_featured:
                 state.featured_5star_guaranteed = False
                 if outcome.was_50_50:
                     state.capturing_radiance_streak = 0
             else:
                 state.featured_5star_guaranteed = True
                 state.capturing_radiance_streak += 1

             state.lifetime_5star_count += 1
             state.lifetime_pulls += 1
             return BuildPullResult(outcome, ...)

    5. Calculate 4★ probability:
         p4 = rarity_model.get_4star_probability(current_4star_pity)

    6. Roll for 4★:
         roll_val = rng.random_float(0.0, 1.0)
         if roll_val < p4:
             # Resolve 4★ Outcome via FourStarOutcomeModel
             outcome = outcome_4star_model.resolve_4star(state, banner, rng)
             
             # Apply State Transitions
             state.pity_5star += 1
             state.pity_4star = 0
             if outcome.is_featured:
                 state.featured_4star_guaranteed = False
             else:
                 state.featured_4star_guaranteed = True

             state.lifetime_4star_count += 1
             state.lifetime_pulls += 1
             return BuildPullResult(outcome, ...)

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
   ├── YES ──> [Step 2: Resolve 5★ Outcome]
   │                 ├── Guaranteed? ──> Award featured 5★ (0 extra draws)
   │                 └── 50/50 Active? ──> [CapturingRadianceModel.resolve()]
   │                                             ├── CR Triggered ──> Award featured 5★ (Draws determined by CR model)
   │                                             └── CR Not Triggered ──> [Standard 50/50 Roll] ---- (Draw: random_float)
   │                                                                           ├── Won ──> Award featured 5★
   │                                                                           └── Lost ──> Select standard 5★ ---- (Draw: choice)
   │
   └── NO ───> [Step 3: 4★ Rarity Roll] ---- (Draw 2: random_float)
                     │
                 Is it 4★?
                 ├── YES ──> [Step 4: Resolve 4★ Outcome]
                 │                 ├── Guaranteed? ──> Select 1 of 3 featured 4★ ---- (Draw 3: choice)
                 │                 └── 50/50 Active? ──> [4★ 50/50 Roll] ---- (Draw 3: random_float)
                 │                                             ├── Won ──> Select 1 of 3 featured 4★ ---- (Draw 4: choice)
                 │                                             └── Lost ──> Select standard 4★ ---- (Draw 4: choice)
                 │
                 └── NO ───> [Step 5: 3★ Weapon Roll] ---- (Draw 3: choice)
```

**Rule**: No speculative or discarded RNG calls are permitted. If an outcome is guaranteed by pity or prior loss, the corresponding probability roll is bypassed.

---

## 10. Probability & Outcome Model Architecture

The probability calculation and outcome resolutions are decoupled into four modular abstractions:

```python
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass

class RarityProbabilityModel(ABC):
    """Abstract interface defining pull probability curves by rarity."""

    @abstractmethod
    def get_5star_probability(self, pity_5star_count: int) -> float:
        """Return 5★ probability for the given pity count (1 to 90)."""
        pass

    @abstractmethod
    def get_4star_probability(self, pity_4star_count: int) -> float:
        """Return 4★ probability for the given pity count (1 to 10+)."""
        pass

@dataclass(frozen=True)
class CapturingRadianceResult:
    """Result payload from a Capturing Radiance resolution attempt."""
    triggered: bool
    model_identifier: str
    reason: str                     # e.g., "GUARANTEED_STREAK", "MODEL_TRIGGERED", "NOT_TRIGGERED"
    updated_streak: int             # new streak count (0 if won/triggered, streak + 1 if lost)

class CapturingRadianceModel(ABC):
    """Abstract interface for Capturing Radiance resolution strategies."""

    @property
    @abstractmethod
    def model_identifier(self) -> str:
        """Unique identifier for the active CR model."""
        pass

    @abstractmethod
    def resolve(
        self,
        state: GachaState,
        rng: Any,
        context: Optional[Dict[str, Any]] = None
    ) -> CapturingRadianceResult:
        """Resolve whether Capturing Radiance triggers on an eligible 5★ pull."""
        pass

@dataclass(frozen=True)
class FiveStarOutcomeResult:
    """Outcome of resolving a 5★ drop."""
    item: WishItem
    is_featured: bool
    was_50_50: bool
    won_50_50: Optional[bool]
    cr_triggered: bool
    cr_model_id: Optional[str]

class FiveStarOutcomeModel(ABC):
    """Abstract interface for resolving 5★ character promotional vs standard outcome."""

    @abstractmethod
    def resolve_5star(
        self,
        state: GachaState,
        banner: Any,
        cr_model: CapturingRadianceModel,
        rng: Any
    ) -> FiveStarOutcomeResult:
        pass

@dataclass(frozen=True)
class FourStarOutcomeResult:
    """Outcome of resolving a 4★ drop."""
    item: WishItem
    is_featured: bool
    was_50_50: bool
    won_50_50: Optional[bool]

class FourStarOutcomeModel(ABC):
    """Abstract interface for resolving 4★ promotional vs standard outcome."""

    @abstractmethod
    def resolve_4star(
        self,
        state: GachaState,
        banner: Any,
        rng: Any
    ) -> FourStarOutcomeResult:
        pass
```

---

## 11. Soft-Pity Model

### Default Empirical Model (`StandardEmpiricalPityModel`)
*Epistemological Status*: **EMPIRICAL MODEL — NOT OFFICIAL (Level C)**.

#### 5★ Curve Formulation:
$$P_5(\text{pity}) = \begin{cases} 
0.006 & \text{if } 1 \le \text{pity} \le 73 \\ 
0.006 + (\text{pity} - 73) \times 0.06 & \text{if } 74 \le \text{pity} \le 89 \\ 
1.000 & \text{if } \text{pity} \ge 90 
\end{cases}$$

- Pulls 1–73: Flat base rate of $0.6\%$ (Official Fact, Level A).
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
1.000 & \text{if } \text{pity} \ge 10 
\end{cases}$$

- Pulls 1–8: Flat base rate of $5.1\%$ (Official Fact, Level A).
- Pull 9: Jump to $56.1\%$ (**EMPIRICAL MODEL — NOT OFFICIAL, Level C**).
- Pull 10: $100.0\%$ (Official Hard Pity, Level A).

> [!NOTE]
> Neither the linear $+6\%$ escalation for 5★ nor the pull-9 jump to $56.1\%$ for 4★ is an official published formula. Both are empirical community models derived from aggregate wish trackers.

---

## 12. 5★ Rules

1. **Base Rate**: $0.006$ ($0.6\%$) (Level A).
2. **Consolidated Rate**: $0.016$ ($1.6\%$) metadata property (Level A).
3. **Hard Pity**: Reaching pull 90 guarantees a 5★ item (Level A).
4. **Pool Structure**:
   - Exactly 1 featured promotional 5★ character.
   - Standard 5★ character pool: `["Jean", "Diluc", "Qiqi", "Mona", "Keqing", "Tighnari", "Dehya"]`.
5. **Deduplication**: Standard 5★ characters are drawn uniformly from the standard units.

---

## 13. 4★ Rules

1. **Base Rate**: $0.051$ ($5.1\%$) (Level A).
2. **Consolidated Rate**: $0.130$ ($13.0\%$) metadata property (Level A).
3. **Hard Pity**: Reaching pull 10 guarantees a 4★ or higher item (Level A).
4. **Pool Structure**:
   - Exactly 3 featured promotional 4★ characters.
   - Standard 4★ pool consisting of characters and weapons.
5. **Featured Selection**: When a featured 4★ is awarded, each of the 3 featured units has an exact $\frac{1}{3}$ ($33.\overline{3}\%$) selection probability (Level A).
6. **Non-Featured Distribution**: When a non-featured 4★ item is awarded, the split between 4★ characters and 4★ weapons is modeled as 50% character / 50% weapon (**EMPIRICAL MODEL — NOT OFFICIAL, Level C**).

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

### 15.1 Official Published Parameters (Level A)
The official HoYoverse announcement ("Capturing Radiance" Mechanic: You Ask, I Answer!, Aug 16, 2024 / Feb 10, 2025) establishes:
1. **Base Trigger Probability**: $0.018\%$ ($0.00018$).
2. **Consolidated Promotional Probability**: $55.000\%$ (overall effective probability of obtaining the promotional 5★ character on a 5★ event wish outcome, taking Capturing Radiance into account).
3. **Guaranteed Trigger Condition**: "If the promotional 5★ character is the second 5★ character obtained on three consecutive occasions, Capturing Radiance is guaranteed to trigger on the next applicable 5★ pull."
4. **Applicability Clarification**: Capturing Radiance applies **only** where the normal 50/50 applies (`featured_5star_guaranteed == False`). It does **not** apply when a guarantee is active, and does **not** alter or consume an existing guarantee.

### 15.2 Critical Mathematical Contradiction & Research Disclaimers
> [!IMPORTANT]
> **The exact mapping between the published 0.018% base trigger probability, the 55% consolidated promotional probability, and hidden internal Capturing Radiance state/probability behavior is not publicly specified. Therefore the simulator must not present one guessed mapping as official.**

**Mathematical Contradiction of the Naive Bernoulli Model**:
If Capturing Radiance were implemented as a naive Bernoulli trial rolling $P = 0.00018$ followed by a standard $50/50$ roll:
$$P(\text{promotional single 50/50 pull}) = 0.00018 + (1 - 0.00018) \times 0.5 = 0.00018 + 0.49991 = 0.50009 \quad (50.009\%)$$
Factoring in the guaranteed trigger after 3 consecutive losses:
The probability of 3 consecutive losses is $q^3 \approx 0.49991^3 \approx 0.1249$. Even when factoring in this guaranteed reset, the long-term consolidated promotional rate rises only to $\approx 51.7\%$, mathematically failing to reproduce the official $55.000\%$ rate.

### 15.3 Research / Implementation Blocker Status
> [!CAUTION]
> **RESEARCH / IMPLEMENTATION BLOCKER**:
> Exact CR probability/state mapping is insufficiently specified.
> Because HoYoverse has not published the exact hidden state transitions or probability function bridging 0.018% and 55%, any default simulator implementation attempting to satisfy both numbers simultaneously is an **empirical hypothesis**, not an official server rule.
> 
> Implementation of a default Capturing Radiance model claiming to achieve 55% is **BLOCKED** pending approval of a formal empirical model specification. The engine architecture isolates this logic entirely behind the `CapturingRadianceModel` interface so that empirical models may be evaluated and plugged in without altering `GachaState` or `GachaEngine`.

### 15.4 Capturing Radiance Model Interface
```python
class CapturingRadianceModel(ABC):
    """Pluggable strategy for evaluating Capturing Radiance."""

    @property
    @abstractmethod
    def model_identifier(self) -> str:
        """Returns the unique identifier of the model."""
        pass

    @abstractmethod
    def resolve(
        self,
        state: GachaState,
        rng: Any,
        context: Optional[Dict[str, Any]] = None
    ) -> CapturingRadianceResult:
        """Evaluate Capturing Radiance on an eligible 5★ pull.
        
        Must return CapturingRadianceResult containing:
        - triggered: bool
        - model_identifier: str
        - reason: str ('GUARANTEED_STREAK', 'EMPIRICAL_TRIGGER', 'NOT_TRIGGERED')
        - updated_streak: int
        """
        pass
```

### 15.5 Capturing Radiance State Transitions
- **Eligibility**: Evaluated **only** when obtaining a 5★ AND `featured_5star_guaranteed == False`.
- **Active Guarantee**: If `featured_5star_guaranteed == True`, Capturing Radiance is **not evaluated**, not rolled, does not alter guarantees, and leaves `capturing_radiance_streak` unchanged.
- **Streak Guarantee Trigger**: If `capturing_radiance_streak == 3`, CR triggers with certainty ($P=1.0$), awards the promotional character, and resets `capturing_radiance_streak = 0`.
- **Model Trigger**: If CR triggers via the active `CapturingRadianceModel`, awards the promotional character, sets `featured_5star_guaranteed = False`, and resets `capturing_radiance_streak = 0`.
- **Standard 50/50 Win**: If CR does not trigger and standard 50/50 is won, awards promotional character, sets `featured_5star_guaranteed = False`, and resets `capturing_radiance_streak = 0`.
- **Standard 50/50 Loss**: If CR does not trigger and standard 50/50 is lost, awards standard 5★ character, sets `featured_5star_guaranteed = True`, and increments `capturing_radiance_streak += 1`.
- **Carry-Over**: `capturing_radiance_streak` is shared between Character Event Wish and Character Event Wish-2 and persists across banner rotations.

---

## 16. Banner Carry-Over

1. **Concurrent Banner Sharing**:
   - Character Event Wish (Banner 1) and Character Event Wish-2 (Banner 2) share the exact same mutable `GachaState` reference.
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
  "pity_collision_policy": "DEFER_AT_CAP",
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
    "official_published_base_rate": 0.00018,
    "official_consolidated_promotional_rate": 0.55,
    "guaranteed_streak_threshold": 3,
    "default_model_identifier": "naive_bernoulli_empirical"
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
   - $0 \le \text{pity\_4star} \le 10$ (depending on `PityCollisionPolicy`)
2. **Pity Independence Invariant**:
   - Awarding a 5★ item MUST NOT reset `pity_4star` to 0.
   - Awarding a 4★ item MUST NOT reset `pity_5star` to 0.
3. **Hard Pity Invariants**:
   - A pull initiated at $\text{pity\_5star} = 89$ MUST yield a 5★ item.
   - A pull initiated at $\text{pity\_4star} \ge 9$ MUST yield a 4★ or 5★ item.
4. **Streak Invariant**:
   - $0 \le \text{capturing\_radiance\_streak} \le 3$.
   - A 50/50 pull initiated at $\text{capturing\_radiance\_streak} = 3$ MUST trigger Capturing Radiance ($P=1.0$).
5. **Guarantee Invariants**:
   - When $\text{featured\_5star\_guaranteed} == \text{True}$, an awarded 5★ item MUST be the promotional character. Capturing Radiance is never evaluated.
   - When $\text{featured\_4star\_guaranteed} == \text{True}$, an awarded 4★ item MUST be one of the 3 featured 4★ characters.
6. **State Conservation**:
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
- Capturing Radiance trigger indicator, model identifier, and historical streak counter

---

## 23. API Boundary

```
[Presentation / Frontend]
          ↓ HTTP JSON
[API Transport Layer (app/api/v1/gacha.py)]
          ↓ Dependency Injection
[Gacha Engine (app/core/gacha/engine.py)]
          ↓
[State Management (GachaState)]  &  [Outcome & Probability Models]
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

---

## 25. Deterministic Test Vectors

The test suite must implement the following deterministic seeded scenarios:

1. **5★ Hard Pity**:
   - Mock probability model returning $P_5 = 0.0$ for pulls 1–89 and $P_5 = 1.0$ at pull 90.
   - Assert: Pulls 1–89 yield non-5★; pull 90 yields 5★ with `pity_count_5star == 90`.
2. **4★ Hard Pity**:
   - Mock probability model returning $P_4 = 0.0$ for pulls 1–9 and $P_4 = 1.0$ at pull 10.
   - Assert: Pull 10 yields 4★+ with `pity_count_4star == 10`.
3. **Independent 4★ Pity Tracking on 5★ Drop**:
   - Pull sequence where 5★ is awarded at `pity_4star == 5`.
   - Assert: 5★ item awarded, `pity_5star` resets to 0, `pity_4star` increments to 6 (NOT reset to 0).
4. **4★ Pity Collision at Pull 10 (`SIMULATOR DESIGN CHOICE`)**:
   - Force 5★ drop on a pull where `pity_4star == 9`.
   - Assert: 5★ item awarded, `pity_5star` resets to 0, `pity_4star` handled per `PityCollisionPolicy` (e.g. preserved at 9 so that next pull triggers 4★ hard pity).
5. **50/50 Loss and Guarantee**:
   - Force 5★ drop with 50/50 loss (CR not triggered).
   - Assert: Standard 5★ awarded, `featured_5star_guaranteed == True`, `capturing_radiance_streak == 1`.
   - Next 5★ drop: Assert promotional character awarded, `featured_5star_guaranteed == False`.
6. **Capturing Radiance Streak Guarantee**:
   - Force 3 consecutive 50/50 losses (interspersed with guaranteed pulls).
   - Assert: `capturing_radiance_streak == 3`.
   - Next 50/50 pull: Assert Capturing Radiance triggers ($P_{\text{CR}} = 1.0$), promotional character awarded, `capturing_radiance_streak == 0`.
7. **Capturing Radiance Pluggable Model Delegation**:
   - Configure engine with a mock `CapturingRadianceModel` returning `triggered=True`.
   - Assert: Promotional character awarded with `capturing_radiance_triggered == True`, `capturing_radiance_streak == 0`.
8. **Concurrent Banner Carry-Over**:
   - Execute 50 pulls on Banner 1 (`pity_5star == 50`).
   - Execute 1 pull on Banner 2.
   - Assert: Pull on Banner 2 is evaluated at `pity_count_5star == 51`; `state.pity_5star == 51`.
9. **Batch Equivalence**:
   - Seed engine with seed $S$, execute `pull(banner_id, 10)`.
   - Re-seed independent engine with seed $S$, execute `single_pull(banner_id)` 10 times.
   - Assert: Item identities, pity counts, and guarantee states match 100% item-for-item.

---

## 26. Statistical Test Strategy

For every statistical acceptance test, the parameters and mathematical guarantees are explicitly documented:

| Metric | Officially Published (Level A) | Empirical Target | Model Tested | Expected Tolerance | Mathematically Guaranteed by Model? |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **5★ Consolidated Rate** | $1.600\%$ | $1.600\%$ | `StandardEmpiricalPityModel` ($N = 200{,}000$) | $\pm 0.100\%$ | **YES**: Analytical Markov chain and Monte Carlo simulations under this curve yield $\approx 1.604\%$. |
| **4★ Consolidated Rate** | $13.000\%$ | $13.000\%$ | `StandardEmpiricalPityModel` with independent pity ($N = 200{,}000$) | $\pm 0.500\%$ | **YES**: Yields $\approx 13.0\%$. |
| **Consolidated Promotional 5★ Rate (Capturing Radiance)** | $55.000\%$ | Model-Specific | Requires approved empirical `CapturingRadianceModel` | $\pm 1.000\%$ | **NO MATHEMATICAL GUARANTEE UNDER NAIVE MODEL**: A naive Bernoulli model ($P=0.00018$ then $50/50$) yields $\approx 51.7\%$, mathematically contradicting the $55\%$ official target. A test asserting $55\%$ is valid ONLY for an empirical model specifically calibrated to produce $55\%$. Tests must assert the specific model's expected value. |

---

## 27. Regression Strategy

- All existing 93 automated unit tests in `tests/test_artifact.py`, `tests/test_probability.py`, `tests/test_rng.py`, and `tests/test_api.py` must remain 100% passing.
- Gacha engine tests must reside in a dedicated test module (`tests/test_gacha_engine.py`) without modifying existing test fixtures.

---

## 28. Acceptance Criteria

P2 implementation will be approved for sign-off only if:

- [ ] All 22 scope items are implemented in domain and engine code.
- [ ] 4★ and 5★ pity counters are strictly independent (`pity_4star` is not wiped by 5★ drops).
- [ ] 4★ pity collision at pull 10 is isolated behind a configurable `PityCollisionPolicy`.
- [ ] Capturing Radiance is decoupled into a pluggable `CapturingRadianceModel` interface.
- [ ] No claim is made that rolling $P=0.00018$ followed by standard $50/50$ reproduces the official $55\%$ consolidated rate.
- [ ] Empirical soft-pity curves and standard pool splits are explicitly labeled as `EMPIRICAL MODEL — NOT OFFICIAL`.
- [ ] Character Event Wish and Character Event Wish-2 share identical atomic state.
- [ ] Batch execution is mathematically identical to sequential single pulls.
- [ ] All deterministic test vectors pass.
- [ ] Statistical tests verify models against their mathematically proven targets without false derivations.
- [ ] Zero production changes to Artifact Engine or core RNG abstractions.

---

## 29. Known Research Limitations & Blockers

1. **Proprietary Server PRNG**: HoYoverse's exact server-side random number generator and floating-point comparison sequence are proprietary and unobservable.
2. **Soft-Pity Formula**: The linear $+6\%$ escalation from pull 74 to 89 is an empirical community model (Level C), not an officially published formula.
3. **4★ Non-Featured Weapon vs. Character Split**: Modeled as 50/50 per community consensus (Level C).
4. **Capturing Radiance Exact Mapping (`RESEARCH / IMPLEMENTATION BLOCKER`)**:
   The exact internal server mechanism mapping the published 0.018% base trigger rate and the 55% consolidated promotional rate has not been disclosed by HoYoverse. A naive single roll cannot reproduce 55%. Selection of a production default model is **BLOCKED** until an empirical model specification reconciling this behavior is formally approved.
5. **4★ Pity Collision at Pull 10 (`SIMULATOR DESIGN CHOICE`)**:
   Server behavior when a 5★ drops on the 10th pull of 4★ pity is unrevealed; handled via configurable `PityCollisionPolicy`.

---

## 30. Implementation Order

When implementation commences in subsequent prompts, work will proceed in the following strict order:

1. **Step 1: Domain Models & State (`app/core/gacha/models.py`)**
   - Enums: `Rarity`, `ItemType`, `BannerType`, `PityCollisionPolicy`.
   - Dataclasses: `WishItem`, `PullResult`, `GachaState` with independent pity validation.
2. **Step 2: Configuration Schemas & Loader (`app/core/gacha/config.py`)**
   - Dataclasses: `GachaBannerConfig`, `GachaRulesConfig`.
   - JSON data files in `config/gacha/` (`rules.json`, `banners.json`, `pools.json`).
3. **Step 3: Model Abstractions (`app/core/gacha/probability_model.py`)**
   - Interfaces: `RarityProbabilityModel`, `CapturingRadianceModel`, `FiveStarOutcomeModel`, `FourStarOutcomeModel`.
   - Default empirical soft-pity model (`StandardEmpiricalPityModel`).
4. **Step 4: Gacha Engine (`app/core/gacha/engine.py`)**
   - Core `GachaEngine` class with pluggable models and collision policy.
   - Methods: `single_pull()`, `pull()`, `save_state()`, `restore_state()`.
5. **Step 5: Automated Unit & Deterministic Tests (`tests/test_gacha_engine.py`)**
   - Implementation of all deterministic test vectors (hard pity, independent pity, streak guarantee, mock CR model).
6. **Step 6: Statistical Verification & Sign-Off**
   - Monte Carlo convergence verification against model-specific mathematical targets.
