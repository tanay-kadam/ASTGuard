from __future__ import annotations

import argparse
import dataclasses
from functools import lru_cache
from pathlib import Path

from astguard.alignment.byte_spans import ByteSpanAligner
from astguard.alignment.projection import RelationProjector
from astguard.alignment.tokenizer import CanonicalTokenizer, SmokeTokenizer
from astguard.data.schema import FeatureRecord, SampleRecord, read_jsonl, write_jsonl
from astguard.data.cache import FeatureCache
from astguard.parsing.lowering import extract_dependencies,extract_visible_prefix_dependencies
from astguard.parsing.lexical import lex
from astguard.parsing.relations import SyntaxRelationBuilder
from astguard.parsing.trees import select_c_or_cpp, error_free_prefix_forest
from astguard.utils.hashing import object_hash


@lru_cache(maxsize=16)
def _preprocessing_hash(tokenizer_hash: str, max_length: int, smoke: bool,
                        ast_relation: str, dfg_symmetry: bool, structural_context: str, topology: str) -> str:
    import importlib.metadata
    from astguard.utils.hashing import sha256_file
    dependencies={name:importlib.metadata.version(name) for name in ['tree-sitter','tree-sitter-c','tree-sitter-cpp','transformers','tokenizers']} if not smoke else {}
    code_paths=[path for directory in ['astguard/parsing','astguard/alignment'] for path in sorted(Path(directory).glob('*.py'))]
    code_paths += [Path('astguard/data/preprocess.py'),Path('astguard/analysis/robustness.py')]
    code_hashes={str(path):sha256_file(path) for path in code_paths}
    return object_hash({'schema':3,'versions':dependencies,'code':code_hashes,'tokenizer':tokenizer_hash,
                        'max_length':max_length,'smoke':smoke,'ast_radius':4,'ast_relation':ast_relation,
                        'dfg_symmetry':dfg_symmetry,'structural_context':structural_context,'topology':topology})


def preprocess_record(record: SampleRecord, tokenizer, *, max_length: int = 512, smoke: bool = False, ast_relation='leaf_path_radius4', dfg_symmetry=False, structural_context='full_function', topology='clean') -> FeatureRecord:
    if topology not in {'clean','degree_preserving_rewired'}:
        raise ValueError(f'unsupported topology: {topology}')
    source = record.source_canonical
    encoded = tokenizer.encode(source, max_length=max_length)
    lexical_error=None
    try:
        lexical = lex(source)
    except ValueError as exc:
        lexical=[]
        lexical_error=str(exc)
    spans = [(node.start_byte, node.end_byte) for node in lexical]
    full_offsets=[(0,0),*encoded.all_source_offsets_byte]
    full_special=[True]+[False]*len(encoded.all_source_offsets_byte)
    lexical_to_bpe, eligible = ByteSpanAligner().align(full_offsets, spans, full_special,1+encoded.retained_bpe_length)
    ast_to_bpe = lexical_to_bpe
    prefix_incomplete=False
    extraction_source=source
    if structural_context=='visible_prefix' and encoded.original_bpe_length>encoded.retained_bpe_length:
        boundary=max((spans[i][1] for i in eligible),default=0)
        raw=source.encode('utf-8')
        extraction_source=(raw[:boundary]+bytes(10 if b==10 else 32 for b in raw[boundary:])).decode('utf-8')
    reasons: list[str] = []
    language = record.language_metadata if record.language_metadata in {"c", "cpp"} else "c"
    if smoke:
        # Plumbing-only topology. Scientific preprocessing refuses this path.
        ast_lexical = [(i, i + 1) for i in range(len(lexical) - 1) if i in eligible and i + 1 in eligible]
        parse_status, ast_status, dfg_status = "smoke_lexical", "smoke_lexical", "smoke_unavailable"
        dfg_lexical: list[tuple[int, int]] = []
        reasons.append("plumbing_only_no_tree_sitter")
    else:
        tree = select_c_or_cpp(extraction_source, record.language_metadata)
        native_tree=tree
        if structural_context=='visible_prefix' and extraction_source!=source and not tree.successful:
            tree=error_free_prefix_forest(tree,boundary)
            prefix_incomplete=True
        language = tree.language
        parse_status = 'prefix_recovered' if prefix_incomplete else "ok" if tree.successful else "parse_failed"
        if tree.successful:
            builder=SyntaxRelationBuilder(4)
            tree_leaf_ids, ast_lexical = builder.anchored_parent_child(tree) if ast_relation=='anchored_parent_child' else builder.build(tree)
            tree_spans = [(tree.nodes[node].start_byte, tree.nodes[node].end_byte) for node in tree_leaf_ids]
            ast_to_bpe, ast_eligible = ByteSpanAligner().align(full_offsets, tree_spans, full_special,1+encoded.retained_bpe_length)
            ast_status = "ok"
        else:
            ast_lexical = []
            ast_status = "parse_failed"
            reasons.append("tree_contains_error_or_missing_node")
        if lexical_error is None and structural_context=='visible_prefix' and extraction_source!=source:
            extraction=extract_visible_prefix_dependencies(extraction_source,native_tree,lexical,boundary)
        else:
            extraction = extract_dependencies(extraction_source, native_tree, lexical) if lexical_error is None else None
        dfg_lexical = list(extraction.edges) if extraction else []
        dfg_status = extraction.status if extraction else 'lexical_failed'
        reasons.extend(extraction.reasons if extraction else [lexical_error])
        if dfg_symmetry:
            dfg_lexical=sorted(set(dfg_lexical)|{(b,a) for a,b in dfg_lexical})
    topology_stats={}
    if topology == 'degree_preserving_rewired':
        from astguard.analysis.robustness import rewire_directed_edges, rewire_symmetric_edges
        ast_swap=rewire_symmetric_edges(ast_lexical,sample_id=record.sample_id,relation='ast',seed=1001)
        dfg_swap=rewire_directed_edges(dfg_lexical,sample_id=record.sample_id,relation='dfg',seed=1001)
        ast_lexical,dfg_lexical=ast_swap['edges'],dfg_swap['edges']
        topology_stats={'ast_rewire_rate':ast_swap['achieved_rate'],'dfg_rewire_rate':dfg_swap['achieved_rate'],
                        'ast_rewire_attempts':ast_swap['attempts'],'dfg_rewire_attempts':dfg_swap['attempts'],
                        'ast_successful_swaps':ast_swap['successful_swaps'],
                        'dfg_successful_swaps':dfg_swap['successful_swaps'],
                        'ast_successful_swap_goal':ast_swap['successful_swap_goal'],
                        'dfg_successful_swap_goal':dfg_swap['successful_swap_goal'],
                        'rewire_seed':1001}
    ast_edges, groups = RelationProjector().project(ast_lexical, ast_to_bpe, symmetric=True)
    dfg_edges, dfg_groups = RelationProjector().project(dfg_lexical, lexical_to_bpe, symmetric=False)
    for group in groups:
        group["relation"] = "ast"
    for group in dfg_groups:
        group["relation"] = "dfg"
    tokenizer_hash=getattr(tokenizer,'identity_hash',None)
    if tokenizer_hash is None:
        tokenizer_hash=object_hash(tokenizer.tokenizer.backend_tokenizer.to_str()) if hasattr(tokenizer,'tokenizer') else 'smoke'
        tokenizer.identity_hash=tokenizer_hash
    preprocessing_hash=_preprocessing_hash(tokenizer_hash,max_length,smoke,ast_relation,dfg_symmetry,structural_context,topology)
    return FeatureRecord(
        sample_id=record.sample_id, source_sha256=record.raw_sha256, preprocessing_hash=preprocessing_hash,
        input_ids=encoded.input_ids, attention_mask=encoded.attention_mask,
        special_tokens_mask=encoded.special_tokens_mask, offsets_char=encoded.offsets_char,
        offsets_byte=encoded.offsets_byte, original_bpe_length=encoded.original_bpe_length,
        retained_bpe_length=encoded.retained_bpe_length, language_selected=language,
        parse_status=parse_status, ast_status=ast_status, dfg_status=dfg_status,
        alignment_status="ok", status_reasons=reasons,
        lexical_nodes=[dataclasses.asdict(node) for node in lexical],
        lexical_ast_edges=ast_lexical, lexical_dfg_edges=dfg_lexical, leaf_to_bpe=lexical_to_bpe,
        ast_leaf_to_bpe=ast_to_bpe,
        ast_token_edges=ast_edges, dfg_token_edges=dfg_edges,
        edge_projection_groups=groups + dfg_groups,
        relation_stats={"ast_edges": len(ast_edges), "dfg_edges": len(dfg_edges), "eligible_leaves": len(eligible), **topology_stats},
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--checkpoint", default="microsoft/codebert-base")
    parser.add_argument("--revision")
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--dataset")
    parser.add_argument("--view")
    parser.add_argument('--ast-relation', choices=['leaf_path_radius4','anchored_parent_child'], default='leaf_path_radius4')
    parser.add_argument('--dfg-symmetry', action='store_true')
    parser.add_argument('--structural-context', choices=['full_function','visible_prefix'], default='full_function')
    parser.add_argument('--topology', choices=['clean','degree_preserving_rewired'], default='clean')
    parser.add_argument('--cache-root',default='data/cache/features')
    parser.add_argument('--failures',help='JSONL failure ledger (defaults beside --output)')
    args = parser.parse_args(argv)
    tokenizer = SmokeTokenizer() if args.smoke else CanonicalTokenizer(args.checkpoint, args.revision)
    tokenizer_hash=getattr(tokenizer,'identity_hash','smoke')
    preprocessing_hash=_preprocessing_hash(tokenizer_hash,args.max_length,args.smoke,args.ast_relation,
                                           args.dfg_symmetry,args.structural_context,args.topology)
    cache=FeatureCache(Path(args.cache_root)/preprocessing_hash,preprocessing_hash)
    failure_path=Path(args.failures or (str(args.output)+'.failures.jsonl'))
    from astguard.utils.atomic_io import atomic_write_text
    atomic_write_text(failure_path,"")
    failure_count=[0]
    def features():
        from astguard.utils.atomic_io import append_jsonl
        for row in read_jsonl(args.records):
            record=SampleRecord.from_dict(row)
            try:
                yield cache.get_or_build(record.raw_sha256,lambda:dataclasses.asdict(preprocess_record(
                    record,tokenizer,max_length=args.max_length,smoke=args.smoke,ast_relation=args.ast_relation,
                    dfg_symmetry=args.dfg_symmetry,structural_context=args.structural_context,topology=args.topology)),
                    sample_id=record.sample_id)
            except Exception as exc:
                failure_count[0]+=1
                append_jsonl(failure_path,{"sample_id":record.sample_id,"dataset":record.dataset,
                    "stage":"preprocess","exception":type(exc).__name__,"reason":str(exc),
                    "source_length":len(record.source_canonical),"language":record.language_metadata,
                    "cache_version":preprocessing_hash})
    write_jsonl(args.output, features)
    if failure_count[0]:
        raise RuntimeError(f"{failure_count[0]} preprocessing failures; see {failure_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
