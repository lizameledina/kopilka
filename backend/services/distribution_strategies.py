import abc
import random


class DistributionStrategy(abc.ABC):
    @abc.abstractmethod
    def distribute(self, total: int, count: int) -> list[int]:
        raise NotImplementedError


class EqualStrategy(DistributionStrategy):
    def distribute(self, total: int, count: int) -> list[int]:
        base = total // count
        remainder = total % count
        amounts = [base] * count
        for i in range(remainder):
            amounts[i] += 1
        return amounts


class RandomStrategy(DistributionStrategy):
    def distribute(self, total: int, count: int) -> list[int]:
        raw = [random.randint(1, total) for _ in range(count)]
        total_raw = sum(raw)
        amounts = [max(1, round(r * total / total_raw)) for r in raw]

        diff = total - sum(amounts)
        for i in range(abs(diff)):
            idx = i % count
            if diff > 0:
                amounts[idx] += 1
            elif amounts[idx] > 1:
                amounts[idx] -= 1

        while sum(amounts) != total:
            idx = random.randint(0, count - 1)
            if sum(amounts) > total and amounts[idx] > 1:
                amounts[idx] -= 1
            elif sum(amounts) < total:
                amounts[idx] += 1

        return amounts


class AscendingStrategy(DistributionStrategy):
    def distribute(self, total: int, count: int) -> list[int]:
        weights = list(range(1, count + 1))
        total_weight = sum(weights)
        amounts = [max(1, round(w * total / total_weight)) for w in weights]

        diff = total - sum(amounts)
        for i in range(abs(diff)):
            idx = i % count
            if diff > 0:
                amounts[idx] += 1
            elif amounts[idx] > 1:
                amounts[idx] -= 1

        while sum(amounts) != total:
            idx = random.randint(0, count - 1)
            if sum(amounts) > total and amounts[idx] > 1:
                amounts[idx] -= 1
            elif sum(amounts) < total:
                amounts[idx] += 1

        return amounts


class DescendingStrategy(DistributionStrategy):
    def distribute(self, total: int, count: int) -> list[int]:
        weights = list(range(count, 0, -1))
        total_weight = sum(weights)
        amounts = [max(1, round(w * total / total_weight)) for w in weights]

        diff = total - sum(amounts)
        for i in range(abs(diff)):
            idx = i % count
            if diff > 0:
                amounts[idx] += 1
            elif amounts[idx] > 1:
                amounts[idx] -= 1

        while sum(amounts) != total:
            idx = random.randint(0, count - 1)
            if sum(amounts) > total and amounts[idx] > 1:
                amounts[idx] -= 1
            elif sum(amounts) < total:
                amounts[idx] += 1

        return amounts


STRATEGY_REGISTRY: dict[str, DistributionStrategy] = {
    "equal": EqualStrategy(),
    "random": RandomStrategy(),
    "ascending": AscendingStrategy(),
    "descending": DescendingStrategy(),
}


def get_strategy(name: str) -> DistributionStrategy:
    strategy = STRATEGY_REGISTRY.get(name)
    if not strategy:
        raise ValueError(f"Unknown distribution strategy: {name}")
    return strategy