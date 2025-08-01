"""
this file is gonna be dedicated to generating dummy data for testing purposes
"""

import random
import pandas as pd

df = pd.DataFrame({
    "id": [i for i in range(1, 101)],   
    "name": [f"Name_{i}" for i in range(1, 101)],
    "age": [random.choice([None, random.randint(18, 65)]) for _ in range(100)],
    "salary": [random.choice([None, random.randint(30000, 120000)]) for _ in range(100)]
})

hollowed_df = df.copy()
for column in hollowed_df.columns:
    for row in range(len(hollowed_df)):
        if random.random() < 0.5:
            hollowed_df.at[row, column] = None


hollowed_df.to_csv("tests/dummy_gen.csv", index=False)
print(hollowed_df.isna().mean())