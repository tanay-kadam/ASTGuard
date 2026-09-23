# Review 08: `primevul:original:349800` (c)

Author edges from the source alone. Do not open the pack file or any extractor output.

Record directed scalar dependencies as `[consumer_id, source_id]` using the identifier token ids below.

- A read `u` of a local scalar or parameter links `[u, d]` to every definition `d` of that binding that can reach it
  (declaration with initializer, assignment, `++`/`--`, compound assignment, or the parameter declarator).
- A new assignment/definition occurrence `d_new` links `[d_new, r]` to every scalar read `r` in its right-hand side.
  Compound assignment and increment read the old value before writing, so `i++` or `i += n` inside a loop
  can give a self-edge `[k, k]` (the read at token `k` reached by the write at `k` from the previous iteration).
- Pointer, array, and member expressions contribute only their scalar base/index reads; do not add memory or alias edges.
- Calls contribute only scalar argument reads; no callee effects or return provenance.
- Type names, function names, member selectors, and unknown globals have no bindings or edges.
  Keywords such as `return` appear in the token table because the lexer tags them as identifiers; they never have edges.
- Branches, loops, `break`, `continue`, and `return` follow normal control flow; loop back edges can carry definitions.

## Source

```c
   1 | void sched_setnuma(struct task_struct *p, int nid)
   2 | {
   3 | 	struct rq *rq;
   4 | 	unsigned long flags;
   5 | 	bool queued, running;
   6 | 
   7 | 	rq = task_rq_lock(p, &flags);
   8 | 	queued = task_on_rq_queued(p);
   9 | 	running = task_current(rq, p);
  10 | 
  11 | 	if (queued)
  12 | 		dequeue_task(rq, p, DEQUEUE_SAVE);
  13 | 	if (running)
  14 | 		put_prev_task(rq, p);
  15 | 
  16 | 	p->numa_preferred_nid = nid;
  17 | 
  18 | 	if (running)
  19 | 		p->sched_class->set_curr_task(rq);
  20 | 	if (queued)
  21 | 		enqueue_task(rq, p, ENQUEUE_RESTORE);
  22 | 	task_rq_unlock(rq, p, &flags);
  23 | }
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `void` | 1:1 |
| 1 | `sched_setnuma` | 1:6 |
| 3 | `struct` | 1:20 |
| 4 | `task_struct` | 1:27 |
| 6 | `p` | 1:40 |
| 8 | `int` | 1:43 |
| 9 | `nid` | 1:47 |
| 12 | `struct` | 3:2 |
| 13 | `rq` | 3:9 |
| 15 | `rq` | 3:13 |
| 17 | `unsigned` | 4:2 |
| 18 | `long` | 4:11 |
| 19 | `flags` | 4:16 |
| 21 | `bool` | 5:2 |
| 22 | `queued` | 5:7 |
| 24 | `running` | 5:15 |
| 26 | `rq` | 7:2 |
| 28 | `task_rq_lock` | 7:7 |
| 30 | `p` | 7:20 |
| 33 | `flags` | 7:24 |
| 36 | `queued` | 8:2 |
| 38 | `task_on_rq_queued` | 8:11 |
| 40 | `p` | 8:29 |
| 43 | `running` | 9:2 |
| 45 | `task_current` | 9:12 |
| 47 | `rq` | 9:25 |
| 49 | `p` | 9:29 |
| 52 | `if` | 11:2 |
| 54 | `queued` | 11:6 |
| 56 | `dequeue_task` | 12:3 |
| 58 | `rq` | 12:16 |
| 60 | `p` | 12:20 |
| 62 | `DEQUEUE_SAVE` | 12:23 |
| 65 | `if` | 13:2 |
| 67 | `running` | 13:6 |
| 69 | `put_prev_task` | 14:3 |
| 71 | `rq` | 14:17 |
| 73 | `p` | 14:21 |
| 76 | `p` | 16:2 |
| 78 | `numa_preferred_nid` | 16:5 |
| 80 | `nid` | 16:26 |
| 82 | `if` | 18:2 |
| 84 | `running` | 18:6 |
| 86 | `p` | 19:3 |
| 88 | `sched_class` | 19:6 |
| 90 | `set_curr_task` | 19:19 |
| 92 | `rq` | 19:33 |
| 95 | `if` | 20:2 |
| 97 | `queued` | 20:6 |
| 99 | `enqueue_task` | 21:3 |
| 101 | `rq` | 21:16 |
| 103 | `p` | 21:20 |
| 105 | `ENQUEUE_RESTORE` | 21:23 |
| 108 | `task_rq_unlock` | 22:2 |
| 110 | `rq` | 22:17 |
| 112 | `p` | 22:21 |
| 115 | `flags` | 22:25 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 1 | `'void'` |
| 2 | `'sched'` |
| 3 | `'_'` |
| 4 | `'set'` |
| 5 | `'n'` |
| 6 | `'uma'` |
| 7 | `'('` |
| 8 | `'struct'` |
| 9 | `'task'` |
| 10 | `'_'` |
| 11 | `'struct'` |
| 12 | `'*'` |
| 13 | `'p'` |
| 14 | `','` |
| 15 | `'int'` |
| 16 | `'n'` |
| 17 | `'id'` |
| 18 | `')'` |
| 19 | `'\n'` |
| 20 | `'{'` |
| 21 | `'\n'` |
| 22 | `'\t'` |
| 23 | `'struct'` |
| 24 | `'r'` |
| 25 | `'q'` |
| 26 | `'*'` |
| 27 | `'r'` |
| 28 | `'q'` |
| 29 | `';'` |
| 30 | `'\n'` |
| 31 | `'\t'` |
| 32 | `'unsigned'` |
| 33 | `'long'` |
| 34 | `'flags'` |
| 35 | `';'` |
| 36 | `'\n'` |
| 37 | `'\t'` |
| 38 | `'bool'` |
| 39 | `'que'` |
| 40 | `'ued'` |
| 41 | `','` |
| 42 | `'running'` |
| 43 | `';'` |
| 44 | `'\n\n'` |
| 45 | `'\t'` |
| 46 | `'r'` |
| 47 | `'q'` |
| 48 | `'='` |
| 49 | `'task'` |
| 50 | `'_'` |
| 51 | `'r'` |
| 52 | `'q'` |
| 53 | `'_'` |
| 54 | `'lock'` |
| 55 | `'('` |
| 56 | `'p'` |
| 57 | `','` |
| 58 | `'&'` |
| 59 | `'flags'` |
| 60 | `');'` |
| 61 | `'\n'` |
| 62 | `'\t'` |
| 63 | `'que'` |
| 64 | `'ued'` |
| 65 | `'='` |
| 66 | `'task'` |
| 67 | `'_'` |
| 68 | `'on'` |
| 69 | `'_'` |
| 70 | `'r'` |
| 71 | `'q'` |
| 72 | `'_'` |
| 73 | `'que'` |
| 74 | `'ued'` |
| 75 | `'('` |
| 76 | `'p'` |
| 77 | `');'` |
| 78 | `'\n'` |
| 79 | `'\t'` |
| 80 | `'running'` |
| 81 | `'='` |
| 82 | `'task'` |
| 83 | `'_'` |
| 84 | `'current'` |
| 85 | `'('` |
| 86 | `'r'` |
| 87 | `'q'` |
| 88 | `','` |
| 89 | `'p'` |
| 90 | `');'` |
| 91 | `'\n\n'` |
| 92 | `'\t'` |
| 93 | `'if'` |
| 94 | `'('` |
| 95 | `'que'` |
| 96 | `'ued'` |
| 97 | `')'` |
| 98 | `'\n'` |
| 99 | `'\t'` |
| 100 | `'\t'` |
| 101 | `'de'` |
| 102 | `'queue'` |
| 103 | `'_'` |
| 104 | `'task'` |
| 105 | `'('` |
| 106 | `'r'` |
| 107 | `'q'` |
| 108 | `','` |
| 109 | `'p'` |
| 110 | `','` |
| 111 | `'DE'` |
| 112 | `'Q'` |
| 113 | `'UE'` |
| 114 | `'UE'` |
| 115 | `'_'` |
| 116 | `'SA'` |
| 117 | `'VE'` |
| 118 | `');'` |
| 119 | `'\n'` |
| 120 | `'\t'` |
| 121 | `'if'` |
| 122 | `'('` |
| 123 | `'running'` |
| 124 | `')'` |
| 125 | `'\n'` |
| 126 | `'\t'` |
| 127 | `'\t'` |
| 128 | `'put'` |
| 129 | `'_'` |
| 130 | `'prev'` |
| 131 | `'_'` |
| 132 | `'task'` |
| 133 | `'('` |
| 134 | `'r'` |
| 135 | `'q'` |
| 136 | `','` |
| 137 | `'p'` |
| 138 | `');'` |
| 139 | `'\n\n'` |
| 140 | `'\t'` |
| 141 | `'p'` |
| 142 | `'->'` |
| 143 | `'n'` |
| 144 | `'uma'` |
| 145 | `'_'` |
| 146 | `'pre'` |
| 147 | `'ferred'` |
| 148 | `'_'` |
| 149 | `'n'` |
| 150 | `'id'` |
| 151 | `'='` |
| 152 | `'n'` |
| 153 | `'id'` |
| 154 | `';'` |
| 155 | `'\n\n'` |
| 156 | `'\t'` |
| 157 | `'if'` |
| 158 | `'('` |
| 159 | `'running'` |
| 160 | `')'` |
| 161 | `'\n'` |
| 162 | `'\t'` |
| 163 | `'\t'` |
| 164 | `'p'` |
| 165 | `'->'` |
| 166 | `'sc'` |
| 167 | `'hed'` |
| 168 | `'_'` |
| 169 | `'class'` |
| 170 | `'->'` |
| 171 | `'set'` |
| 172 | `'_'` |
| 173 | `'cur'` |
| 174 | `'r'` |
| 175 | `'_'` |
| 176 | `'task'` |
| 177 | `'('` |
| 178 | `'r'` |
| 179 | `'q'` |
| 180 | `');'` |
| 181 | `'\n'` |
| 182 | `'\t'` |
| 183 | `'if'` |
| 184 | `'('` |
| 185 | `'que'` |
| 186 | `'ued'` |
| 187 | `')'` |
| 188 | `'\n'` |
| 189 | `'\t'` |
| 190 | `'\t'` |
| 191 | `'en'` |
| 192 | `'queue'` |
| 193 | `'_'` |
| 194 | `'task'` |
| 195 | `'('` |
| 196 | `'r'` |
| 197 | `'q'` |
| 198 | `','` |
| 199 | `'p'` |
| 200 | `','` |
| 201 | `'EN'` |
| 202 | `'Q'` |
| 203 | `'UE'` |
| 204 | `'UE'` |
| 205 | `'_'` |
| 206 | `'R'` |
| 207 | `'EST'` |
| 208 | `'ORE'` |
| 209 | `');'` |
| 210 | `'\n'` |
| 211 | `'\t'` |
| 212 | `'task'` |
| 213 | `'_'` |
| 214 | `'r'` |
| 215 | `'q'` |
| 216 | `'_'` |
| 217 | `'un'` |
| 218 | `'lock'` |
| 219 | `'('` |
| 220 | `'r'` |
| 221 | `'q'` |
| 222 | `','` |
| 223 | `'p'` |
| 224 | `','` |
| 225 | `'&'` |
| 226 | `'flags'` |
| 227 | `');'` |
| 228 | `'\n'` |
| 229 | `'}'` |
