import os
import re

files_to_fix = [
    r"api/services/workflow/errors.py",
    r"api/services/configuration/check_validity.py",
    r"api/routes/s3_signed_url.py",
    r"api/routes/user.py",
    r"api/routes/integration.py"
]

for rel_path in files_to_fix:
    full_path = os.path.join(os.getcwd(), rel_path)
    if not os.path.exists(full_path):
        print(f"Skipping {rel_path} - not found")
        continue

    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Check if TypedDict is imported from typing
    if re.search(r"from typing import.*TypedDict", content):
        # Remove TypedDict from typing import
        new_content = re.sub(r"(from typing import.*),\s*TypedDict", r"\1", content)
        new_content = re.sub(r"(from typing import\s*)TypedDict,\s*", r"\1", new_content)
        new_content = re.sub(r"from typing import\s*TypedDict\s*\n", "", new_content)
        
        # Add typing_extensions import
        if "from typing_extensions import TypedDict" not in new_content:
            new_content = "from typing_extensions import TypedDict\n" + new_content
        
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Fixed TypedDict in {rel_path}")
    else:
        print(f"No standard TypedDict import found in {rel_path}")
