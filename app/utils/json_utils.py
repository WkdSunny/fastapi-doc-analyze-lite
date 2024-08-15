import numpy as np
from pydantic import BaseModel

def serialize(data):
    """ Recursively convert data to make it JSON serializable, handling Pydantic models, numpy types, and other common structures. """
    if isinstance(data, dict):
        return {k: serialize(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [serialize(i) for i in data]
    elif isinstance(data, BaseModel):
        return serialize(data.dict())
    elif isinstance(data, np.generic):
        return data.item()  # Converts numpy types to native Python types
    elif isinstance(data, np.ndarray):
        return data.tolist()  # Converts numpy arrays to lists
    elif isinstance(data, (float, int, str, bool)) or data is None:
        return data  # No conversion needed for standard types
    else:
        raise TypeError(f"Type {type(data)} not serializable")

