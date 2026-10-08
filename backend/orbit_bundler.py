import os
import re
from datetime import datetime

# ==========================================
# IDENTITY: The Architect / The Scribe
# FILEPATH: orbit_bundler.py
# COMPONENT: Project Infrastructure
# ROLE: The "Big Bang" script. Compiles all project files into a single context 
#       snapshot for AI interaction.
# VERSION: 1.1.0
# SYSTEM VERSION: Backend v3.1.0
# VIBE: The historian of your Life-OS. No cap, this keeps the context window clean.
# ==========================================

# --- CONFIGURATION ---
OUTPUT_FILENAME = "Trace_backend_SNAPSHOT.txt"
PROJECT_DIRECTORIES = ["backend", "android", "Pocket_Orbit", "workstation", "infrastructure", "."]

ALLOWED_EXTENSIONS = {
    '.py', '.kt', '.xml', '.yml', '.yaml', '.txt', '.css', '.tsx', '.ts', '.js',
    '.md', '.sql', '.gradle', '.kts', '.ini', '.conf', '.dockerfile'
}

IGNORE_DIRS = {
    '.git', '__pycache__', 'build', '.gradle', 'node_modules', 
    '.venv', 'venv', '.idea', 'bin', 'obj', 'outputs', 'intermediates'
}

# --- AI PROTOCOL CONSTANTS ---
# Using distinct symbols that are unlikely to appear in code logic
START_DELIMITER = ">>>--- START_FILE_BLOCK: "
END_DELIMITER = " <<<--- END_FILE_BLOCK: "

AI_INSTRUCTIONS_TEMPLATE = """
================================================================================
SYSTEM INSTRUCTIONS FOR PROJECT ORBIT (THE JARVIS PROTOCOL)
================================================================================
DATE: {timestamp}
STATUS: VERSION 3.1 (STABILITY UPGRADE)

INSTRUCTIONS FOR THE AI ASSISTANT:
1. SINGLE SOURCE OF TRUTH: This snapshot is the Holy Grail. Use it for all context.
2. EDIT PROTOCOL: 
   - State the target file path clearly.
   - Maintain the header Identity as this is what I use to distinguish between files.
   - Increment VERSION (Major.Minor.Patch) in the IDENTITY header for each file.
   - For files > 700 lines, use the "DIFF" approach (10 lines context).
3. DELIMITER AWARENESS: Files are wrapped in unique delimiters:
   {start_delim}[path] and {end_delim}[path].
   Use these to anchor your parsing and avoid "fumbling" lines.
4. VIBE CHECK: Maintain all comments, imports, and docstrings. No "creative deletion."
5. PROJECT STRUCTURE: Refer to the FILE MANIFEST below for the full architecture.

================================================================================
FILE MANIFEST (TABLE OF CONTENTS)
================================================================================
{manifest}

================================================================================
FULL PROJECT CONTENT BEGINS BELOW
================================================================================
"""

def extract_versions(content):
    """Extracts versioning data using regex."""
    f_match = re.search(r"VERSION:\s*(\d+\.\d+\.\d+)", content)
    file_version = f_match.group(1) if f_match else "1.0.0"
    
    s_match = re.search(r"SYSTEM VERSION:\s*([\w\s]+v\d+\.\d+\.\d+)", content)
    system_version = s_match.group(1) if s_match else "N/A"
    
    return file_version, system_version

def get_file_list():
    """Walks the directories and returns a list of valid files."""
    valid_files = []
    root_dir = os.getcwd()
    
    for target_dir in PROJECT_DIRECTORIES:
        target_path = os.path.join(root_dir, target_dir)
        if not os.path.exists(target_path):
            continue
            
        for root, dirs, files in os.walk(target_path):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            for file in files:
                if file == OUTPUT_FILENAME or file == "orbit_bundler.py":
                    continue
                
                ext = os.path.splitext(file)[1].lower()
                if file.lower() == "dockerfile" or ext in ALLOWED_EXTENSIONS:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, root_dir)
                    if rel_path not in [f['rel_path'] for f in valid_files]:
                        valid_files.append({'rel_path': rel_path, 'full_path': full_path})
    return valid_files

def bundle_project():
    print(f"🚀 Launching Orbit Bundler v1.1.0... Target: {OUTPUT_FILENAME}")
    
    files_to_bundle = get_file_list()
    manifest_lines = []
    
    # Prepare Manifest and Content
    content_blocks = []
    
    for file_info in files_to_bundle:
        try:
            with open(file_info['full_path'], "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            
            f_version, s_version = extract_versions(content)
            manifest_lines.append(f"- {file_info['rel_path']} [v{f_version}]")
            
            # Construct the Block
            block = f"\n{START_DELIMITER}{file_info['rel_path']}\n"
            block += f"{'#'*80}\n"
            block += f"FILE: {file_info['rel_path']}\n"
            block += f"VERSION: {f_version} | SYSTEM: {s_version}\n"
            block += f"{'#'*80}\n\n"
            block += content
            block += f"\n\n{END_DELIMITER}{file_info['rel_path']}\n"
            
            content_blocks.append(block)
            print(f"✅ Indexed: {file_info['rel_path']}")
        except Exception as e:
            print(f"❌ Failed to read {file_info['rel_path']}: {e}")

    # Write everything
    with open(OUTPUT_FILENAME, "w", encoding="utf-8") as snapshot:
        header = AI_INSTRUCTIONS_TEMPLATE.format(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            manifest="\n".join(manifest_lines),
            start_delim=START_DELIMITER,
            end_delim=END_DELIMITER
        )
        snapshot.write(header.strip() + "\n")
        for block in content_blocks:
            snapshot.write(block)

    print(f"\n✨ Manifested {len(content_blocks)} files into {OUTPUT_FILENAME}")
    print("📈 The context is secured. AI is now fully operational.")

if __name__ == "__main__":
    bundle_project()
