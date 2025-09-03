import json
import re

# Input and output file paths
input_file = "d:\\projects\\lobot\\output.txt"
output_file = "d:\\projects\\lobot\\extracted_acts.json"

# Read the input file
with open(input_file, "r", encoding="utf-8") as f:
    content = f.read()

# Initialize variables
acts = []
seen_acts = set()

# Use regex to find all act entries in the format: "number. Name Year ActNumber"
# This pattern looks for: number followed by dot, then text, then 4-digit year, then act number
pattern = r'(\d+)\.\s+(.+?)\s+(\d{4})\s+(\d+\*?)'

matches = re.findall(pattern, content)

print(f"Found {len(matches)} potential matches with regex")

for match in matches:
    sno, name, year, act_no = match
    
    # Clean up the name (remove extra spaces, tabs, newlines)
    name = re.sub(r'\s+', ' ', name).strip()
    
    entry = {
        "S.No": sno,
        "Name": name,
        "Year": year,
        "Act No.": act_no
    }
    
    # Create a unique key for deduplication
    act_key = (entry["S.No"], entry["Name"], entry["Year"], entry["Act No."])
    if act_key not in seen_acts:
        acts.append(entry)
        seen_acts.add(act_key)

print(f"Extracted {len(acts)} unique acts after deduplication")

# If the regex approach didn't work well, try a line-by-line approach
if len(acts) < 100:  # Assuming there should be many more acts
    print("Regex approach yielded few results, trying line-by-line approach...")
    
    acts = []
    seen_acts = set()
    
    # Split into lines and process
    lines = [line.strip() for line in content.split('\n') if line.strip()]
    
    for line in lines:
        # Skip header lines and other non-data content
        if any(skip in line for skip in [
            "CHRONOLOGICALLISTOFCENTRALACTS",
            "S. No.",
            "Name of the Act", 
            "Year",
            "Act No.",
            "Spent Act.",
            "Repealed by Ordinance"
        ]):
            continue
            
        # Look for lines that start with number followed by dot
        match = re.match(r'^(\d+)\.\s+(.+)', line)
        if match:
            sno = match.group(1)
            rest = match.group(2).strip()
            
            # Try to extract year and act number from the end
            # Look for pattern: "... YYYY NN" or "... YYYY NN*"
            end_match = re.search(r'(.+?)\s+(\d{4})\s+(\d+\*?)$', rest)
            if end_match:
                name = end_match.group(1).strip()
                year = end_match.group(2)
                act_no = end_match.group(3)
                
                # Clean up the name
                name = re.sub(r'\s+', ' ', name)
                
                entry = {
                    "S.No": sno,
                    "Name": name,
                    "Year": year,
                    "Act No.": act_no
                }
                
                # Create a unique key for deduplication
                act_key = (entry["S.No"], entry["Name"], entry["Year"], entry["Act No."])
                if act_key not in seen_acts:
                    acts.append(entry)
                    seen_acts.add(act_key)

# Sort by serial number to ensure correct order
acts.sort(key=lambda x: int(x["S.No"]))

# Write the extracted acts to a JSON file
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(acts, f, indent=2, ensure_ascii=False)

print(f"\nFinal count: {len(acts)} unique acts saved to {output_file}")

# Print first few records to verify
print("\nFirst 10 records:")
for i, act in enumerate(acts[:10]):
    print(f"{act['S.No']}. {act['Name']} ({act['Year']}, {act['Act No.']})")

# Print last few records to verify
if len(acts) > 10:
    print("\nLast 5 records:")
    for act in acts[-5:]:
        print(f"{act['S.No']}. {act['Name']} ({act['Year']}, {act['Act No.']})")