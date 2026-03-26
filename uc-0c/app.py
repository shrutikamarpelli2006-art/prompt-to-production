import argparse
import pandas as pd
import sys
import os

def load_dataset(path):
    """Reads CSV, validates columns, reports null count and which rows before returning."""
    if not os.path.exists(path):
        print(f"Error: File {path} not found.")
        sys.exit(1)
    
    df = pd.read_csv(path)
    required_columns = ['period', 'ward', 'category', 'budgeted_amount', 'actual_spend', 'notes']
    
    if not all(col in df.columns for col in required_columns):
        print(f"Error: CSV must contain columns: {', '.join(required_columns)}")
        sys.exit(1)
    
    # Flag null rows
    null_rows = df[df['actual_spend'].isna()]
    if not null_rows.empty:
        print(f"Found {len(null_rows)} null actual_spend rows:")
        for _, row in null_rows.iterrows():
            print(f"- {row['period']} | {row['ward']} | {row['category']} | Reason: {row['notes']}")
    
    return df

def compute_growth(df, ward, category, growth_type):
    """Takes ward + category + growth_type, returns per-period table with formula shown."""
    # Enforcement 1: Never aggregate across wards or categories unless explicitly instructed
    # Check if we have multiple wards or categories in the filtered data
    unique_wards = df['ward'].unique()
    unique_categories = df['category'].unique()

    # If the user didn't specify ward or category, and there are multiple, refuse.
    if (not ward and len(unique_wards) > 1) or (not category and len(unique_categories) > 1):
        print("Refusal: This system does not aggregate across wards or categories. Please specify both --ward and --category.")
        sys.exit(1)

    filtered_df = df.copy()
    if ward:
        filtered_df = filtered_df[filtered_df['ward'] == ward]
    if category:
        filtered_df = filtered_df[filtered_df['category'] == category]

    if filtered_df.empty:
        print(f"No data found for Ward: {ward}, Category: {category}")
        sys.exit(1)

    # Re-check uniqueness in filtered data
    if len(filtered_df['ward'].unique()) > 1 or len(filtered_df['category'].unique()) > 1:
         print("Refusal: The criteria results in multiple wards/categories. Aggregation is not allowed.")
         sys.exit(1)

    filtered_df = filtered_df.sort_values('period')
    results = []
    
    # Growth Calculation (MoM)
    for i in range(len(filtered_df)):
        current_row = filtered_df.iloc[i]
        period = current_row['period']
        actual_spend = current_row['actual_spend']
        note = current_row['notes']

        if pd.isna(actual_spend):
            results.append({
                'Ward': current_row['ward'],
                'Category': current_row['category'],
                'Period': period,
                'Actual Spend': 'NULL',
                'Growth': 'FLAGGED',
                'Formula': 'n/a (Null value)',
                'Notes': note
            })
            continue

        if i == 0:
            results.append({
                'Ward': current_row['ward'],
                'Category': current_row['category'],
                'Period': period,
                'Actual Spend': actual_spend,
                'Growth': 'n/a',
                'Formula': 'Initial Period',
                'Notes': note
            })
        else:
            prev_spend = filtered_df.iloc[i-1]['actual_spend']
            if pd.isna(prev_spend):
                results.append({
                    'Ward': current_row['ward'],
                    'Category': current_row['category'],
                    'Period': period,
                    'Actual Spend': actual_spend,
                    'Growth': 'n/a',
                    'Formula': f"({actual_spend} - NULL) / NULL",
                    'Notes': note
                })
            else:
                growth = ((actual_spend - prev_spend) / prev_spend) * 100
                formula = f"({actual_spend} - {prev_spend}) / {prev_spend}"
                results.append({
                    'Ward': current_row['ward'],
                    'Category': current_row['category'],
                    'Period': period,
                    'Actual Spend': actual_spend,
                    'Growth': f"{growth:+.1f}%",
                    'Formula': formula,
                    'Notes': note
                })
                
    return pd.DataFrame(results)

def main():
    parser = argparse.ArgumentParser(description="Budget Growth Analyst")
    parser.add_argument("--input", required=True, help="Path to input budget CSV")
    parser.add_argument("--ward", help="Ward name")
    parser.add_argument("--category", help="Category name")
    parser.add_argument("--growth-type", help="MoM or YoY")
    parser.add_argument("--output", required=True, help="Path to output CSV")

    args = parser.parse_args()

    # Enforcement 4: If --growth-type is not specified — refuse
    if not args.growth_type:
        print("Error: --growth-type must be specified (e.g., MoM). Refusing the request.")
        sys.exit(1)

    df = load_dataset(args.input)
    
    results_df = compute_growth(df, args.ward, args.category, args.growth_type)
    
    results_df.to_csv(args.output, index=False)
    print(f"Results saved to {args.output}")

if __name__ == "__main__":
    main()
