import ujson

def read_json(filePath: str) -> dict:
    
    with open(filePath, 'r') as f:
        data = ujson.loads(f.read())
    
    return data


    