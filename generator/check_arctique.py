import yaml

fm = yaml.safe_load(open('../geographie/policy_reform.md', encoding='utf-8').read().split('---')[1])
for z in fm.get('zones', []):
    for o in (z.get('origine_reelle') or []):
        if isinstance(o, dict) and 'arctique' in o.get('entite', '').lower():
            print(f"{z['slug']} (niveau {z.get('niveau')}) -> {o.get('entite')!r}")
