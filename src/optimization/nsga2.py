# ============================================================================
# NSGA-II Multi-Objective Optimization
# Non-dominated Sorting Genetic Algorithm II
# ============================================================================
import numpy as np
from typing import Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class OptimizationObjective:
    """Definition of an optimization objective."""
    name: str
    direction: str  # "minimize" or "maximize"
    weight: float = 1.0
    target_value: Optional[float] = None
    constraint_min: Optional[float] = None
    constraint_max: Optional[float] = None


@dataclass
class OptimizationVariable:
    """Definition of an optimization variable (decision parameter)."""
    name: str
    lower_bound: float
    upper_bound: float
    var_type: str = "continuous"  # "continuous" or "integer"


@dataclass
class ParetoSolution:
    """A solution on the Pareto front."""
    variables: Dict[str, float]
    objectives: Dict[str, float]
    rank: int = 0
    crowding_distance: float = 0.0
    feasible: bool = True


class NSGA2Optimizer:
    """
    NSGA-II (Non-dominated Sorting Genetic Algorithm II)
    for multi-objective optimization of manufacturing parameters.

    Optimizes:
    - Maximize: Yield, Productivity, Quality
    - Minimize: Specific Energy, Carbon Footprint, Process Deviation

    Constraints:
    - Equipment operating limits
    - Quality specification bounds
    - Regulatory emission caps
    """

    def __init__(
        self,
        pop_size: int = 100,
        n_generations: int = 200,
        crossover_prob: float = 0.9,
        mutation_prob: float = 0.1,
        seed: int = 42,
    ):
        self.pop_size = pop_size
        self.n_gen = n_generations
        self.crossover_prob = crossover_prob
        self.mutation_prob = mutation_prob
        self.rng = np.random.RandomState(seed)

        self.variables: List[OptimizationVariable] = []
        self.objectives: List[OptimizationObjective] = []
        self.objective_function: Optional[Callable] = None

        # Results
        self.pareto_front: List[ParetoSolution] = []
        self.history: List[Dict] = []

    def set_variables(self, variables: List[OptimizationVariable]):
        """Set decision variables."""
        self.variables = variables

    def set_objectives(self, objectives: List[OptimizationObjective]):
        """Set optimization objectives."""
        self.objectives = objectives

    def set_objective_function(self, func: Callable):
        """Set the function that evaluates objectives given variables."""
        self.objective_function = func

    def _initialize_population(self) -> np.ndarray:
        """Create initial random population within bounds."""
        n_vars = len(self.variables)
        pop = np.zeros((self.pop_size, n_vars))

        for j, var in enumerate(self.variables):
            pop[:, j] = self.rng.uniform(
                var.lower_bound, var.upper_bound, self.pop_size
            )
            if var.var_type == "integer":
                pop[:, j] = np.round(pop[:, j])

        return pop

    def _evaluate_population(
        self, population: np.ndarray
    ) -> np.ndarray:
        """Evaluate all objectives for the population."""
        n_obj = len(self.objectives)
        fitness = np.zeros((len(population), n_obj))

        for i, individual in enumerate(population):
            var_dict = {
                var.name: individual[j]
                for j, var in enumerate(self.variables)
            }
            obj_values = self.objective_function(var_dict)

            for k, obj in enumerate(self.objectives):
                val = obj_values.get(obj.name, 0)
                # Convert maximization to minimization (NSGA-II minimizes)
                if obj.direction == "maximize":
                    fitness[i, k] = -val
                else:
                    fitness[i, k] = val

        return fitness

    def _non_dominated_sort(
        self, fitness: np.ndarray
    ) -> List[List[int]]:
        """Perform non-dominated sorting."""
        n = len(fitness)
        domination_count = np.zeros(n, dtype=int)
        dominated_set = [[] for _ in range(n)]
        fronts = [[]]

        for p in range(n):
            for q in range(n):
                if p == q:
                    continue
                if self._dominates(fitness[p], fitness[q]):
                    dominated_set[p].append(q)
                elif self._dominates(fitness[q], fitness[p]):
                    domination_count[p] += 1

            if domination_count[p] == 0:
                fronts[0].append(p)

        i = 0
        while fronts[i]:
            next_front = []
            for p in fronts[i]:
                for q in dominated_set[p]:
                    domination_count[q] -= 1
                    if domination_count[q] == 0:
                        next_front.append(q)
            i += 1
            fronts.append(next_front)

        return [f for f in fronts if f]

    def _dominates(self, p: np.ndarray, q: np.ndarray) -> bool:
        """Check if solution p dominates solution q (all minimized)."""
        return np.all(p <= q) and np.any(p < q)

    def _crowding_distance(
        self, fitness: np.ndarray, front: List[int]
    ) -> np.ndarray:
        """Compute crowding distance for a front."""
        n = len(front)
        if n <= 2:
            return np.full(n, np.inf)

        distances = np.zeros(n)
        n_obj = fitness.shape[1]

        for m in range(n_obj):
            sorted_indices = np.argsort(fitness[front, m])
            distances[sorted_indices[0]] = np.inf
            distances[sorted_indices[-1]] = np.inf

            f_range = fitness[front[sorted_indices[-1]], m] - fitness[front[sorted_indices[0]], m]
            if f_range == 0:
                continue

            for i in range(1, n - 1):
                distances[sorted_indices[i]] += (
                    fitness[front[sorted_indices[i + 1]], m]
                    - fitness[front[sorted_indices[i - 1]], m]
                ) / f_range

        return distances

    def _sbx_crossover(
        self, parent1: np.ndarray, parent2: np.ndarray, eta: float = 20
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Simulated Binary Crossover (SBX)."""
        child1 = parent1.copy()
        child2 = parent2.copy()

        if self.rng.random() > self.crossover_prob:
            return child1, child2

        for j in range(len(parent1)):
            if self.rng.random() < 0.5:
                if abs(parent1[j] - parent2[j]) > 1e-10:
                    u = self.rng.random()
                    if u <= 0.5:
                        beta = (2 * u) ** (1 / (eta + 1))
                    else:
                        beta = (1 / (2 * (1 - u))) ** (1 / (eta + 1))

                    child1[j] = 0.5 * ((1 + beta) * parent1[j] + (1 - beta) * parent2[j])
                    child2[j] = 0.5 * ((1 - beta) * parent1[j] + (1 + beta) * parent2[j])

        # Clip to bounds
        for j, var in enumerate(self.variables):
            child1[j] = np.clip(child1[j], var.lower_bound, var.upper_bound)
            child2[j] = np.clip(child2[j], var.lower_bound, var.upper_bound)
            if var.var_type == "integer":
                child1[j] = round(child1[j])
                child2[j] = round(child2[j])

        return child1, child2

    def _polynomial_mutation(
        self, individual: np.ndarray, eta: float = 20
    ) -> np.ndarray:
        """Polynomial mutation."""
        mutant = individual.copy()

        for j, var in enumerate(self.variables):
            if self.rng.random() < self.mutation_prob:
                delta = var.upper_bound - var.lower_bound
                u = self.rng.random()

                if u < 0.5:
                    delta_q = (2 * u) ** (1 / (eta + 1)) - 1
                else:
                    delta_q = 1 - (2 * (1 - u)) ** (1 / (eta + 1))

                mutant[j] = individual[j] + delta_q * delta
                mutant[j] = np.clip(mutant[j], var.lower_bound, var.upper_bound)

                if var.var_type == "integer":
                    mutant[j] = round(mutant[j])

        return mutant

    def _tournament_selection(
        self, ranks: np.ndarray, crowding: np.ndarray
    ) -> int:
        """Binary tournament selection based on rank and crowding distance."""
        i, j = self.rng.choice(len(ranks), 2, replace=False)

        if ranks[i] < ranks[j]:
            return i
        elif ranks[j] < ranks[i]:
            return j
        elif crowding[i] > crowding[j]:
            return i
        else:
            return j

    def optimize(self) -> List[ParetoSolution]:
        """Run NSGA-II optimization."""
        if not self.variables or not self.objectives or not self.objective_function:
            raise ValueError("Variables, objectives, and objective function must be set")

        logger.info(
            f"Starting NSGA-II: {len(self.variables)} variables, "
            f"{len(self.objectives)} objectives, "
            f"{self.pop_size} pop, {self.n_gen} generations"
        )

        # Initialize
        population = self._initialize_population()
        fitness = self._evaluate_population(population)

        for gen in range(self.n_gen):
            # Create offspring
            offspring = np.zeros_like(population)
            ranks_full = np.zeros(len(population))
            crowding_full = np.zeros(len(population))

            # Non-dominated sorting
            fronts = self._non_dominated_sort(fitness)

            idx = 0
            for rank, front in enumerate(fronts):
                cd = self._crowding_distance(fitness, front)
                for fi, f_idx in enumerate(front):
                    if f_idx < len(ranks_full):
                        ranks_full[f_idx] = rank
                        crowding_full[f_idx] = cd[fi]

            # Generate offspring
            for i in range(0, self.pop_size, 2):
                p1 = self._tournament_selection(ranks_full, crowding_full)
                p2 = self._tournament_selection(ranks_full, crowding_full)

                c1, c2 = self._sbx_crossover(population[p1], population[p2])
                c1 = self._polynomial_mutation(c1)
                c2 = self._polynomial_mutation(c2)

                offspring[i] = c1
                if i + 1 < self.pop_size:
                    offspring[i + 1] = c2

            # Evaluate offspring
            offspring_fitness = self._evaluate_population(offspring)

            # Combine parent and offspring
            combined_pop = np.vstack([population, offspring])
            combined_fitness = np.vstack([fitness, offspring_fitness])

            # Select next generation
            fronts = self._non_dominated_sort(combined_fitness)
            new_pop = []
            new_fitness = []

            for front in fronts:
                if len(new_pop) + len(front) <= self.pop_size:
                    for idx in front:
                        new_pop.append(combined_pop[idx])
                        new_fitness.append(combined_fitness[idx])
                else:
                    # Sort by crowding distance
                    cd = self._crowding_distance(combined_fitness, front)
                    sorted_idx = np.argsort(-cd)
                    remaining = self.pop_size - len(new_pop)
                    for si in sorted_idx[:remaining]:
                        new_pop.append(combined_pop[front[si]])
                        new_fitness.append(combined_fitness[front[si]])
                    break

            population = np.array(new_pop)
            fitness = np.array(new_fitness)

            # Track progress
            if gen % 50 == 0 or gen == self.n_gen - 1:
                first_front = fronts[0] if fronts else []
                self.history.append({
                    "generation": gen,
                    "pareto_size": len(first_front),
                    "best_fitness": [float(np.min(fitness[:, k])) for k in range(fitness.shape[1])],
                })
                logger.info(f"Gen {gen}: Pareto size = {len(first_front)}")

        # Extract final Pareto front
        fronts = self._non_dominated_sort(fitness)
        pareto_indices = fronts[0] if fronts else []

        self.pareto_front = []
        for idx in pareto_indices:
            var_dict = {
                var.name: float(population[idx, j])
                for j, var in enumerate(self.variables)
            }
            obj_dict = {}
            for k, obj in enumerate(self.objectives):
                val = fitness[idx, k]
                if obj.direction == "maximize":
                    val = -val  # Convert back
                obj_dict[obj.name] = float(val)

            self.pareto_front.append(ParetoSolution(
                variables=var_dict,
                objectives=obj_dict,
                rank=0,
            ))

        logger.info(f"NSGA-II complete. Pareto front size: {len(self.pareto_front)}")
        return self.pareto_front

    def get_best_solution(
        self, priority_weights: Optional[Dict[str, float]] = None
    ) -> Optional[ParetoSolution]:
        """
        Select best solution from Pareto front based on weighted priorities.
        """
        if not self.pareto_front:
            return None

        if priority_weights is None:
            priority_weights = {obj.name: obj.weight for obj in self.objectives}

        best_score = -np.inf
        best_solution = None

        for sol in self.pareto_front:
            score = 0
            for obj in self.objectives:
                val = sol.objectives.get(obj.name, 0)
                weight = priority_weights.get(obj.name, 1.0)

                # Normalize by objective range
                obj_values = [
                    s.objectives.get(obj.name, 0) for s in self.pareto_front
                ]
                obj_range = max(obj_values) - min(obj_values) + 1e-10

                if obj.direction == "maximize":
                    score += weight * (val - min(obj_values)) / obj_range
                else:
                    score += weight * (max(obj_values) - val) / obj_range

            if score > best_score:
                best_score = score
                best_solution = sol

        return best_solution
