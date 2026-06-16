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

ACCOUNT_TYPES = ["Classic", "Prime", "Islamic"]
BOOK_TYPES = ["A-Book", "B-Book", "M-Book"]

REGIONS = ["GCC", "MENA", "Africa", "Europe", "South Asia", "SE Asia"]

COUNTRY_TO_REGION = {
    "UAE": "GCC", "Saudi Arabia": "GCC", "Kuwait": "GCC",
    "Qatar": "GCC", "Bahrain": "GCC",
    "Egypt": "MENA", "Jordan": "MENA", "Lebanon": "MENA",
    "Iraq": "MENA", "Morocco": "MENA",
    "Nigeria": "Africa", "Kenya": "Africa", "South Africa": "Africa",
    "Ghana": "Africa", "Tanzania": "Africa",
    "UK": "Europe", "Germany": "Europe", "France": "Europe",
    "Spain": "Europe", "Italy": "Europe",
    "India": "South Asia", "Pakistan": "South Asia", "Bangladesh": "South Asia",
    "Sri Lanka": "South Asia", "Nepal": "South Asia",
    "Malaysia": "SE Asia", "Indonesia": "SE Asia", "Thailand": "SE Asia",
    "Philippines": "SE Asia", "Vietnam": "SE Asia",
}

REGIONAL_MANAGERS = {
    "GCC":        "Omar Al-Mansouri",
    "MENA":       "Nadia Hassan",
    "Africa":     "Emmanuel Okafor",
    "Europe":     "Sophie Laurent",
    "South Asia": "Rajesh Kumar",
    "SE Asia":    "Lin Wei",
}

SALES_DIRECTORS = {
    "GCC":        "Michael Thompson",
    "MENA":       "Michael Thompson",
    "Africa":     "Rebecca Osei",
    "Europe":     "Rebecca Osei",
    "South Asia": "Chen Xiaoming",
    "SE Asia":    "Chen Xiaoming",
}

BUSINESS_DEVELOPERS = [
    "Alex Turner", "Layla Al-Farsi", "Marco Rossi", "Zara Ahmed",
    "Tom Bradley", "Mia Kowalski", "Hassan Malik", "Ingrid Svensson",
]


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
        region = COUNTRY_TO_REGION[country]
        regional_manager = REGIONAL_MANAGERS[region]
        sales_director = SALES_DIRECTORS[region]
        account_manager = np.random.choice(ACCOUNT_MANAGERS)
        business_developer = np.random.choice(BUSINESS_DEVELOPERS)
        sales_owner = account_manager  # AM is the primary relationship owner
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

        # --- NEW FIELDS: Book-type aware revenue ---
        # swap_revenue: all book types earn swap from client overnight positions
        if book_type == "A-Book":
            swap_revenue = round(max(0, np.random.lognormal(
                mean=np.log(max(current_equity * 0.002, 0.01)), sigma=0.5
            )), 2)
        elif book_type == "B-Book":
            swap_revenue = round(max(0, np.random.lognormal(
                mean=np.log(max(current_equity * 0.0015, 0.01)), sigma=0.5
            )), 2)
        else:  # M-Book
            swap_revenue = round(max(0, np.random.lognormal(
                mean=np.log(max(current_equity * 0.001, 0.01)), sigma=0.5
            )), 2)

        # commission_revenue: A-Book = higher rate, B-Book = lower (spread markup), M-Book = mid
        if book_type == "A-Book":
            commission_revenue = round(
                trading_volume_last_30d * np.random.uniform(0.0001, 0.0005), 2
            )
        elif book_type == "B-Book":
            commission_revenue = round(
                trading_volume_last_30d * np.random.uniform(0.00005, 0.0002), 2
            )
        else:  # M-Book
            commission_revenue = round(
                trading_volume_last_30d * np.random.uniform(0.00005, 0.0002), 2
            )

        # captured_client_losses: B-Book/M-Book only
        # 75% of B-Book clients lose money (positive = profit for company)
        # 25% win (negative = cost to company)
        if book_type == "B-Book":
            if np.random.random() < 0.75:
                # Client loses — positive captured losses
                captured_client_losses = round(
                    current_equity * np.random.uniform(0.01, 0.15), 2
                )
            else:
                # Client wins — negative (cost to company)
                captured_client_losses = round(
                    -current_equity * np.random.uniform(0.005, 0.08), 2
                )
        elif book_type == "M-Book":
            # M-Book: 60% of B-Book amount
            if np.random.random() < 0.75:
                captured_client_losses = round(
                    current_equity * np.random.uniform(0.006, 0.09), 2
                )
            else:
                captured_client_losses = round(
                    -current_equity * np.random.uniform(0.003, 0.048), 2
                )
        else:  # A-Book
            captured_client_losses = 0.0

        # net_company_pnl: Book-aware total
        # A-Book: all fee-based (spread IS a client-facing charge)
        # B-Book: position P&L model — spread not included
        # M-Book: partial position P&L model — spread not included
        if book_type == "A-Book":
            net_company_pnl = round(
                spread_commission_revenue + commission_revenue + swap_revenue, 2
            )
        elif book_type == "B-Book":
            net_company_pnl = round(
                captured_client_losses + commission_revenue + swap_revenue, 2
            )
        else:  # M-Book
            net_company_pnl = round(
                0.6 * captured_client_losses + commission_revenue + swap_revenue, 2
            )

        # client_tenure_days: int, lognormal to get range 30-1825 days
        raw_tenure = np.random.lognormal(mean=6.0, sigma=0.8)
        client_tenure_days = int(np.clip(raw_tenure, 30, 1825))

        # total_deposits_count: number_of_redeposits + 1 (or random 1-25)
        total_deposits_count = number_of_redeposits + 1

        # equity_30d_ago: current_equity * uniform(0.85, 1.25)
        equity_30d_ago = round(current_equity * np.random.uniform(0.85, 1.25), 2)

        # volume_90d_ago: trading_volume_last_30d * uniform(0.4, 2.2)
        volume_90d_ago = round(trading_volume_last_30d * np.random.uniform(0.4, 2.2), 2)

        # account_status: Active/Dormant/Inactive based on login_days_ago
        if login_days_ago < 30:
            account_status = "Active"
        elif login_days_ago <= 90:
            account_status = "Dormant"
        else:
            account_status = "Inactive"

        records.append({
            # Identity
            "client_id": client_id,
            "client_name": client_name,
            "country": country,
            "region": region,
            "regional_manager": regional_manager,
            "sales_director": sales_director,
            "account_manager": account_manager,
            "business_developer": business_developer,
            "sales_owner": sales_owner,
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
            # New Phase 2 fields
            "swap_revenue": swap_revenue,
            "commission_revenue": commission_revenue,
            "captured_client_losses": captured_client_losses,
            "net_company_pnl": net_company_pnl,
            "client_tenure_days": client_tenure_days,
            "total_deposits_count": total_deposits_count,
            "equity_30d_ago": equity_30d_ago,
            "volume_90d_ago": volume_90d_ago,
            "account_status": account_status,
        })

    return pd.DataFrame(records)
