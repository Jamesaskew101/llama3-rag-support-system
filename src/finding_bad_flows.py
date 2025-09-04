df = pd.read_csv("Ticker_resolution_flows.csv")

# --- Define a validity check ---
def is_valid_flow(text: str) -> bool:
    if not isinstance(text, str) or not text.strip():
        return False

    # Does it contain a numbered flow? (at least "1." and "2.")
    if "1." in text and "2." in text:
        return True

    # Otherwise it's invalid
    return False


# Apply the check
df["is_valid"] = df["RESOLUTION_FLOW"].apply(is_valid_flow)

# Split into good and bad
bad_rows = df[~df["is_valid"]]
good_rows = df[df["is_valid"]]

print(f"✅ Found {len(good_rows)} valid rows and {len(bad_rows)} invalid rows out of {len(df)} total.")

# Save bad ones for re-processing
bad_rows.to_csv("Ticker_resolution_flows_bad.csv", index=False)
print("⚠️ Saved bad rows to Ticker_resolution_flows_bad.csv for re-running.")
# Load original ticket file
df = pd.read_excel("Ticket_query_resolution.xlsx", dtype={"TICKETID": str})

# Load bad flows (assuming you already saved them)
bad_df = pd.read_csv("Ticker_resolution_flows_bad.csv", dtype={"TICKETID": str})

# Filter: only keep rows with those TICKETIDs
filtered = df[df["TICKETID"].isin(bad_df["TICKETID"])]

# Save out to a new file
filtered.to_excel("Ticket_query_resolution_bad_only.xlsx", index=False)

print(f"✅ Filtered down to {len(filtered)} bad rows and saved to Ticket_query_
