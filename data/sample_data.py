# data/sample_data.py
# This file generates 300 fake client records for the platform.
# We use the Faker library to create realistic-looking names, countries, etc.

import pandas as pd
import numpy as np
from faker import Faker

fake = Faker()

# Seed for reproducibility — same fake data every time
np.random.seed(42)
Faker.seed(42)

# --- Reference lists ---
COUNTRIES = [
    "UAE", "Saudi Arabia", "Kuwait", "Qatar", "Bahrain",
    "Egypt", "Jordan", "Lebanon", "Iraq", "Morocco",
    "Nigeria", "Kenya", "South Africa", "Ghana", "Tanzania",
    "UK", "Germany", "France", "Spain", "Italy",
    "India", "Pakistan", "Bangladesh", "Sri Lanka", "Nepal",
    "Malaysia", "Indonesia", "Thailand", "Philippines", "Vietnam",
]

ACCOUNT_MANAGERS = [
    "Sarah Johnson", "Mohammed Al-Rashid", "David Chen",
    "Priya Sharma", "Ahmed Hassan", "Elena Volkov",
    "James Williams", "Fatima Al-Zahra", "Carlos Rivera",
    "Aisha Okonkwo",
]

IB_NAMES = [
    "AlphaFX Partners", "Gulf Traders IB", "Asia Markets IB",
    "ProSignals IB", "GoldBridge IB", "DirectFX IB",
    "NileFX IB", "EastWest IB", "Premier IB Group",
    "SunriseFX IB", "No IB",
]

ACCOUNT_TYPES = ["Standard", "ECN", "VIP", "Islamic", "Pro", "Micro"]
BOOK_TYPES = ["A-Book", "B-Book", "M-Book"]


def generate_clients(n: int = 300) -> pd.DataFrame:
    """
    Generate n fake client records with all required fields.
    Returns a pandas DataFrame.
    """
    records = []

    for i in range(1, n + 1):
        # --- Basic identifiers ---
        client_id = f"CR{10000 + i}"
        client_name = fake.name()
        country = np.random.choice(COUNTRIES, p=None)
        account_manager = np.random.choice(ACCOUNT_MANAGERS)
        ib_name = np.random.choice(IB_NAMES)
        account_type = np.random.choice(ACCOUNT_TYPES)
        book_type = np.random.choice(BOOK_TYPES, p=[0.3, 0.5, 0.2])

        # --- Financial fields ---
        lifetime_deposits = round(np.random.lognormal(mean=8.5, sigma=1.5), 2)
        withdrawals_total = round(lifetime_deposits * np.random.uniform(0.1, 0.6), 2)
        net_deposits = round(lifetime_deposits - withdrawals_total, 2)
        current_equity = round(net_deposits * np.random.uniform(0.3, 1.8), 2)

        # --- Activity timing (days ago) ---
        last_deposit_days_ago = int(np.random.choice(
            [7, 14, 30, 60, 90, 120, 180, 270, 365],
            p=[0.05, 0.08, 0.15, 0.18, 0.17, 0.13, 0.1, 0.08, 0.06]
        ))
        last_withdrawal_days_ago = int(np.random.choice(
            [0, 7, 14, 30, 60, 90, 180, 365],
            p=[0.05, 0.08, 0.10, 0.17, 0.20, 0.18, 0.12, 0.10]
        ))
        login_days_ago = int(np.random.choice(
            [0, 1, 3, 7, 14, 30, 60, 90],
            p=[0.10, 0.15, 0.18, 0.17, 0.14, 0.12, 0.08, 0.06]
        ))

        # --- Volume and withdrawal data ---
        withdrawal_amount_last_30d = round(
            current_equity * np.random.uniform(0, 0.5)
            if last_withdrawal_days_ago <= 30 else 0, 2
        )
        trading_volume_last_30d = round(np.random.lognormal(mean=6, sigma=2), 2)
        # Previous volume can be higher or lower (trend signal)
        trading_volume_previous_30d = round(
            trading_volume_last_30d * np.random.uniform(0.3, 2.5), 2
        )

        # --- Engagement and service ---
        number_of_redeposits = int(np.random.choice(
            [0, 1, 2, 3, 5, 8, 12, 20],
            p=[0.10, 0.15, 0.20, 0.20, 0.15, 0.10, 0.07, 0.03]
        ))
        complaints_last_30d = int(np.random.choice(
            [0, 0, 0, 1, 2, 3],
            p=[0.60, 0.15, 0.10, 0.09, 0.04, 0.02]
        ))
        open_tickets = int(np.random.choice(
            [0, 0, 1, 2, 3],
            p=[0.55, 0.20, 0.14, 0.07, 0.04]
        ))

        # --- Revenue ---
        company_pnl_from_client = round(
            np.random.normal(loc=current_equity * 0.05, scale=current_equity * 0.15), 2
        )
        spread_commission_revenue = round(
            trading_volume_last_30d * np.random.uniform(0.0001, 0.0008), 2
        )

        records.append({
            "client_id": client_id,
            "client_name": client_name,
            "country": country,
            "account_manager": account_manager,
            "ib_name": ib_name,
            "account_type": account_type,
            "book_type": book_type,
            "lifetime_deposits": lifetime_deposits,
            "net_deposits": net_deposits,
            "current_equity": current_equity,
            "last_deposit_days_ago": last_deposit_days_ago,
            "last_withdrawal_days_ago": last_withdrawal_days_ago,
            "withdrawal_amount_last_30d": withdrawal_amount_last_30d,
            "trading_volume_last_30d": trading_volume_last_30d,
            "trading_volume_previous_30d": trading_volume_previous_30d,
            "login_days_ago": login_days_ago,
            "number_of_redeposits": number_of_redeposits,
            "complaints_last_30d": complaints_last_30d,
            "open_tickets": open_tickets,
            "company_pnl_from_client": company_pnl_from_client,
            "spread_commission_revenue": spread_commission_revenue,
        })

    return pd.DataFrame(records)
