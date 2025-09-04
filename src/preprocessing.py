import pandas as pd
import re

# Load & clean data (your existing steps)
file_path = "Ticket history 3.xlsx"
df = pd.read_excel(file_path)
TICKET_COL, TIME_COL, ACTIVITY_COL = "TICKETID", "CREATEDATE", "ACTIVITYDESC"
df[TIME_COL] = pd.to_datetime(df[TIME_COL], errors="coerce", dayfirst=True)

df_sorted = df.sort_values([TICKET_COL, TIME_COL]).reset_index(drop=True)

def clean_activity(text):
    if not isinstance(text, str):
        return ""
    text = re.sub(r"TO\s*:.*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\[REDACTED[^\]]*\]", "", text)
    text = re.sub(r"TICKET RECEIVED:.*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"DESCRIPTION\s*:", "", text, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", text).strip()

df_sorted["ACTIVITYDESC_CLEAN"] = df_sorted[ACTIVITY_COL].apply(clean_activity)
df_sorted["ROLE"] = df_sorted.groupby(TICKET_COL).cumcount().apply(lambda x: "QUERY" if x == 0 else "RESOLUTION")

# Build QUERY and RESOLUTION columns
query_res_df = df_sorted.groupby(TICKET_COL).apply(
    lambda g: pd.Series({
        "QUERY": g.iloc[0]["ACTIVITYDESC_CLEAN"],
        "RESOLUTION": " || ".join(g.iloc[1:]["ACTIVITYDESC_CLEAN"])
    })
).reset_index()

# Save to Excel with auto-adjusted column width
with pd.ExcelWriter("Ticket_query_resolution.xlsx", engine="xlsxwriter") as writer:
    query_res_df.to_excel(writer, index=False, sheet_name="Summary")
    worksheet = writer.sheets["Summary"]
    worksheet.set_column("A:C", 50)  # widen columns for readability

