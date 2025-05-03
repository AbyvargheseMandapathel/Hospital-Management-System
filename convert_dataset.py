import pandas as pd
import numpy as np

# Define file paths
input_file = 'dataset1.csv'
output_file = 'dataset.csv'

# Read the input CSV file
df = pd.read_csv(input_file)

# Extract all unique symptoms from the dataset
all_symptoms = set()
for col in df.columns[1:]:  # Skip the Disease column
    # Extract non-empty symptoms from each row and strip whitespace
    symptoms = df[col].dropna().astype(str).str.strip()
    all_symptoms.update(symptoms)

# Remove any empty strings
all_symptoms = [s for s in all_symptoms if s]
# Sort symptoms alphabetically
all_symptoms = sorted(all_symptoms)

print(f"Total unique symptoms found: {len(all_symptoms)}")

# Create a new DataFrame with symptoms as columns
result_df = pd.DataFrame(columns=all_symptoms)

# Process each row in the original dataset
for _, row in df.iterrows():
    disease = row['Disease']
    
    # Create a dictionary to store symptom presence (1) or absence (0)
    symptom_dict = {symptom: 0 for symptom in all_symptoms}
    
    # Mark symptoms as present (1) for this disease instance
    for col in df.columns[1:]:
        if pd.notna(row[col]):
            symptom = row[col].strip()
            if symptom in all_symptoms:
                symptom_dict[symptom] = 1
    
    # Add a row to the result DataFrame
    result_df = pd.concat([result_df, pd.DataFrame([symptom_dict])], ignore_index=True)

# Add prognosis (disease) column at the end
result_df['prognosis'] = df['Disease']

# Save the result to a new CSV file
result_df.to_csv(output_file, index=False)

print(f"Conversion complete. Output saved to {output_file}")
print(f"Number of features in the output dataset: {len(result_df.columns) - 1}")  # -1 for prognosis column