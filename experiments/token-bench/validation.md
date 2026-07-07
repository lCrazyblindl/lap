# LAP honest validation v2 - live success rates + tokens-per-correct

- date: 2026-07-07
- models: `claude-haiku-4-5-20251001` and `claude-sonnet-4-6` (both complete);
  repeats: **5** per task x variant; all **10** grouped tasks (>=2 per category);
  variants: openapi_full / compact_sig / numbered / code_exec / odata_query
- fixture: 50 animals; runner: `run_bench.py --matrix-v2 --repeats 5`
- supersedes the k=3, one-task-per-category, Haiku-only matrix (Stage 15b; in git history)
- _Run note: the Sonnet pass executed in two parts (the first stopped at 38/50 cells on API
  credit exhaustion; the tail re-ran with `--tasks`, and the overlapping T4b cells were taken
  from the fresh run - old vs new means differed by <=2 tokens). Token totals are reconstructed
  from the per-cell means the runner logs; rounding error <=0.1%._

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

## Model `claude-sonnet-4-6` - success per task (5 repeats each)

| category | task | openapi_full | compact_sig | numbered | code_exec | odata_query |
| --- | --- | --- | --- | --- | --- | --- |
| write | T1_create | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| write | T1b_create_lion | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| aggregate-read | T2_count_females | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| aggregate-read | T2b_count_old_lions | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| multi-step | T3_count_per_species | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| multi-step | T3b_males_per_species | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| peek-read | T4_peek_one | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| peek-read | T4b_peek_female_monkey | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| beyond-DSL | T5_longest_name | 5/5 | 4/5 | 5/5 | 5/5 | 5/5 |
| beyond-DSL | T5b_avg_age | 5/5 | 5/5 | 5/5 | 5/5 | 4/5 |

**Overall correct:** openapi_full **50/50**, compact_sig **49/50**, numbered **50/50**,
code_exec **50/50**, odata_query **49/50**

## Tokens per correct answer (all 500 runs)

Total tokens spent across every run of a form / its correct answers - the price of a *right*
answer, so cheap-but-wrong loses.

| model | openapi_full | compact_sig | numbered | code_exec | odata_query |
| --- | ---: | ---: | ---: | ---: | ---: |
| claude-haiku-4-5 | 5759 | 4100 | 4366 | **1977** | 2069 |
| claude-sonnet-4-6 | 5652 | 4005 | 4034 | 5345 | **1902** |

Mean tokens per run (correct or not), for comparison:

| model | openapi_full | compact_sig | numbered | code_exec | odata_query |
| --- | ---: | ---: | ---: | ---: | ---: |
| claude-haiku-4-5 | 5644 | 3936 | 4017 | 1977 | 1862 |
| claude-sonnet-4-6 | 5652 | 3925 | 4034 | 5345 | 1864 |

## Findings

1. **The cheapest right answer depends on the model - and that's the headline.** On Haiku,
   `code_exec` wins outright: the only 100% form (50/50) *and* the cheapest correct answer
   (1977 tokens - 2.9x cheaper than naive's 5759). On Sonnet, the same sandbox costs
   **5345 tokens per correct answer - 2.7x more than on Haiku and nearly naive-priced** -
   because Sonnet writes exploratory, multi-attempt code (14.5k tokens on one task, 8.2k on
   another) where Haiku writes one short script. Code-execution's saving is **behavioral**,
   and stronger models can behave *more* expensively; the declarative query is Sonnet's
   cheapest right answer (1902). Structure guarantees only that the *result* stays small,
   not what the model spends getting there - the same mechanism we measured on Anthropic's
   real code execution ([CODE-EXEC.md](../../docs/CODE-EXEC.md)), now reproduced in our own
   sandbox on a strong model.
2. **Compression does not cost accuracy on either model** - compact_sig 48/50 (Haiku) and
   49/50 (Sonnet) vs naive 49/50 and 50/50, at ~30% fewer tokens per run.
3. **The `numbered` penalty is a small-model phenomenon, now measured**: Haiku 46/50 with a
   2/5 collapse on an aggregate-count task; Sonnet 50/50. Opaque codes (profile rule D3) tax
   exactly the models most sensitive to grounding - and numbered still saves no tokens over
   compact, so it loses on both axes.
4. **The DSL gap is category-shaped, and its severity is model-dependent**: on the
   query-inexpressible task (average over a computed property), Haiku's odata_query fails
   **0/5** while Sonnet recovers **4/5**. A declarative layer needs the code escape hatch
   (rule X1) for what it can't express - or a strong enough model to improvise around it.
5. **Accuracy is form-insensitive for the stronger model** (Sonnet 248/250 overall, worst
   cell 4/5) - form choice decides *cost* everywhere, and decides *correctness* mainly for
   small models.

Caveats: one toy API (pet-zoo), 2 models, k=5 (a 1-run gap is within noise), answer checking
is substring-based. Live spend across both passes: ~625k tokens (Haiku 250 runs, Sonnet ~325
runs including the interrupted first pass).
