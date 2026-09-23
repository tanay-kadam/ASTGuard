from astguard.models.codebert import ASTGuardClassifier


def create_model(config):
    if config.model.variant=='linevul_function':
        from astguard.baselines.linevul import LineVulFunction
        return LineVulFunction.from_pretrained(config.model.checkpoint,config.model.revision)
    if config.model.variant=='graphcodebert_c_adapted':
        from astguard.baselines.graphcodebert import GraphCodeBERTClassifier
        return GraphCodeBERTClassifier.from_pretrained(config.model.checkpoint,config.model.revision)
    if config.model.variant=='regvd':
        from astguard.baselines.regvd import ReGVDClassifier
        return ReGVDClassifier.from_pretrained(config.model.checkpoint,config.model.revision,
            hidden_size=config.model.regvd_hidden_size,layers=config.model.regvd_layers,
            window_size=config.model.regvd_window_size)
    return ASTGuardClassifier.from_pretrained(config.model.checkpoint,revision=config.model.revision,
        variant=config.model.variant,structural_layers=config.model.structural_layers,head_dropout=config.model.head_dropout,
        beta_init=config.model.beta_init,gate_sharing=config.model.gate_sharing,freeze_beta=config.model.freeze_beta,
        degree_normalization=config.preprocessing.degree_normalization)


def create_collator(config,training=False):
    if config.model.variant=='graphcodebert_c_adapted':
        from astguard.baselines.graphcodebert import GraphCollator
        return GraphCollator()
    if config.model.variant in {'sequence_only','linevul_function','regvd'}:
        from astguard.data.collate import SequenceCollator
        return SequenceCollator()
    from astguard.data.collate import StructuralCollator
    return StructuralCollator(config.model.structural_dropout if training else 0.,config.training.seed)
