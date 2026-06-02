from decimal import Decimal, ROUND_HALF_UP, getcontext

getcontext().prec = 28

ZERO = Decimal("0")
ONE = Decimal("1")
HUNDRED = Decimal("100")
TWELVE = Decimal("12")
MONEY_QUANT = Decimal("0.01")
PERCENT_QUANT = Decimal("0.01")


def to_decimal(value: Decimal | int | float | str) -> Decimal:
    decimal_value = value if isinstance(value, Decimal) else Decimal(str(value))
    if decimal_value < ZERO:
        raise ValueError("Invalid amount")
    return decimal_value


def quantize_money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def calculate_available_money(
    monthly_income: Decimal | int | float | str,
    monthly_expenses: Decimal | int | float | str,
    extra_income_amount: Decimal | int | float | str = ZERO,
) -> Decimal:
    income = to_decimal(monthly_income)
    expenses = to_decimal(monthly_expenses)
    extra = to_decimal(extra_income_amount)
    return quantize_money(income + extra - expenses)


def calculate_progress_percent(
    current_balance: Decimal | int | float | str,
    target_amount: Decimal | int | float | str,
) -> Decimal:
    current = to_decimal(current_balance)
    target = to_decimal(target_amount)
    if target <= ZERO:
        raise ValueError("Target amount must be greater than zero")
    percent = (current / target) * HUNDRED
    return min(percent, HUNDRED).quantize(PERCENT_QUANT, rounding=ROUND_HALF_UP)


def calculate_compound_future_value(
    current_balance: Decimal | int | float | str,
    monthly_investment: Decimal | int | float | str,
    annual_return_percent: Decimal | int | float | str,
    months: int,
) -> Decimal:
    current = to_decimal(current_balance)
    monthly = to_decimal(monthly_investment)
    annual_return = to_decimal(annual_return_percent)
    if months < 0:
        raise ValueError("Months cannot be negative")

    if months == 0:
        return quantize_money(current)

    monthly_rate = annual_return / HUNDRED / TWELVE
    if monthly_rate == ZERO:
        return quantize_money(current + monthly * months)

    growth_factor = (ONE + monthly_rate) ** months
    future_value = current * growth_factor + monthly * ((growth_factor - ONE) / monthly_rate)
    return quantize_money(future_value)


def calculate_total_invested(
    current_balance: Decimal | int | float | str,
    monthly_investment: Decimal | int | float | str,
    months: int,
) -> Decimal:
    current = to_decimal(current_balance)
    monthly = to_decimal(monthly_investment)
    if months < 0:
        raise ValueError("Months cannot be negative")
    return quantize_money(current + monthly * months)


def calculate_estimated_completion_months(
    current_balance: Decimal | int | float | str,
    target_amount: Decimal | int | float | str,
    monthly_investment: Decimal | int | float | str,
    annual_return_percent: Decimal | int | float | str,
    max_months: int = 600,
) -> int | None:
    current = to_decimal(current_balance)
    target = to_decimal(target_amount)
    monthly = to_decimal(monthly_investment)
    annual_return = to_decimal(annual_return_percent)

    if target <= ZERO:
        raise ValueError("Target amount must be greater than zero")
    if current >= target:
        return 0
    if monthly == ZERO and annual_return == ZERO:
        return None

    monthly_rate = annual_return / HUNDRED / TWELVE
    balance = current
    for month in range(1, max_months + 1):
        if monthly_rate > ZERO:
            balance = balance * (ONE + monthly_rate)
        balance += monthly
        if balance >= target:
            return month

    return None

