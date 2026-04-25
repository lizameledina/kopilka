import pytest
from services.distribution_strategies import (
    EqualStrategy,
    RandomStrategy,
    AscendingStrategy,
    DescendingStrategy,
    get_strategy,
    STRATEGY_REGISTRY,
)


class TestEqualStrategy:
    def test_basic_distribution(self):
        s = EqualStrategy()
        amounts = s.distribute(10000, 5)
        assert len(amounts) == 5
        assert sum(amounts) == 10000

    def test_remainder_distributed(self):
        s = EqualStrategy()
        amounts = s.distribute(10003, 5)
        assert sum(amounts) == 10003
        assert min(amounts) >= max(amounts) - 1

    def test_single_step(self):
        s = EqualStrategy()
        amounts = s.distribute(5000, 1)
        assert amounts == [5000]

    def test_many_steps(self):
        s = EqualStrategy()
        amounts = s.distribute(10000, 500)
        assert len(amounts) == 500
        assert sum(amounts) == 10000

    def test_all_positive(self):
        s = EqualStrategy()
        for total in [100, 1000, 50000]:
            for count in [5, 10, 100]:
                amounts = s.distribute(total, count)
                assert all(a > 0 for a in amounts), f"Zero/negative amount for total={total} count={count}"


class TestRandomStrategy:
    def test_sum_matches(self):
        s = RandomStrategy()
        amounts = s.distribute(10000, 5)
        assert sum(amounts) == 10000

    def test_all_positive(self):
        s = RandomStrategy()
        amounts = s.distribute(10000, 50)
        assert all(a > 0 for a in amounts)

    def test_single_step(self):
        s = RandomStrategy()
        amounts = s.distribute(5000, 1)
        assert amounts == [5000]


class TestAscendingStrategy:
    def test_ascending_order(self):
        s = AscendingStrategy()
        amounts = s.distribute(10000, 5)
        assert sum(amounts) == 10000
        for i in range(len(amounts) - 1):
            assert amounts[i] <= amounts[i + 1] or amounts[i] == amounts[i + 1] - 1

    def test_all_positive(self):
        s = AscendingStrategy()
        amounts = s.distribute(100, 10)
        assert all(a > 0 for a in amounts)
        assert sum(amounts) == 100


class TestDescendingStrategy:
    def test_descending_order(self):
        s = DescendingStrategy()
        amounts = s.distribute(10000, 5)
        assert sum(amounts) == 10000
        for i in range(len(amounts) - 1):
            assert amounts[i] >= amounts[i + 1] or amounts[i] == amounts[i + 1] + 1

    def test_all_positive(self):
        s = DescendingStrategy()
        amounts = s.distribute(100, 10)
        assert all(a > 0 for a in amounts)
        assert sum(amounts) == 100


class TestGetStrategy:
    def test_all_strategies_registered(self):
        for name in ["equal", "random", "ascending", "descending"]:
            s = get_strategy(name)
            assert s is not None

    def test_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown distribution strategy"):
            get_strategy("nonexistent")

    def test_registry_types(self):
        assert isinstance(STRATEGY_REGISTRY["equal"], EqualStrategy)
        assert isinstance(STRATEGY_REGISTRY["random"], RandomStrategy)
        assert isinstance(STRATEGY_REGISTRY["ascending"], AscendingStrategy)
        assert isinstance(STRATEGY_REGISTRY["descending"], DescendingStrategy)