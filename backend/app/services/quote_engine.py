"""Quote engine: predefined question flows and premium calculation for insurance products."""
from typing import Any, Dict, List, Optional


class QuoteQuestion:
    def __init__(
        self,
        id: str,
        text: str,
        type: str = "choice",
        options: Optional[List[str]] = None,
    ):
        self.id = id
        self.text = text
        self.type = type
        self.options = options or []

    def to_dict(self) -> Dict[str, Any]:
        result = {"id": self.id, "text": self.text, "type": self.type}
        if self.options:
            result["options"] = self.options
        return result


class QuoteFlow:
    def __init__(self, flow_id: str, name: str, questions: List[QuoteQuestion]):
        self.flow_id = flow_id
        self.name = name
        self.questions = questions

    def to_dict(self) -> Dict[str, Any]:
        return {
            "flow_id": self.flow_id,
            "name": self.name,
            "questions": [q.to_dict() for q in self.questions],
        }


# ---------------------------------------------------------------------------
# Product flows
# ---------------------------------------------------------------------------

MOTOR_FLOW = QuoteFlow(
    flow_id="motor",
    name="Motor Insurance",
    questions=[
        QuoteQuestion(
            id="coverage_type",
            text="What type of coverage do you need?",
            options=["Comprehensive", "Third Party"],
        ),
        QuoteQuestion(
            id="vehicle_age",
            text="How old is your vehicle?",
            options=["Less than 3 years", "3-7 years", "More than 7 years"],
        ),
        QuoteQuestion(
            id="vehicle_value",
            text="What is the approximate value of your vehicle (ETB)?",
            options=["Under 500,000", "500,000 - 1,500,000", "Over 1,500,000"],
        ),
        QuoteQuestion(
            id="usage",
            text="How do you use your vehicle?",
            options=["Private", "Commercial"],
        ),
    ],
)

LIFE_FLOW = QuoteFlow(
    flow_id="life",
    name="Life Insurance",
    questions=[
        QuoteQuestion(
            id="age_group",
            text="What is your age group?",
            options=["18-30", "31-45", "46-60", "Over 60"],
        ),
        QuoteQuestion(
            id="sum_assured",
            text="How much coverage do you need (ETB)?",
            options=["100,000 - 500,000", "500,000 - 2,000,000", "Over 2,000,000"],
        ),
        QuoteQuestion(
            id="term",
            text="For how many years do you want coverage?",
            options=["5 years", "10 years", "15 years", "20 years"],
        ),
        QuoteQuestion(
            id="smoker",
            text="Do you smoke?",
            options=["Yes", "No"],
        ),
    ],
)

HEALTH_FLOW = QuoteFlow(
    flow_id="health",
    name="Health Insurance",
    questions=[
        QuoteQuestion(
            id="age_group",
            text="What is your age group?",
            options=["18-30", "31-45", "46-60", "Over 60"],
        ),
        QuoteQuestion(
            id="family_size",
            text="How many people will be covered?",
            options=["1 (Individual)", "2 (Couple)", "3-4 (Family)", "5+ (Extended Family)"],
        ),
        QuoteQuestion(
            id="coverage_level",
            text="What coverage level do you prefer?",
            options=["Basic", "Standard", "Premium"],
        ),
    ],
)

PROPERTY_FLOW = QuoteFlow(
    flow_id="property",
    name="Property Insurance",
    questions=[
        QuoteQuestion(
            id="property_type",
            text="What type of property are you insuring?",
            options=["House", "Apartment", "Office", "Warehouse"],
        ),
        QuoteQuestion(
            id="property_value",
            text="What is the estimated value of your property (ETB)?",
            options=["Under 2,000,000", "2,000,000 - 5,000,000", "Over 5,000,000"],
        ),
        QuoteQuestion(
            id="location",
            text="Where is the property located?",
            options=["Addis Ababa", "Other major city", "Rural area"],
        ),
    ],
)



TRAVEL_FLOW = QuoteFlow(
    flow_id="travel",
    name="Travel Insurance",
    questions=[
        QuoteQuestion(
            id="destination",
            text="Where are you traveling?",
            options=["Domestic (Ethiopia)", "Africa", "International"],
        ),
        QuoteQuestion(
            id="duration",
            text="How long is your trip?",
            options=["1-7 days", "8-30 days", "Over 30 days"],
        ),
        QuoteQuestion(
            id="travelers",
            text="How many travelers?",
            options=["1", "2", "3-4", "5+"],
        ),
    ],
)

FLOWS = {
    "motor": MOTOR_FLOW,
    "life": LIFE_FLOW,
    "health": HEALTH_FLOW,
    "property": PROPERTY_FLOW,
    "travel": TRAVEL_FLOW,
}


# ---------------------------------------------------------------------------
# Premium calculation
# ---------------------------------------------------------------------------

def _parse_value_range(value_str: str) -> float:
    """Extract a numeric value from a range string like '500,000 - 1,500,000'."""
    parts = value_str.replace(",", "").replace("ETB", "").strip()
    if " - " in parts:
        low, high = parts.split(" - ")
        return (float(low) + float(high)) / 2
    elif parts.startswith("Under "):
        return float(parts.replace("Under ", "")) * 0.7
    elif parts.startswith("Over "):
        return float(parts.replace("Over ", "")) * 1.3
    else:
        try:
            return float(parts)
        except ValueError:
            return 0


def calculate_motor_premium(answers: Dict[str, str]) -> Dict[str, Any]:
    """Calculate motor insurance premium."""
    coverage = answers.get("coverage_type", "Comprehensive")
    vehicle_age = answers.get("vehicle_age", "3-7 years")
    vehicle_value_str = answers.get("vehicle_value", "500,000 - 1,500,000")
    usage = answers.get("usage", "Private")

    # Base rate
    base_rate = 0.03 if coverage == "Comprehensive" else 0.015

    # Vehicle value
    vehicle_value = _parse_value_range(vehicle_value_str)

    # Age factor
    age_factors = {"Less than 3 years": 1.1, "3-7 years": 1.0, "More than 7 years": 0.9}
    age_factor = age_factors.get(vehicle_age, 1.0)

    # Usage factor
    usage_factor = 1.3 if usage == "Commercial" else 1.0

    # Calculate
    annual_premium = vehicle_value * base_rate * age_factor * usage_factor
    annual_premium = max(annual_premium, 3000)  # Minimum premium

    monthly_premium = annual_premium / 12

    return {
        "base_rate": f"{base_rate * 100:.1f}%",
        "vehicle_value": f"ETB {vehicle_value:,.0f}",
        "age_factor": age_factor,
        "usage_factor": usage_factor,
        "annual_premium": round(annual_premium, 2),
        "monthly_premium": round(monthly_premium, 2),
    }


def calculate_life_premium(answers: Dict[str, str]) -> Dict[str, Any]:
    """Calculate life insurance premium."""
    age_group = answers.get("age_group", "31-45")
    sum_assured_str = answers.get("sum_assured", "500,000 - 2,000,000")
    term = answers.get("term", "10 years")
    smoker = answers.get("smoker", "No")

    # Sum assured
    sum_assured = _parse_value_range(sum_assured_str)

    # Age factor
    age_factors = {"18-30": 0.8, "31-45": 1.0, "46-60": 1.4, "Over 60": 2.0}
    age_factor = age_factors.get(age_group, 1.0)

    # Term (years)
    term_years = int(term.replace(" years", ""))

    # Smoker factor
    smoker_factor = 1.5 if smoker == "Yes" else 1.0

    # Rate per 1000 sum assured per year
    base_rate_per_1000 = 2.5
    annual_premium = (sum_assured / 1000) * base_rate_per_1000 * age_factor * smoker_factor
    annual_premium = max(annual_premium, 2000)

    monthly_premium = annual_premium / 12

    return {
        "sum_assured": f"ETB {sum_assured:,.0f}",
        "term_years": term_years,
        "age_factor": age_factor,
        "smoker_factor": smoker_factor,
        "annual_premium": round(annual_premium, 2),
        "monthly_premium": round(monthly_premium, 2),
    }


def calculate_health_premium(answers: Dict[str, str]) -> Dict[str, Any]:
    """Calculate health insurance premium."""
    age_group = answers.get("age_group", "31-45")
    family_size_str = answers.get("family_size", "1 (Individual)")
    coverage_level = answers.get("coverage_level", "Standard")

    # Family size
    if "1" in family_size_str:
        family_count = 1
    elif "2" in family_size_str:
        family_count = 2
    elif "3-4" in family_size_str:
        family_count = 3.5
    else:
        family_count = 6

    # Coverage multiplier
    coverage_multipliers = {"Basic": 0.7, "Standard": 1.0, "Premium": 1.5}
    coverage_mult = coverage_multipliers.get(coverage_level, 1.0)

    # Age factor
    age_factors = {"18-30": 0.8, "31-45": 1.0, "46-60": 1.3, "Over 60": 1.8}
    age_factor = age_factors.get(age_group, 1.0)

    # Base per person
    base_per_person = 8000
    annual_premium = base_per_person * family_count * coverage_mult * age_factor
    annual_premium = max(annual_premium, 5000)

    monthly_premium = annual_premium / 12

    return {
        "family_count": int(family_count),
        "coverage_level": coverage_level,
        "age_factor": age_factor,
        "annual_premium": round(annual_premium, 2),
        "monthly_premium": round(monthly_premium, 2),
    }


def calculate_property_premium(answers: Dict[str, str]) -> Dict[str, Any]:
    """Calculate property insurance premium."""
    property_type = answers.get("property_type", "House")
    property_value_str = answers.get("property_value", "2,000,000 - 5,000,000")
    location = answers.get("location", "Addis Ababa")

    # Property value
    property_value = _parse_value_range(property_value_str)

    # Type factor
    type_factors = {"House": 1.0, "Apartment": 0.9, "Office": 1.1, "Warehouse": 1.3}
    type_factor = type_factors.get(property_type, 1.0)

    # Location factor
    location_factors = {"Addis Ababa": 1.0, "Other major city": 0.95, "Rural area": 0.85}
    location_factor = location_factors.get(location, 1.0)

    # Base rate
    base_rate = 0.002
    annual_premium = property_value * base_rate * type_factor * location_factor
    annual_premium = max(annual_premium, 2500)

    monthly_premium = annual_premium / 12

    return {
        "property_value": f"ETB {property_value:,.0f}",
        "property_type": property_type,
        "location": location,
        "annual_premium": round(annual_premium, 2),
        "monthly_premium": round(monthly_premium, 2),
    }


def calculate_travel_premium(answers: Dict[str, str]) -> Dict[str, Any]:
    """Calculate travel insurance premium."""
    destination = answers.get("destination", "International")
    duration_str = answers.get("duration", "8-30 days")
    travelers_str = answers.get("travelers", "1")

    # Duration (days)
    if "1-7" in duration_str:
        duration_days = 4
    elif "8-30" in duration_str:
        duration_days = 19
    else:
        duration_days = 45

    # Travelers
    if "1" == travelers_str:
        traveler_count = 1
    elif "2" == travelers_str:
        traveler_count = 2
    elif "3-4" in travelers_str:
        traveler_count = 3.5
    else:
        traveler_count = 6

    # Destination factor
    destination_factors = {"Domestic (Ethiopia)": 0.5, "Africa": 1.0, "International": 1.5}
    dest_factor = destination_factors.get(destination, 1.0)

    # Base per person per day
    base_per_day = 150
    total_premium = base_per_day * duration_days * traveler_count * dest_factor
    total_premium = max(total_premium, 500)

    return {
        "destination": destination,
        "duration_days": duration_days,
        "traveler_count": int(traveler_count),
        "total_premium": round(total_premium, 2),
    }


def calculate_quote(flow_id: str, answers: Dict[str, str]) -> Dict[str, Any]:
    """Calculate premium for a given flow and answers."""
    flow = FLOWS.get(flow_id)
    if not flow:
        raise ValueError(f"Unknown flow: {flow_id}")

    if flow_id == "motor":
        breakdown = calculate_motor_premium(answers)
        annual = breakdown["annual_premium"]
        monthly = breakdown["monthly_premium"]
    elif flow_id == "life":
        breakdown = calculate_life_premium(answers)
        annual = breakdown["annual_premium"]
        monthly = breakdown["monthly_premium"]
    elif flow_id == "health":
        breakdown = calculate_health_premium(answers)
        annual = breakdown["annual_premium"]
        monthly = breakdown["monthly_premium"]
    elif flow_id == "property":
        breakdown = calculate_property_premium(answers)
        annual = breakdown["annual_premium"]
        monthly = breakdown["monthly_premium"]
    elif flow_id == "travel":
        breakdown = calculate_travel_premium(answers)
        # Travel is a one-time premium
        annual = breakdown["total_premium"]
        monthly = breakdown["total_premium"]
    else:
        raise ValueError(f"Unsupported flow: {flow_id}")

    return {
        "product_name": flow.name,
        "answers": answers,
        "premium_monthly": monthly,
        "premium_annual": annual,
        "breakdown": breakdown,
    }
