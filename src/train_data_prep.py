import pandas as pd
from datasets import Dataset
from sklearn.model_selection import train_test_split

# ---------- Load CSV ----------
df = pd.read_csv("final_main_data.csv")

# ---------- Filter out rows with missing PROBLEM or SOLUTION ----------
before = len(df)
df = df[df["PROBLEM"].notna() & df["SOLUTION"].notna()]
df = df[(df["PROBLEM"].str.strip() != "") & (df["SOLUTION"].str.strip() != "")]
after = len(df)
print(f"✅ Filtered dataset: kept {after} rows out of {before}")

# ---------- Train/Test Split (95/5) ----------
train_df, test_df = train_test_split(df, test_size=0.05, random_state=42, shuffle=True)

# Save to CSV
train_df.to_csv("train_95.csv", index=False)
test_df.to_csv("test_5.csv", index=False)
print(f"✅ Saved train_95.csv ({len(train_df)} rows) and test_5.csv ({len(test_df)} rows)")

# ---------- Build JSONL from TRAIN set only ----------
records = []

for row in train_df.to_dict(orient="records"):
    instruction = (
        "Classify and resolve this support ticket using the following details:\n"
        f"- ticketID: {row.get('TICKETID', '')}\n"
        f"- Subject: {row.get('SUBJECT', '')}\n"
        f"- Problem: {row.get('PROBLEM', '')}\n"
    )

    output = (
        f"- Urgency: {row.get('URGENCYCODE', '')}\n"
        f"- Issue: {row.get('ISSUE', '')}\n"
        f"- Category: {row.get('CATEGORY', '')}\n"
        f"- Solution: {row.get('SOLUTION', '')}\n"
        f"- Flow: {row.get('RESOLUTION_FLOW', '')}\n"
    )

    records.append({
        "instruction": instruction.strip(),
        "input": "",
        "output": output.strip()
    })

dataset = Dataset.from_list(records)

# Save TRAIN set only as JSONL
dataset.to_json("final_train.jsonl", orient="records", lines=True)
print(f"✅ Saved {len(dataset)} training examples to final_train.jsonl")
