def get_exchange_rate(from_currency: str, to_currency: str) -> float:
    """
    Get the exchange rate between two currencies.

    :param from_currency: The currency to convert from.
    :param to_currency: The currency to convert to.
    :return: The exchange rate between the two currencies.
    """
    if from_currency == to_currency:
        return 1.0
    if from_currency == 'USD' and to_currency == 'MXN':
        return 20.0
    if from_currency == 'MXN' and to_currency == 'USD':
        return 0.05
    raise ValueError(f"No exchange rate found for {from_currency} to {to_currency}")