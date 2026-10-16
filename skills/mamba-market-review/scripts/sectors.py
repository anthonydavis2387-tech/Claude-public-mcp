"""The 11 GICS sectors, under their standard names, and the S&P 500 sector fund that measures each.

FMP labels sectors its own way ("Consumer Cyclical", "Consumer Defensive", "Financial Services", "Healthcare",
"Technology", "Basic Materials"). Every page uses the standard GICS names instead, the ones the user sees on S&P,
the WSJ and the SPDR sector funds. Map anything coming from FMP through gics() before it is saved or shown.
"""
FMP_TO_GICS = {
    'Technology': 'Information Technology', 'Financial Services': 'Financials', 'Healthcare': 'Health Care',
    'Consumer Cyclical': 'Consumer Discretionary', 'Consumer Defensive': 'Consumer Staples', 'Basic Materials': 'Materials',
}
# The official S&P 500 sector funds (Select Sector SPDRs), in the usual order.
SECTOR_FUNDS = [
    ('Information Technology', 'XLK'), ('Financials', 'XLF'), ('Health Care', 'XLV'), ('Consumer Discretionary', 'XLY'),
    ('Communication Services', 'XLC'), ('Industrials', 'XLI'), ('Consumer Staples', 'XLP'), ('Energy', 'XLE'),
    ('Utilities', 'XLU'), ('Real Estate', 'XLRE'), ('Materials', 'XLB'),
]
GICS_SECTORS = [s for s, _ in SECTOR_FUNDS]
FINANCIALS = ('Financials', 'Financial Services')
SENSITIVITY = {'Materials': 'Cyclical', 'Consumer Discretionary': 'Cyclical', 'Financials': 'Cyclical', 'Real Estate': 'Cyclical',
               'Communication Services': 'Sensitive', 'Energy': 'Sensitive', 'Industrials': 'Sensitive', 'Information Technology': 'Sensitive',
               'Consumer Staples': 'Defensive', 'Health Care': 'Defensive', 'Utilities': 'Defensive'}


def gics(name):
    """Standard GICS name for an FMP sector label (names already in GICS form pass through)."""
    return FMP_TO_GICS.get(name, name) if name else name
