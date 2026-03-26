# skills.md

skills:
  - name: retrieve_documents
    description: Loads HR, IT, and Finance policy files and indexes them by document name and section number.
    input: None
    output: A collection of indexed policy sections (JSON or similar structured format).
    error_handling: Logs an error if any policy file is missing or unreadable; returns an empty index.

  - name: answer_question
    description: Searches indexed policies and returns a single-source answer with citation or the exact refusal template. Strict anti-blending and anti-hedging rules apply.
    input: Question (string)
    output: Single-source answer + citation (Doc Name + Section) OR exact refusal template.
    error_handling: Return the refusal template if information is missing, ambiguous, or requires cross-document blending.
