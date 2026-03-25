skills:
  - name: classify_complaint
    description: One complaint row in -> category + priority + reason + flag out.
    input: Dictionary containing the original complaint fields.
    output: Dictionary with exact keys `category`, `priority`, `reason`, and `flag`.
    error_handling: Genuinely ambiguous or unclassifiable complaints must output category 'Other' and flag 'NEEDS_REVIEW'.

  - name: batch_classify
    description: Reads input CSV, applies classify_complaint per row, writes output CSV.
    input: input_path (string) to test CSV, output_path (string) for results CSV.
    output: CSV file written to output_path.
    error_handling: Process must flag nulls and must not crash on bad rows. Output must be produced even if some rows fail.
