# skills.md
# INSTRUCTIONS: Generate a draft by prompting AI, then manually refine this file.
# Delete these comments before committing.

skills:
  - name: load_dataset
    description: Reads the budget CSV, validates required columns, and reports null count/rows before returning the data.
    input: File path to the budget CSV (string).
    output: A pandas DataFrame or similar structure containing the validated data.
    error_handling: Raise an error if required columns are missing or if the file cannot be read.

  - name: compute_growth
    description: Calculates growth (MoM or YoY) for a specific ward and category, returning a table with the exact formula shown.
    input: Ward (string), Category (string), Growth Type (string), and the dataset.
    output: A table/list of dictionaries containing period, growth value, and the formula used.
    error_handling: Refuse and ask for clarification if growth_type is missing; flag and skip null actual_spend rows.
