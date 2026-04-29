import sys
print("Script started", file=sys.stderr)

from app.db.supabase_client import get_supabase
print("Got supabase client", file=sys.stderr)

supabase = get_supabase()
print("Supabase initialized", file=sys.stderr)

# 1. 查询所有表名
try:
    r = supabase.table('pg_tables').select('tablename').eq('schemaname', 'public').execute()
    print('Public tables:', [x['tablename'] for x in r.data])
except Exception as e:
    print('List tables error:', e)

# 2. 查询 scene_object_manual
try:
    r = supabase.table('scene_object_manual').select('*').limit(5).execute()
    print('scene_object_manual rows:', len(r.data))
    if r.data:
        print('First row keys:', list(r.data[0].keys()))
        print('First row:', r.data[0])
except Exception as e:
    print('Query scene_object_manual error:', e)
