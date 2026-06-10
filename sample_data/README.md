# Sample Label Test Data

The app applies one set of application data to every uploaded file in a batch. For that reason, not every sample label should be tested with the same sidebar values.

## Default demo batch

Use the default sidebar values and leave **Country of origin, if imported** blank. Then upload the files in:

```text
sample_data/default_demo_batch/
```

Expected outcomes:

| File | Expected status | Purpose |
|---|---:|---|
| `old_tom_label.txt` | PASS | Baseline passing label |
| `pass_linebreak_warning_label.txt` | PASS | Government warning split across lines |
| `pass_proof_only_label.txt` | PASS | Proof-only alcohol content equivalent to 45% ABV |
| `review_case_old_tom_case.txt` | PASS | Human-equivalent casing/formatting |
| `bad_warning_label.txt` | FAIL | Non-standard warning wording |
| `fail_abv_mismatch_label.txt` | FAIL | ABV mismatch |
| `fail_missing_warning_label.txt` | FAIL | Missing government warning |
| `fail_net_contents_mismatch_label.txt` | FAIL | Net contents mismatch |
| `fail_titlecase_warning_label.txt` | FAIL | `Government Warning` title case instead of exact all-caps prefix |

## Special scenarios

These files require changing the sidebar application data before testing.

| File | Sidebar value to change | Expected status | Purpose |
|---|---|---:|---|
| `special_scenarios/country_origin_jamaica_label.txt` | Set **Country of origin, if imported** to `Jamaica` | PASS | Imported product country-of-origin match |
| `special_scenarios/country_origin_jamaica_label.txt` | Leave **Country of origin, if imported** blank | REVIEW | Label appears imported, but application field is blank |
| `special_scenarios/review_stones_throw_case_label.txt` | Set **Brand name** to `Stone's Throw` | PASS | Dave's case/punctuation nuance: `STONE'S THROW` vs. `Stone's Throw` |

Do not upload the special-scenario files together with the default Old Tom batch unless the sidebar values match the scenario you are testing.
