import torch
import pandas as pd
from transformers import AutoTokenizer, AutoModelForCausalLM

# ---- Model load ----
MODEL_PATH = "./model"

tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    torch_dtype=torch.float16,
    device_map="auto",
    trust_remote_code=True
)

# ---- Resolution-only prompt ----
MASTER_PROMPT = """
You are a support assistant.

You will be given a RESOLUTION log from a support ticket.

Your task is to:
- Ignore ticket numbers, email signatures, metadata, and unrelated information.
- Extract only the meaningful actions taken and responses in the order they happened.
- Rewrite them clearly as a numbered step-by-step resolution flow.
- If helpful, add one short NOTE for additional context, this could include code or any other technical details (3-4 sentences max).
- Keep the entire response under 140 words.
Here's an example of how to respond:

Input:
A member of our team attempted to run notes this evening but received an error about posting to the GL. When I connected to ERP01, the F:\\ drive was full due to a 45GB file in F:\\csserver\\temp. We moved the file to another drive to free up space. Please review tomorrow.

Output:
1. Attempted to run notes, resulting in an error about posting to the GL.
2. Investigated and found that the ERP01 server F:\\ drive was full due to a 45GB file.
3. Moved the file to another drive to free up space.
4. Requested a follow-up review the next day.

NOTE: Disk space issues on the server likely caused the posting error. Recommend monitoring usage.

Now process the following input:

{RESOLUTION}

### Response:
"""
def make_prompt(resolution_text: str) -> str:
    return MASTER_PROMPT.replace("{RESOLUTION}", str(resolution_text or "").strip())

@torch.inference_mode()
def generate_flow(resolution_text: str, max_new_tokens: int = 160) -> str:
    prompt = make_prompt(resolution_text)
    inputs = tokenizer(prompt, return_tensors="pt")
    inputs = {k: v.to(model.device) for k, v in inputs.items()}

    outputs = model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        do_sample=False,
        temperature=0.0,
        pad_token_id=tokenizer.eos_token_id,
    )

    # Remove echo of prompt using input_ids slicing
    generated_ids = outputs[0][inputs["input_ids"].shape[-1]:]
    decoded = tokenizer.decode(generated_ids, skip_special_tokens=True).strip()

    # Optional: Stop at NOTE or after 6 steps
    if "NOTE:" in decoded:
        decoded = decoded.split("NOTE:")[0].strip() + "\nNOTE: " + decoded.split("NOTE:")[1].split("\n")[0]

    return decoded.strip()

def main():
    input_path = "Ticket_query_resolution.xlsx"
    out_path = "Ticker_resolution_flows.csv"

    df = pd.read_excel(input_path, dtype={"TICKETID": str})
    if "TICKETID" not in df.columns or "RESOLUTION" not in df.columns:
        raise ValueError("Input file must contain columns: 'TICKETID' and 'RESOLUTION'.")

    flows = []
    for _, row in df.iterrows():
        ticket_id = str(row["TICKETID"])
        raw_res = row["RESOLUTION"] if pd.notna(row["RESOLUTION"]) else ""
        flow_text = generate_flow(raw_res)
        flows.append({"TICKETID": ticket_id, "RESOLUTION_FLOW": flow_text})

    out_df = pd.DataFrame(flows, columns=["TICKETID", "RESOLUTION_FLOW"])
    out_df.to_csv(out_path, index=False)
    print(f"✅ Saved {len(out_df)} rows to {out_path}")

if __name__ == "__main__":
    main()
