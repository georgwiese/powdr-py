from powdr import Circuit, Fixed, Witness, star, FixedColumn, WitnessColumn, PIL

def fib() -> PIL:
    is_last = FixedColumn("is_last", star([0]) + [1])
    x = WitnessColumn("x")
    y = WitnessColumn("y")

    yield is_last * (y.n - 1) == 0
    yield is_last * (x.n - 1) == 0
    yield (1 - is_last) * (x.n - y) == 0
    yield (1 - is_last) * (y.n - (x + y)) == 0


class FibCircuit(Circuit):

    __name__ = "fib_via_circuit"

    def __init__(self):
        self.x = Witness()
        self.y = Witness()
        self.is_last = Fixed(star([0]) + [1])

    def __call__(self) -> PIL:
        yield self.is_last * (self.x.n - 1) == 0
        yield self.is_last * (self.x.n - 1) == 0
        yield (1 - self.is_last) * (self.x.n - self.y) == 0
        yield (1 - self.is_last) * (self.y.n - (self.x + self.y)) == 0