"""The 7 planted stories: names and target numbers in one place.

The generators plant these, and tests/test_seed_stories.py checks them.
"""
CR = 10_000_000  # 1 crore in rupees
LAKH = 100_000

TOTAL_BOOKINGS = 850
TOTAL_LEADS = 4000

# Story 1: Tower B delay
DELAY_PROJECT, DELAY_TOWER, DELAY_MILESTONE = "Radhe Skyline", "Tower B", "slab_14"
DELAY_SLIP_DAYS = 23
DELAY_CONTRACTOR = "Sri Balaji Formworks"
DELAY_CAUSE = "Shuttering contractor Sri Balaji Formworks is short of labour; a steel delivery was also delayed."
DELAY_BLOCKED_BOOKINGS = 41
DELAY_BLOCKED_AMOUNT = 6.8 * CR

# Story 2: unhappy NRI buyer and his overloaded RM
KARTHIK = "Karthik Reddy"
KARTHIK_EMAIL_DAYS_AGO = [12, 8, 4]  # three emails about possession, none answered
KARTHIK_LAST_CONTACT_DAYS_AGO = 41
SNEHA = "Sneha Rao"
SNEHA_BUYERS = 62  # team average is about 38

# Story 3: stuck sales manager
ARJUN = "Arjun Varma"
ARJUN_BOOKINGS = 12
ARJUN_CONVERSION = 0.04  # team is about 11%
ARJUN_IDLE_BUDGETS_CR = [1.2, 1.4, 1.5, 1.5, 1.6, 1.6, 1.7, 1.7, 1.8]  # 9 idle negotiations, Rs 14 Cr

# Story 4: star channel partner
SKYWAY = "Skyway Realty Advisors"
SKYWAY_VILLA_SHARE = 0.31

# Story 5: ageing inventory
AGEING_PROJECT = "Radhe Greens"
AGEING_UNITS = 22

# Story 6: bank bottleneck
OVERDUE_BUYERS = 18
OVERDUE_AMOUNT = 4.2 * CR
BOTTLENECK_BANK = "Deccan National Bank"
BOTTLENECK_BUYERS = 6

# Story 7: interiors upsell
UPSELL_BUYERS = 63  # about Rs 9 Cr opportunity
