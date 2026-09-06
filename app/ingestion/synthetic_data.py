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

    @classmethod
    def generate_hdb_resale_and_mop(cls, count: int = 150, seed: int = 42) -> list[dict]:
        """Generates realistic HDB resale transaction and 5-Year MOP cluster records."""
        rng = random.Random(seed)
        hdb_records = []
        flat_types = ["3 ROOM", "4 ROOM", "5 ROOM", "EXECUTIVE"]
        current_year = date.today().year

        for i in range(count):
            town = rng.choice(cls.TOWNS)
            flat_type = rng.choice(flat_types)
            block = f"{rng.randint(100, 999)}{rng.choice(['', 'A', 'B', 'C'])}"
            street = f"{town} ST {rng.randint(11, 99)}"
            # Completion year between 5 to 30 years ago, with strong clustering around 5 years ago (MOP cohort)
            completion_year = current_year - rng.choice([5, 5, 5, 6, 7, 10, 15, 20, 25])
            mop_year = completion_year + 5
            is_mop_cohort = (mop_year >= current_year - 1 and mop_year <= current_year + 1)

            sqft = rng.randint(700, 1400) if "EXECUTIVE" in flat_type or "5" in flat_type else rng.randint(600, 950)
            resale_price = rng.randint(420000, 1150000)
            psf = round(resale_price / (sqft if sqft > 0 else 850), 2)
            month_offset = rng.randint(0, 12)
            tx_month = (date.today() - timedelta(days=month_offset * 30)).strftime("%Y-%m")

            hdb_records.append({
                "month": tx_month,
                "town": town,
                "flat_type": flat_type,
                "block": block,
                "street_name": street,
                "storey_range": f"{rng.randint(1, 10):02d} TO {rng.randint(11, 20):02d}",
                "floor_area_sqm": round(sqft * 0.092903, 1),
                "flat_model": "Model A",
                "lease_commence_date": completion_year,
                "remaining_lease": f"{99 - (current_year - completion_year)} years",
                "resale_price": resale_price,
                "psf": psf,
                "mop_year": mop_year,
                "is_mop_upgrader_cohort": is_mop_cohort,
                "estimated_units_in_cluster": rng.randint(80, 240),
            })

        return hdb_records

    @classmethod
    def generate_ura_caveats(cls, count: int = 150, seed: int = 42) -> list[dict]:
        """Generates realistic URA private residential caveats and developer sales."""
        rng = random.Random(seed)
        ura_records = []
        projects = [
            ("NORWOOD GRAND", "D25", "WOODLANDS", "OCR"),
            ("THE CHUAN PARK", "D19", "SERANGOON", "OCR"),
            ("GRAND DUNMAN", "D15", "MARINE PARADE", "RCR"),
            ("PINETREE HILL", "D21", "BUKIT TIMAH", "RCR"),
            ("MIDTOWN MODERN", "D07", "BUGIS", "CCR"),
            ("WATEN HILL RESIDENCES", "D10", "BUKIT TIMAH", "CCR"),
        ]

        for i in range(count):
            proj_name, district, town, region = rng.choice(projects)
            days_ago = rng.randint(0, 365)
            contract_date = date.today() - timedelta(days=days_ago)
            area_sqft = rng.randint(480, 2200)
            base_psf = 2900 if region == "CCR" else (2400 if region == "RCR" else 1950)
            psf = base_psf + rng.randint(-200, 350)
            transacted_price = psf * area_sqft

            ura_records.append({
                "project_name": proj_name,
                "district": district,
                "town": town,
                "market_segment": region,
                "contract_date": contract_date.isoformat(),
                "area_sqft": area_sqft,
                "unit_price_psf": psf,
                "transacted_price": transacted_price,
                "property_type": "CONDOMINIUM",
                "type_of_sale": rng.choice(["NEW_SALE", "RESALE", "SUB_SALE"]),
            })

        return ura_records

    @classmethod
    def generate_geospatial_benchmarks(cls, count: int = 50, seed: int = 42) -> list[dict]:
        """Generates spatial proximity indices and 1km/2km school catchments."""
        rng = random.Random(seed)
        benchmarks = []
        top_schools = [
            "Nanyang Primary School", "Tao Nan School", "Anglo-Chinese School (Primary)",
            "Raffles Girls' Primary School", "Catholic High School (Primary)", "Henry Park Primary School"
        ]

        for i in range(count):
            district = rng.choice(cls.DISTRICTS)
            town = rng.choice(cls.TOWNS)
            school = rng.choice(top_schools)
            mrt_dist_m = rng.randint(120, 1100)
            school_dist_km = round(rng.uniform(0.3, 2.5), 2)

            benchmarks.append({
                "district": district,
                "town": town,
                "nearest_mrt": f"{town} MRT",
                "mrt_distance_meters": mrt_dist_m,
                "nearest_top_school": school,
                "school_distance_km": school_dist_km,
                "within_1km_school_radius": school_dist_km <= 1.0,
                "within_2km_school_radius": school_dist_km <= 2.0,
                "transit_score": max(10, min(100, 100 - (mrt_dist_m // 15))),
            })

        return benchmarks

