import abc
import random

from models import ChallengeStep, StepStatus
from services.distribution_strategies import get_strategy


class ChallengeStrategy(abc.ABC):
    @abc.abstractmethod
    def generate_steps(
        self,
        challenge_id: int,
        goal_id: int,
        target_amount: int,
        count: int,
        distribution: str,
    ) -> list[ChallengeStep]:
        raise NotImplementedError


class EnvelopeChallengeStrategy(ChallengeStrategy):
    def generate_steps(
        self,
        challenge_id: int,
        goal_id: int,
        target_amount: int,
        count: int,
        distribution: str,
    ) -> list[ChallengeStep]:
        strategy = get_strategy(distribution)
        amounts = strategy.distribute(target_amount, count)

        if distribution == "equal":
            random.shuffle(amounts)

        steps = []
        for i, amount in enumerate(amounts, 1):
            steps.append(
                ChallengeStep(
                    challenge_id=challenge_id,
                    goal_id=goal_id,
                    step_number=i,
                    planned_amount=amount,
                    status=StepStatus.pending,
                )
            )
        return steps


CHALLENGE_REGISTRY: dict[str, ChallengeStrategy] = {
    "envelope": EnvelopeChallengeStrategy(),
}


def get_challenge_strategy(challenge_type: str) -> ChallengeStrategy:
    strategy = CHALLENGE_REGISTRY.get(challenge_type)
    if not strategy:
        raise ValueError(f"Unknown challenge type: {challenge_type}")
    return strategy