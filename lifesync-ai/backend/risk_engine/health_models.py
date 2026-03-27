"""Validated health calculation functions with academic paper references.

Each function implements a well-known clinical or physiological formula
and includes the original paper DOI in its docstring.
"""

import math
from typing import Literal


def harris_benedict_bmr(
    weight_kg: float,
    height_cm: float,
    age: int,
    sex: Literal["male", "female"],
) -> float:
    """Calculate Basal Metabolic Rate using the Harris-Benedict equation.

    Formula (original 1918, revised 1984 by Roza & Shizgal):
        Male:   BMR = 88.362 + (13.397 * W) + (4.799 * H) - (5.677 * A)
        Female: BMR = 447.593 + (9.247 * W) + (3.098 * H) - (4.330 * A)

    Reference:
        Harris JA, Benedict FG. A Biometric Study of Human Basal Metabolism.
        Proc Natl Acad Sci USA. 1918;4(12):370-373.
        DOI: 10.1073/pnas.4.12.370

    Args:
        weight_kg: Body weight in kilograms.
        height_cm: Height in centimeters.
        age: Age in years.
        sex: Biological sex, either "male" or "female".

    Returns:
        BMR in kcal/day.

    Raises:
        ValueError: If any input is non-positive or sex is invalid.
    """
    if weight_kg <= 0 or height_cm <= 0 or age <= 0:
        raise ValueError("weight_kg, height_cm, and age must be positive.")

    if sex == "male":
        return 88.362 + (13.397 * weight_kg) + (4.799 * height_cm) - (5.677 * age)
    elif sex == "female":
        return 447.593 + (9.247 * weight_kg) + (3.098 * height_cm) - (4.330 * age)
    else:
        raise ValueError(f"sex must be 'male' or 'female', got '{sex}'.")


def mifflin_st_jeor_bmr(
    weight_kg: float,
    height_cm: float,
    age: int,
    sex: Literal["male", "female"],
) -> float:
    """Calculate Basal Metabolic Rate using the Mifflin-St Jeor equation.

    Considered more accurate than Harris-Benedict for modern populations.

    Formula:
        Male:   BMR = (10 * W) + (6.25 * H) - (5 * A) + 5
        Female: BMR = (10 * W) + (6.25 * H) - (5 * A) - 161

    Reference:
        Mifflin MD, St Jeor ST, Hill LA, et al. A new predictive equation
        for resting energy expenditure in healthy individuals.
        Am J Clin Nutr. 1990;51(2):241-247.
        DOI: 10.1093/ajcn/51.2.241

    Args:
        weight_kg: Body weight in kilograms.
        height_cm: Height in centimeters.
        age: Age in years.
        sex: Biological sex, either "male" or "female".

    Returns:
        BMR in kcal/day.

    Raises:
        ValueError: If any input is non-positive or sex is invalid.
    """
    if weight_kg <= 0 or height_cm <= 0 or age <= 0:
        raise ValueError("weight_kg, height_cm, and age must be positive.")

    base = (10.0 * weight_kg) + (6.25 * height_cm) - (5.0 * age)

    if sex == "male":
        return base + 5.0
    elif sex == "female":
        return base - 161.0
    else:
        raise ValueError(f"sex must be 'male' or 'female', got '{sex}'.")


def tdee(bmr: float, activity_level: float) -> float:
    """Calculate Total Daily Energy Expenditure.

    Formula:
        TDEE = BMR * activity_level

    Activity level multipliers (PAL):
        1.2  - Sedentary (little or no exercise)
        1.375 - Lightly active (light exercise 1-3 days/week)
        1.55 - Moderately active (moderate exercise 3-5 days/week)
        1.725 - Very active (hard exercise 6-7 days/week)
        1.9  - Extra active (very hard exercise, physical job)

    Reference:
        Gerrior S, Juan W, Peter B. An Easy Approach to Calculating
        Estimated Energy Requirements. Prev Chronic Dis. 2006;3(4):A129.

    Args:
        bmr: Basal Metabolic Rate in kcal/day.
        activity_level: Physical Activity Level multiplier (1.2 to 1.9).

    Returns:
        TDEE in kcal/day.

    Raises:
        ValueError: If bmr is non-positive or activity_level is out of range.
    """
    if bmr <= 0:
        raise ValueError("bmr must be positive.")
    if not (1.0 <= activity_level <= 2.5):
        raise ValueError(
            f"activity_level must be between 1.0 and 2.5, got {activity_level}."
        )

    return bmr * activity_level


def framingham_risk_score(
    age: int,
    sex: Literal["male", "female"],
    total_cholesterol: float,
    hdl: float,
    systolic_bp: float,
    smoker: bool,
    diabetes: bool,
) -> float:
    """Estimate 10-year cardiovascular disease (CVD) risk using the
    Framingham Risk Score (simplified point-based model).

    This is a simplified implementation of the general CVD risk model.
    The full model uses Cox proportional hazards; this version uses a
    log-linear approximation suitable for screening purposes.

    Formula (log-linear approximation):
        For males:
            L = 3.06117*ln(age) + 1.12370*ln(TC) - 0.93263*ln(HDL)
                + 1.93303*ln(SBP_treated) + 0.65451*smoker + 0.57367*diabetes
            mean_coeff = 23.9802, base_survival = 0.88936
        For females:
            L = 2.32888*ln(age) + 1.20904*ln(TC) - 0.70833*ln(HDL)
                + 2.76157*ln(SBP_treated) + 0.52873*smoker + 0.69154*diabetes
            mean_coeff = 26.1931, base_survival = 0.95012

        Risk = 1 - base_survival^exp(L - mean_coeff)

    Reference:
        D'Agostino RB Sr, Vasan RS, Pencina MJ, et al. General
        cardiovascular risk profile for use in primary care: the
        Framingham Heart Study. Circulation. 2008;117(6):743-753.
        DOI: 10.1161/CIRCULATIONAHA.107.699579

    Args:
        age: Age in years (30-79 recommended range).
        sex: Biological sex, either "male" or "female".
        total_cholesterol: Total cholesterol in mg/dL.
        hdl: HDL cholesterol in mg/dL.
        systolic_bp: Systolic blood pressure in mmHg.
        smoker: Whether the individual currently smokes.
        diabetes: Whether the individual has diabetes.

    Returns:
        Estimated 10-year CVD risk as a proportion (0.0 to 1.0).

    Raises:
        ValueError: If inputs are out of clinically plausible ranges.
    """
    if age < 20 or age > 100:
        raise ValueError(f"age must be between 20 and 100, got {age}.")
    if total_cholesterol <= 0 or hdl <= 0 or systolic_bp <= 0:
        raise ValueError("Cholesterol and blood pressure values must be positive.")

    ln_age = math.log(age)
    ln_tc = math.log(total_cholesterol)
    ln_hdl = math.log(hdl)
    ln_sbp = math.log(systolic_bp)
    smoke_val = 1.0 if smoker else 0.0
    diab_val = 1.0 if diabetes else 0.0

    if sex == "male":
        individual_sum = (
            3.06117 * ln_age
            + 1.12370 * ln_tc
            - 0.93263 * ln_hdl
            + 1.93303 * ln_sbp
            + 0.65451 * smoke_val
            + 0.57367 * diab_val
        )
        mean_coeff = 23.9802
        base_survival = 0.88936
    elif sex == "female":
        individual_sum = (
            2.32888 * ln_age
            + 1.20904 * ln_tc
            - 0.70833 * ln_hdl
            + 2.76157 * ln_sbp
            + 0.52873 * smoke_val
            + 0.69154 * diab_val
        )
        mean_coeff = 26.1931
        base_survival = 0.95012
    else:
        raise ValueError(f"sex must be 'male' or 'female', got '{sex}'.")

    risk = 1.0 - base_survival ** math.exp(individual_sum - mean_coeff)
    return max(0.0, min(1.0, risk))


def psqi_score(
    sleep_duration: float,
    sleep_latency: float,
    sleep_efficiency: float,
    disturbances: int,
) -> int:
    """Calculate a simplified Pittsburgh Sleep Quality Index (PSQI) score.

    The full PSQI has 7 components across 19 items. This simplified version
    scores 4 key components, each on a 0-3 scale, yielding a total of 0-12.
    Higher scores indicate worse sleep quality. A score >= 5 on the full
    PSQI suggests poor sleep quality.

    Component scoring:
        Sleep Duration (hours):
            > 7h = 0, 6-7h = 1, 5-6h = 2, < 5h = 3
        Sleep Latency (minutes to fall asleep):
            <= 15min = 0, 16-30min = 1, 31-60min = 2, > 60min = 3
        Sleep Efficiency (%):
            >= 85% = 0, 75-84% = 1, 65-74% = 2, < 65% = 3
        Sleep Disturbances (count per night):
            0 = 0, 1-2 = 1, 3-4 = 2, >= 5 = 3

    Reference:
        Buysse DJ, Reynolds CF, Monk TH, Berman SR, Kupfer DJ. The
        Pittsburgh Sleep Quality Index: a new instrument for psychiatric
        practice and research. Psychiatry Res. 1989;28(2):193-213.
        DOI: 10.1016/0165-1781(89)90047-4

    Args:
        sleep_duration: Total sleep time in hours.
        sleep_latency: Time to fall asleep in minutes.
        sleep_efficiency: Percentage of time in bed spent sleeping (0-100).
        disturbances: Number of sleep disturbances per night.

    Returns:
        Simplified PSQI score (0-12). Higher = worse sleep quality.

    Raises:
        ValueError: If inputs are negative or efficiency is out of range.
    """
    if sleep_duration < 0 or sleep_latency < 0:
        raise ValueError("sleep_duration and sleep_latency must be non-negative.")
    if not (0.0 <= sleep_efficiency <= 100.0):
        raise ValueError(
            f"sleep_efficiency must be between 0 and 100, got {sleep_efficiency}."
        )
    if disturbances < 0:
        raise ValueError("disturbances must be non-negative.")

    # Component 1: Sleep Duration
    if sleep_duration > 7:
        c1 = 0
    elif sleep_duration >= 6:
        c1 = 1
    elif sleep_duration >= 5:
        c1 = 2
    else:
        c1 = 3

    # Component 2: Sleep Latency
    if sleep_latency <= 15:
        c2 = 0
    elif sleep_latency <= 30:
        c2 = 1
    elif sleep_latency <= 60:
        c2 = 2
    else:
        c2 = 3

    # Component 3: Sleep Efficiency
    if sleep_efficiency >= 85:
        c3 = 0
    elif sleep_efficiency >= 75:
        c3 = 1
    elif sleep_efficiency >= 65:
        c3 = 2
    else:
        c3 = 3

    # Component 4: Sleep Disturbances
    if disturbances == 0:
        c4 = 0
    elif disturbances <= 2:
        c4 = 1
    elif disturbances <= 4:
        c4 = 2
    else:
        c4 = 3

    return c1 + c2 + c3 + c4


def body_fat_percentage(
    bmi: float,
    age: int,
    sex: Literal["male", "female"],
) -> float:
    """Estimate body fat percentage from BMI using the Deurenberg equation.

    Formula:
        BF% = (1.20 * BMI) + (0.23 * age) - (10.8 * sex_factor) - 5.4
        where sex_factor = 1 for male, 0 for female.

    Reference:
        Deurenberg P, Weststrate JA, Seidell JC. Body mass index as a
        measure of body fatness: age- and sex-specific prediction formulas.
        Br J Nutr. 1991;65(2):105-114.
        DOI: 10.1079/BJN19910073

    Args:
        bmi: Body Mass Index (kg/m^2).
        age: Age in years.
        sex: Biological sex, either "male" or "female".

    Returns:
        Estimated body fat percentage.

    Raises:
        ValueError: If bmi or age is non-positive or sex is invalid.
    """
    if bmi <= 0:
        raise ValueError("bmi must be positive.")
    if age <= 0:
        raise ValueError("age must be positive.")

    if sex == "male":
        sex_factor = 1.0
    elif sex == "female":
        sex_factor = 0.0
    else:
        raise ValueError(f"sex must be 'male' or 'female', got '{sex}'.")

    bf = (1.20 * bmi) + (0.23 * age) - (10.8 * sex_factor) - 5.4
    return max(0.0, bf)
