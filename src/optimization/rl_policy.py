# ============================================================================
# Reinforcement Learning Policy Layer
# Adaptive RL agent for real-time process optimization
# ============================================================================
import numpy as np
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class ManufacturingEnvironment:
    """
    RL Environment for batch manufacturing optimization.
    State: current process parameters & metrics
    Actions: parameter adjustments
    Reward: multi-objective reward combining quality, energy, carbon
    """

    def __init__(
        self,
        predictor=None,
        bounds: Optional[Dict[str, Tuple[float, float]]] = None,
    ):
        self.predictor = predictor
        self.bounds = bounds or {
            "Granulation_Time": (9, 27),
            "Binder_Amount": (5.5, 14.0),
            "Drying_Temp": (42, 74),
            "Drying_Time": (15, 48),
            "Compression_Force": (4.5, 18.0),
            "Machine_Speed": (90, 280),
            "Lubricant_Conc": (0.3, 2.8),
        }

        self.param_names = list(self.bounds.keys())
        self.n_params = len(self.param_names)

        # Action space: 3 actions per parameter (decrease, keep, increase)
        self.n_actions = 3 ** self.n_params
        self.action_step_size = 0.05  # 5% of range

        # Current state
        self.current_params: Dict[str, float] = {}
        self.step_count = 0
        self.max_steps = 50

    def reset(self) -> np.ndarray:
        """Reset environment with random initial parameters."""
        self.current_params = {}
        for param, (low, high) in self.bounds.items():
            self.current_params[param] = np.random.uniform(low, high)
        self.step_count = 0
        return self._get_state()

    def _get_state(self) -> np.ndarray:
        """Convert current parameters to normalized state vector."""
        state = []
        for param in self.param_names:
            low, high = self.bounds[param]
            normalized = (self.current_params[param] - low) / (high - low + 1e-10)
            state.append(normalized)
        return np.array(state)

    def _decode_action(self, action_idx: int) -> Dict[str, int]:
        """Decode action index to per-parameter adjustments."""
        adjustments = {}
        remaining = action_idx
        for param in self.param_names:
            adj = remaining % 3 - 1  # -1, 0, +1
            adjustments[param] = adj
            remaining //= 3
        return adjustments

    def step(
        self, action_idx: int
    ) -> Tuple[np.ndarray, float, bool, Dict]:
        """Execute action and return (next_state, reward, done, info)."""
        adjustments = self._decode_action(action_idx)

        # Apply adjustments
        for param, adj in adjustments.items():
            low, high = self.bounds[param]
            step = adj * self.action_step_size * (high - low)
            self.current_params[param] = np.clip(
                self.current_params[param] + step, low, high
            )

        # Compute reward
        reward, info = self._compute_reward()

        self.step_count += 1
        done = self.step_count >= self.max_steps

        return self._get_state(), reward, done, info

    def _compute_reward(self) -> Tuple[float, Dict]:
        """
        Compute multi-objective reward.
        Combines quality, yield, energy efficiency, and carbon metrics.
        """
        params = self.current_params

        if self.predictor is not None:
            predictions = self.predictor.predict_single(params)
        else:
            # Simplified physics-based reward
            predictions = self._simplified_predict(params)

        # Quality reward (Hardness near 100, Dissolution > 85)
        hardness = predictions.get("Hardness", 90)
        dissolution = predictions.get("Dissolution_Rate", 90)
        quality_reward = (
            -abs(hardness - 100) / 50 +
            max(0, dissolution - 85) / 15
        )

        # Yield reward (Content Uniformity near 100)
        cu = predictions.get("Content_Uniformity", 98)
        yield_reward = -abs(cu - 100) / 10

        # Energy reward (lower is better)
        energy = predictions.get("Energy_Consumption_kWh", 300)
        energy_reward = -energy / 500

        # Carbon reward (lower is better)
        co2 = predictions.get("CO2_Emissions_kg", 120)
        carbon_reward = -co2 / 200

        # Combined weighted reward
        total_reward = (
            0.30 * quality_reward +
            0.25 * yield_reward +
            0.25 * energy_reward +
            0.20 * carbon_reward
        )

        info = {
            "quality_reward": quality_reward,
            "yield_reward": yield_reward,
            "energy_reward": energy_reward,
            "carbon_reward": carbon_reward,
            "predictions": predictions,
        }

        return float(total_reward), info

    def _simplified_predict(self, params: Dict) -> Dict:
        """Simplified prediction without ML model."""
        cf = params.get("Compression_Force", 12.5)
        ms = params.get("Machine_Speed", 150)
        ba = params.get("Binder_Amount", 8.5)
        lc = params.get("Lubricant_Conc", 1.0)
        dt = params.get("Drying_Temp", 60)

        return {
            "Hardness": 50 + 4 * cf - 0.08 * ms + 2 * ba,
            "Dissolution_Rate": 95 - 0.3 * cf + 0.1 * ms - 0.5 * ba,
            "Content_Uniformity": 98 + 0.2 * params.get("Granulation_Time", 15) - 0.3 * lc,
            "Energy_Consumption_kWh": 200 + 2 * cf + 0.5 * ms + 0.8 * dt,
            "CO2_Emissions_kg": 80 + 0.8 * cf + 0.2 * ms + 0.3 * dt,
        }


class RLPolicyOptimizer:
    """
    Q-Learning based RL policy for manufacturing process optimization.
    Uses discretized state-action space with epsilon-greedy exploration.
    """

    def __init__(
        self,
        env: Optional[ManufacturingEnvironment] = None,
        learning_rate: float = 0.1,
        discount_factor: float = 0.99,
        epsilon: float = 0.1,
        n_episodes: int = 1000,
    ):
        self.env = env or ManufacturingEnvironment()
        self.lr = learning_rate
        self.gamma = discount_factor
        self.epsilon = epsilon
        self.n_episodes = n_episodes

        # Discretize state space
        self.n_bins = 10
        self.q_table: Dict = defaultdict(lambda: np.zeros(self.env.n_actions))

        # Training history
        self.episode_rewards: List[float] = []
        self.best_params: Optional[Dict] = None
        self.best_reward: float = -np.inf

    def _discretize_state(self, state: np.ndarray) -> Tuple:
        """Convert continuous state to discrete bins."""
        bins = np.digitize(state, np.linspace(0, 1, self.n_bins))
        return tuple(bins)

    def _choose_action(self, state: Tuple) -> int:
        """Epsilon-greedy action selection."""
        if np.random.random() < self.epsilon:
            # Explore: random action (simplified - random per-param adj)
            return np.random.randint(min(self.env.n_actions, 2187))  # Cap at 3^7
        else:
            # Exploit: best known action
            q_values = self.q_table[state]
            return int(np.argmax(q_values[:min(len(q_values), 2187)]))

    def train(self) -> Dict:
        """Train the RL policy."""
        logger.info(f"Training RL policy: {self.n_episodes} episodes")

        # Limit action space for tractability
        max_actions = min(self.env.n_actions, 2187)  # 3^7

        for episode in range(self.n_episodes):
            state = self.env.reset()
            state_disc = self._discretize_state(state)
            episode_reward = 0

            for step in range(self.env.max_steps):
                action = self._choose_action(state_disc)
                action = action % max_actions

                next_state, reward, done, info = self.env.step(action)
                next_state_disc = self._discretize_state(next_state)

                # Q-learning update
                best_next = np.max(self.q_table[next_state_disc][:max_actions])
                td_target = reward + self.gamma * best_next * (1 - done)
                td_error = td_target - self.q_table[state_disc][action]
                self.q_table[state_disc][action] += self.lr * td_error

                state_disc = next_state_disc
                episode_reward += reward

                if done:
                    break

            self.episode_rewards.append(episode_reward)

            # Track best
            if episode_reward > self.best_reward:
                self.best_reward = episode_reward
                self.best_params = self.env.current_params.copy()

            # Decay epsilon
            self.epsilon = max(0.01, self.epsilon * 0.999)

            if episode % 200 == 0:
                avg_reward = np.mean(self.episode_rewards[-100:])
                logger.info(
                    f"Episode {episode}: avg_reward={avg_reward:.4f}, "
                    f"epsilon={self.epsilon:.4f}"
                )

        logger.info(f"RL training complete. Best reward: {self.best_reward:.4f}")

        return {
            "best_params": self.best_params,
            "best_reward": float(self.best_reward),
            "n_episodes": self.n_episodes,
            "final_epsilon": float(self.epsilon),
            "reward_history": self.episode_rewards,
        }

    def recommend_action(self, current_state: Dict[str, float]) -> Dict:
        """Recommend optimal action given current state."""
        self.env.current_params = current_state.copy()
        state = self.env._get_state()
        state_disc = self._discretize_state(state)

        # Greedy action
        q_values = self.q_table[state_disc]
        max_actions = min(len(q_values), 2187)
        best_action = int(np.argmax(q_values[:max_actions]))

        adjustments = self.env._decode_action(best_action)

        # Compute suggested new parameters
        suggested = {}
        for param, adj in adjustments.items():
            low, high = self.env.bounds[param]
            step = adj * self.env.action_step_size * (high - low)
            suggested[param] = float(np.clip(
                current_state[param] + step, low, high
            ))

        return {
            "action": best_action,
            "adjustments": adjustments,
            "suggested_params": suggested,
            "expected_improvement": float(q_values[best_action]),
        }
