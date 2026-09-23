from astguard.data.splits import component_fraction


def nested_component_subset(sample_ids: list[str], component_ids: list[str], fraction: float) -> list[str]:
    if len(sample_ids) != len(component_ids):
        raise ValueError("sample/component arrays must align")
    return [sample_id for sample_id, component in zip(sample_ids, component_ids) if component_fraction(component, fraction)]

