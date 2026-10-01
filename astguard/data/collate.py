from __future__ import annotations


import random

from astguard.training.seeds import augmentation_seed


class SequenceCollator:
    """Pad token-only baselines without allocating dense structural masks."""
    def __call__(self,batch):
        import torch
        length=max(len(item["input_ids"]) for item in batch)
        return {"input_ids":torch.tensor([item["input_ids"]+[1]*(length-len(item["input_ids"])) for item in batch],
                                         dtype=torch.long),
                "attention_mask":torch.tensor([item["attention_mask"]+[False]*(length-len(item["attention_mask"]))
                                                for item in batch],dtype=torch.bool),
                "labels":torch.tensor([int(item["label"]) for item in batch],dtype=torch.float32),
                "sample_ids":[item["sample_id"] for item in batch]}


class StructuralCollator:
    def __init__(self, structural_dropout: float = 0.0, run_seed: int = 42, epoch: int = 0, presentation_counts: dict[str, int] | None = None, shuffle_graphs: bool = False):
        if not 0 <= structural_dropout <= 1:
            raise ValueError("structural_dropout must be in [0,1]")
        self.structural_dropout = structural_dropout
        self.run_seed = run_seed
        self.epoch = epoch
        self.presentation_counts = presentation_counts if presentation_counts is not None else {}
        self.shuffle_graphs = shuffle_graphs
        self._shuffle_call_count = 0

    def __call__(self, batch: list[dict]):
        try:
            import torch
        except ImportError as exc:
            raise RuntimeError("StructuralCollator requires PyTorch") from exc
        max_length = max(len(item["input_ids"]) for item in batch)
        ids, masks, specials, labels, relation_masks = [], [], [], [], []
        metadata = []
        for item in batch:
            length = len(item["input_ids"])
            padding = max_length - length
            ids.append(item["input_ids"] + [1] * padding)
            masks.append(item["attention_mask"] + [False] * padding)
            specials.append(item['special_tokens_mask'] + [True] * padding)
            dense = torch.zeros((2, max_length, max_length), dtype=torch.bool)
            grouped = item.get("edge_projection_groups", [])
            retained_by_relation = {"ast": set(), "dfg": set()}
            if grouped:
                presentation = self.presentation_counts.get(item["sample_id"], 0)
                rng = random.Random(augmentation_seed(self.run_seed, self.epoch, item["sample_id"], presentation))
                self.presentation_counts[item["sample_id"]] = presentation + 1
                for group in grouped:
                    if self.structural_dropout and rng.random() < self.structural_dropout:
                        continue
                    retained_by_relation[group["relation"]].update(tuple(pair) for pair in group["projected_pairs"])
            else:
                if self.structural_dropout and (item.get('ast_token_edges') or item.get('dfg_token_edges')):
                    raise ValueError('lexical projection groups are required for structural dropout')
                retained_by_relation["ast"].update(map(tuple,item.get("ast_token_edges", [])))
                retained_by_relation["dfg"].update(map(tuple,item.get("dfg_token_edges", [])))
            for relation_index, relation in enumerate(("ast", "dfg")):
                for left, right in retained_by_relation[relation]:
                    if left < length and right < length and left != right:
                        if item['special_tokens_mask'][left] or item['special_tokens_mask'][right]:
                            raise ValueError('structural edge touches a special token')
                        dense[relation_index, left, right] = True
            relation_masks.append(dense)
            labels.append(int(item["label"]))
            metadata.append(item["sample_id"])
        stacked_relation_masks = torch.stack(relation_masks)
        if self.shuffle_graphs and len(batch) > 1:
            stacked_relation_masks = self._shuffle_batch_graphs(stacked_relation_masks)
        return {
            "input_ids": torch.tensor(ids, dtype=torch.long),
            "attention_mask": torch.tensor(masks, dtype=torch.bool),
            "special_tokens_mask": torch.tensor(specials, dtype=torch.bool),
            "relation_masks": stacked_relation_masks,
            "labels": torch.tensor(labels, dtype=torch.float32),
            "sample_ids": metadata,
        }

    def _shuffle_batch_graphs(self, relation_masks):
        """Pair each example's tokens with another example's graph (no fixed points).

        Capacity-matched topology ablation: breaks the correspondence between a
        function's structure and its own AST/DFG edges while leaving the model
        architecture, parameter count, and edge density distribution untouched.
        """
        import torch

        n = relation_masks.shape[0]
        self._shuffle_call_count += 1
        generator = torch.Generator(device="cpu")
        generator.manual_seed(augmentation_seed(self.run_seed, self.epoch, "shuffle_graphs", self._shuffle_call_count))
        while True:
            perm = torch.randperm(n, generator=generator)
            if n == 1 or bool((perm != torch.arange(n)).all()):
                break
        return relation_masks[perm]
