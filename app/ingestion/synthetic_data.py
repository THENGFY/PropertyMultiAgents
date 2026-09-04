import random
from datetime import date, timedelta


class CEASyntheticGenerator:
    """Generates realistic synthetic CEA datasets mimicking data.gov.sg structures."""

    AGENCIES = [
        {"licence_no": "L3008022J", "agency_name": "PROPEXCELLENCE REALTY PTE LTD"},
        {"licence_no": "L3002382K", "agency_name": "ERA REALTY NETWORK PTE LTD"},
        {"licence_no": "L3008899K", "agency_name": "HUTTONS ASIA PTE LTD"},
        {"licence_no": "L3009740K", "agency_name": "ORANGETEE & TIE PTE LTD"},
        {"licence_no": "L3001538F", "agency_name": "SRI PTE. LTD."},
    ]

    FIRST_NAMES = [
        "Marcus", "Wei Ming", "Sherlyn", "Desmond", "Cheryl", "Kelvin", "Fiona", 
        "Benjamin", "Rachel", "Darren", "Grace", "Alvin", "Valerie", "Clarence", 
        "Jolene", "Nicholas", "Amanda", "Bryan", "Eileen", "Jonathan", "Samantha",
        "Leon", "Melissa", "Eugene", "Hui Min", "Kenneth", "Chloe", "Raymond"
    ]

    LAST_NAMES = [
        "Tan", "Lim", "Lee", "Ng", "Ong", "Wong", "Goh", "Chua", "Chan", "Koh", 
        "Teo", "Ang", "Yeo", "Tay", "Ho", "Low", "Sim", "Chia", "Tan", "Lau"
    ]

    PROPERTY_TYPES = [
        "CONDOMINIUM_APARTMENTS",
        "HDB_4_ROOM",
        "HDB_5_ROOM",
        "EXECUTIVE_CONDOMINIUM",
        "TERRACE_HOUSE",
        "SEMI_DETACHED",
        "GOOD_CLASS_BUNGALOW",
        "COMMERCIAL_OFFICE",
    ]

    DISTRICTS = [f"D{str(i).zfill(2)}" for i in range(1, 29)]

    TOWNS = [
        "BISHAN", "BEDOK", "TAMPINES", "JURONG_EAST", "TOA_PAYOH", 
        "ORCHARD", "BUKIT_TIMAH", "QUEENSTOWN", "ANG_MO_KIO", "PUNGGOL", "SENGKANG"
    ]

    @classmethod
    def generate_agents(cls, count: int = 100, seed: int = 42) -> list[dict]:
        rng = random.Random(seed)
        agents = []
        used_reg_nos = set()

        for i in range(count):
            # Generate unique CEA Reg No: R followed by 7 digits and 1 uppercase letter
            while True:
                num = f"{rng.randint(100000, 999999):06d}"
                letter = rng.choice("ABCDEFGHJKLMNPQRSTUVWXYZ")
                reg_no = f"R0{num}{letter}"
                if reg_no not in used_reg_nos:
                    used_reg_nos.add(reg_no)
                    break

            agency = rng.choice(cls.AGENCIES)
            first = rng.choice(cls.FIRST_NAMES)
            last = rng.choice(cls.LAST_NAMES)
            full_name = f"{last} {first}"

            start_days_ago = rng.randint(365 * 2, 365 * 10)
            start_date = date.today() - timedelta(days=start_days_ago)
            end_date = start_date + timedelta(days=365 * 12)

            contact = f"+65 {rng.choice(['8', '9'])}{rng.randint(1000000, 9999999)}"

            agents.append({
                "cea_reg_no": reg_no,
                "agent_name": full_name,
                "agency_licence_no": agency["licence_no"],
                "agency_name": agency["agency_name"],
                "contact_number": contact,
                "status": "ACTIVE",
                "registration_start_date": start_date.isoformat(),
                "registration_end_date": end_date.isoformat(),
            })

        return agents

    @classmethod
    def generate_transactions(
        cls, 
        agents: list[dict], 
        ref_date: date | None = None, 
        tx_per_agent_range: tuple[int, int] = (2, 45),
        seed: int = 42
    ) -> list[dict]:
        rng = random.Random(seed)
        ref_date = ref_date or date.today()
        transactions = []
        tx_counter = 100000

        # Power law distribution: top 10% agents get 50% of transactions
        for i, agent in enumerate(agents):
            # Deterministic tiering
            if i < len(agents) * 0.05:  # Super top tier
                num_tx = rng.randint(50, 120)
            elif i < len(agents) * 0.20:  # High performers
                num_tx = rng.randint(25, 50)
            elif i < len(agents) * 0.60:  # Mid tier
                num_tx = rng.randint(8, 24)
            else:  # Long tail
                num_tx = rng.randint(1, 7)

            for _ in range(num_tx):
                tx_counter += 1
                days_offset = rng.randint(0, 500)  # Some inside T12M (<365 days), some older
                tx_date = ref_date - timedelta(days=days_offset)

                # Segment weightings
                seg_roll = rng.random()
                if seg_roll < 0.25:
                    tx_type = "NEW_SALE"
                elif seg_roll < 0.65:
                    tx_type = "RESALE"
                else:
                    tx_type = "RENTAL"

                prop_type = rng.choice(cls.PROPERTY_TYPES)
                # Map property category
                if "HDB" in prop_type:
                    prop_cat = "HDB"
                elif any(k in prop_type for k in ["TERRACE", "SEMI_DETACHED", "BUNGALOW", "LANDED"]):
                    prop_cat = "LANDED"
                elif "COMMERCIAL" in prop_type:
                    prop_cat = "COMMERCIAL"
                else:
                    prop_cat = "CONDO_APT"

                district = rng.choice(cls.DISTRICTS)
                town = rng.choice(cls.TOWNS)

                transactions.append({
                    "transaction_ref": f"TX-{tx_date.strftime('%Y%m')}-{tx_counter}",
                    "cea_reg_no": agent["cea_reg_no"],
                    "transaction_date": tx_date.isoformat(),
                    "property_type": prop_type,
                    "property_category": prop_cat,
                    "transaction_type": tx_type,
                    "district": district,
                    "town": town,
                })

        return transactions
