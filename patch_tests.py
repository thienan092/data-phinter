import sys
import re

with open('tests/test_default_data_api.py', encoding='utf-8') as f:
    content = f.read()

# Replace all config path mock with WORKSPACE_PATH mock
content = re.sub(r'patch\.object\(app_module, "(DEFAULT_DATA_CONFIG|CANDIDATE_DATA_CONFIG|VERIFICATION_CONFIG)", (config_path|default_config|verification_config)\)', r'patch.object(app_module, "WORKSPACE_PATH", root)', content)

# Remove duplicate patches
content = re.sub(r'patch\.object\(app_module, "WORKSPACE_PATH", root\), \\\n\s*patch\.object\(app_module, "WORKSPACE_PATH", root\)', r'patch.object(app_module, "WORKSPACE_PATH", root)', content)
content = re.sub(r'patch\.object\(app_module, "WORKSPACE_PATH", root\), \\\n\s*patch\.object\(app_module, "WORKSPACE_PATH", root\)', r'patch.object(app_module, "WORKSPACE_PATH", root)', content)

# Change current.csv to default.csv
content = content.replace('"current.csv"', '"default.csv"')
content = content.replace('X-Default-Data-Name"], "current.csv"', 'X-Default-Data-Name"], "default.csv"')

# Change current-verification.json to verification.json
content = content.replace('"current-verification.json"', '"verification.json"')

with open('tests/test_default_data_api.py', 'w', encoding='utf-8') as f:
    f.write(content)
