
import os
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import inventorize as inv
from typing import Optional, Tuple

# --- Constants ---
INPUT_CSV_NAME = r'C:/Users/ZIAD/Desktop/ABC analysis/Food_prices_dz.csv'
CLEAN_DATA_CSV = 'retail_clean.csv'
ABC_ANALYSIS_CSV = 'for_abc.csv'

PRICE_COL = 'Price'
QUANTITY_COL = 'Quantity'
REVENUE_COL = 'Revenue'
CATEGORY_COL = 'Category'
MARKET_COL = 'Market'
 
def load_and_clean_data(file_path: str) -> Optional[pd.DataFrame]:
    """
    Loads, cleans, and preprocesses the food prices data from a CSV file.
    """
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"Error: The file was not found at {file_path}")
        return None

    # Ensure required columns exist
    required_cols = [PRICE_COL, QUANTITY_COL, CATEGORY_COL, MARKET_COL]
    for col in required_cols:
        if col not in df.columns:
            print(f"Error: Required column '{col}' not found in the input file.")
            return None

    df_clean = (
        df.drop_duplicates()
        .loc[df[QUANTITY_COL] > 0]
        .copy()
    )

    # Clean 'Price' column and calculate 'Revenue'
    df_clean[PRICE_COL] = df_clean[PRICE_COL].fillna('').astype(str)
    df_clean[PRICE_COL] = df_clean[PRICE_COL].str.replace(',', '', regex=False)
    df_clean[PRICE_COL] = df_clean[PRICE_COL].str.replace(' DA', '', regex=False)
    df_clean[PRICE_COL] = df_clean[PRICE_COL].replace('', np.nan)
    df_clean[PRICE_COL] = pd.to_numeric(df_clean[PRICE_COL], errors='coerce')
    df_clean = df_clean.dropna(subset=[PRICE_COL])

    # Ensure Quantity is numeric
    df_clean[QUANTITY_COL] = pd.to_numeric(df_clean[QUANTITY_COL], errors='coerce')
    df_clean = df_clean.dropna(subset=[QUANTITY_COL])

    df_clean[REVENUE_COL] = df_clean[PRICE_COL] * df_clean[QUANTITY_COL]

    if df_clean.empty:
        print("No data left after cleaning. Exiting.")
        return None

    df_clean.to_csv(CLEAN_DATA_CSV, index=False)
    print(f"Cleaned data saved to '{CLEAN_DATA_CSV}'")
    return df_clean

def perform_abc_analysis(df: pd.DataFrame) -> None:
    """
    Performs and visualizes a single-criterion ABC analysis on sales data.
    """
    grouped = df.groupby(CATEGORY_COL).agg(
        total_sales=(QUANTITY_COL, np.sum),
        total_revenue=(REVENUE_COL, np.sum)
    ).reset_index()

    grouped.to_csv(ABC_ANALYSIS_CSV, index=False)
    print(f"ABC analysis input data saved to '{ABC_ANALYSIS_CSV}'")

    # Perform ABC analysis using inventorize
    abc_results = inv.ABC(grouped[[CATEGORY_COL, 'total_sales']])
    # Add total_sales to abc_results
    abc_results = abc_results.merge(grouped[[CATEGORY_COL, 'total_sales']], on=CATEGORY_COL, how='left')
    print("ABC Results columns:", abc_results.columns)

    # Assign ABC class based on cumulative percentage
    def assign_abc(cum):
        if cum <= 0.75:
            return 'A'
        elif cum <= 0.95:
            return 'B'
        else:
            return 'C'

    abc_results['Groupe'] = abc_results['comulative'].astype(float).apply(assign_abc)
    print("ABC Results columns after adding Groupe:", abc_results.columns)
    palette = {'A': 'green', 'B': 'yellow', 'C': 'red'}

    # Plot 1: Count of categories per Groupe
    plt.figure(figsize=(8, 5))
    sns.countplot(x='Groupe', data=abc_results, order=['A', 'B', 'C'], palette=palette)
    plt.title('Count of Categories per Groupe')
    plt.xlabel('Groupe')
    plt.ylabel('Count')
    plt.tight_layout()
    plt.savefig('abc_count_per_groupe.png')
    plt.show()
    plt.close()

    # Plot 2: Total Sales per Groupe
    plt.figure(figsize=(8, 5))
    sns.barplot(x='Groupe', y='total_sales_x', data=abc_results, order=['A', 'B', 'C'], palette=palette, estimator=sum)
    plt.title('Total Sales per Groupe')
    plt.xlabel('Groupe')
    plt.ylabel('Total Sales')
    plt.tight_layout()
    plt.savefig('abc_total_sales_per_groupe.png')
    plt.show()
    plt.close()

def perform_product_mix_analysis(df: pd.DataFrame) -> None:
    """
    Performs and visualizes a multi-criterion product mix analysis.
    """
    grouped = df.groupby(CATEGORY_COL).agg(
        total_sales=(QUANTITY_COL, np.sum),
        total_revenue=(REVENUE_COL, np.sum)
    ).reset_index()

    product_mix_results = inv.productmix(grouped[CATEGORY_COL], grouped['total_sales'], grouped['total_revenue'])
    print("Product Mix Results columns:", product_mix_results.columns)

    mix_col = 'product_mix' if 'product_mix' in product_mix_results.columns else product_mix_results.columns[-1]

    plt.figure(figsize=(10, 7))
    sns.countplot(x=mix_col, data=product_mix_results, palette="Set2")  # Add palette here
    plt.title('Product Mix Analysis - Combination Counts')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('product_mix_counts.png')
    print("Saved plot to 'product_mix_counts.png'")
    plt.show()
    plt.close()

def summarize_by_market_category(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generates a summary of total sales and revenue by market and category.
    """
    market_summary = df.groupby([MARKET_COL, CATEGORY_COL]).agg(
        total_sales=(QUANTITY_COL, np.sum),
        total_revenue=(REVENUE_COL, np.sum)
    ).reset_index()
    print("\nMarket and Category Summary:")
    print(market_summary.to_string(index=False))  # Show all rows

    print("\nAll unique categories:")
    print(market_summary[CATEGORY_COL].unique())

    return market_summary

def main():
    # --- 1. Load and Clean Data ---
    food_prices_clean = load_and_clean_data(INPUT_CSV_NAME)

    if food_prices_clean is not None:
        # --- 2. Perform Analyses ---
        perform_abc_analysis(food_prices_clean)
        perform_product_mix_analysis(food_prices_clean)
        summarize_by_market_category(food_prices_clean)
        print("\nAnalysis complete.")

if __name__ == "__main__":
    main()