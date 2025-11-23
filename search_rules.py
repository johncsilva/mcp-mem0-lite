import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
from server import search_memory, mem0, build_mem0
import server
if server.mem0 is None:
    server.mem0 = build_mem0()
result = search_memory(query='regras de programação', user_id='john')
print(result)