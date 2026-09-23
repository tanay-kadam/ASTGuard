def summarize_gates(values, degrees):
    eligible = [float(value) for value, degree in zip(values, degrees) if degree > 0]
    if not eligible:
        return {"eligible_count": 0, "mean": None, "minimum": None, "maximum": None, "below_0.05": None, "above_0.95": None}
    return {"eligible_count": len(eligible), "mean": sum(eligible) / len(eligible), "minimum": min(eligible), "maximum": max(eligible),
            "below_0.05": sum(x < .05 for x in eligible) / len(eligible), "above_0.95": sum(x > .95 for x in eligible) / len(eligible)}

