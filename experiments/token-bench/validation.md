# LAP honest validation v2 - live success rates + tokens-per-correct

- date: 2026-07-07
- models: `claude-haiku-4-5-20251001` (complete), `claude-sonnet-4-6` (**partial - see note**);
  repeats: **5** per task x variant; all **10** grouped tasks (>=2 per category);
  variants: openapi_full / compact_sig / numbered / code_exec / odata_query
- fixture: 50 animals; runner: `run_bench.py --matrix-v2 --repeats 5`
- supersedes the k=3, one-task-per-category, Haiku-only matrix (Stage 15b; in git history)
- **Interruption note:** the Sonnet pass stopped at cell 39/50 when the API account ran out of
  credits (billing 400, not a code failure). The 38 completed Sonnet cells are reported below;
  finishing is one command after a top-up:
  `run_bench.py --matrix-v2 --repeats 5 --models claude-sonnet-4-6`.

## Model `claude-haiku-4-5-20251001` - success per task (5 repeats each)

| category | task | openapi_full | compact_sig | numbered | code_exec | odata_query |
| --- | --- | --- | --- | --- | --- | --- |
| write | T1_create | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| write | T1b_create_lion | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| aggregate-read | T2_count_females | 4/5 | 4/5 | 2/5 | 5/5 | 5/5 |
| aggregate-read | T2b_count_old_lions | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| multi-step | T3_count_per_species | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| multi-step | T3b_males_per_species | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| peek-read | T4_peek_one | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| peek-read | T4b_peek_female_monkey | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| beyond-DSL | T5_longest_name | 5/5 | 4/5 | 4/5 | 5/5 | 5/5 |
| beyond-DSL | T5b_avg_age | 5/5 | 5/5 | 5/5 | 5/5 | 0/5 |

**Overall correct:** openapi_full **49/50**, compact_sig **48/50**, numbered **46/50**,
code_exec **50/50**, odata_query **45/50**

### Tokens per correct answer (Haiku, all 250 runs)

Total tokens spent across every run of a form / its correct answers - the price of a *right*
answer, so cheap-but-wrong loses. _(Totals reconstructed from the per-cell means the runner
logs; rounding error <=0.1%.)_

| metric | openapi_full | compact_sig | numbered | code_exec | odata_query |
| --- | ---: | ---: | ---: | ---: | ---: |
| tokens per correct answer | 5759 | 4100 | 4366 | **1977** | 2069 |
| mean tokens per run | 5644 | 3936 | 4017 | 1977 | 1862 |

## Model `claude-sonnet-4-6` - partial (38 of 50 cells; interrupted by credit exhaustion)

Every completed cell (T1 through T4b/numbered - writes, aggregate-reads, multi-step, peek)
was **5/5**: **190/190 runs correct across all five forms.** The 12 unrun cells are
T4b code_exec/odata_query and the whole beyond-DSL row (T5/T5b).

Notable even in the partial data: Sonnet's **code_exec token cost is highly variable** -
~1.7-3k tokens/run on most tasks but **~14.5k on T3b** (exploratory code retries), heavier
than the naive form on that task. The same behavioral-cost variance we measured live on
Anthropic's real code execution ([CODE-EXEC.md](../../docs/CODE-EXEC.md)) shows up on a
strong model in our own sandbox too: the *structure* guarantees only the result stays small,
not how much the model spends getting there.

## Findings

1. **The escape hatch is both the most reliable and the cheapest.** `code_exec` is the only
   form at 100% (50/50 on Haiku) *and* has the lowest cost per correct answer (1977 tokens -
   **2.9x cheaper than naive**, whose right answers cost 5759).
2. **Compression does not cost accuracy** - compact_sig 48/50 vs naive 49/50 (a single-run
   difference at k=5), at ~30% fewer tokens per run.
3. **The `numbered` penalty is now measured, not anecdotal**: 46/50 overall, including a
   **2/5** on the aggregate-count task - opaque codes lose accuracy on exactly the tasks
   where grounding matters. (Profile rule D3.)
4. **The DSL gap is category-shaped, not noise**: odata_query fails **0/5** on T5b (average
   over a computed property - inexpressible in the query DSL) while scoring 5/5 everywhere
   else. A declarative layer needs the code escape hatch for what it can't express (rule X1),
   or the model fails rather than falling back.
5. **A stronger model is form-insensitive for accuracy** (Sonnet: 190/190 partial) - but not
   for *cost*: its exploratory code runs show 8x token variance on one task. Form choice
   decides cost everywhere, and decides correctness mainly for small models.

Caveats: one toy API (pet-zoo), 2 models, k=5 (a 1-run gap is within noise), answer checking
is substring-based. Live spend: ~343k tokens (Haiku ~250 runs, Sonnet ~190 runs).
