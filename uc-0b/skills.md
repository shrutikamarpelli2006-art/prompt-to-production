skills:
  - name: retrieve_policy
    description: Loads a .txt policy file and returns its content as a structured list of numbered sections.
    input: file_path (string)
    output: List of dictionaries {heading: string, content: string, clauses: List[string]}
    error_handling: Raise FileNotFoundError if path is invalid; return empty list if file is empty.

  - name: summarize_policy
    description: Takes structured sections and produces a compliant summary with clause references, adhering to agents.md rules.
    input: structured_sections (List of dicts)
    output: A string containing the formatted summary with [Clause X.Y] citations.
    error_handling: If a clause is missing a binding verb or is ambiguous, flag for manual review.
