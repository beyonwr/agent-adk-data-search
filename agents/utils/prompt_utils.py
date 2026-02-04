import os
import yaml
import inspect

def get_prompt_yaml(tag, path=None):
    """
    Get prompt from yaml file
    Args:
        tag (str): the tag of the prompt. separate multiple tags with a dot (e.g., "tag1.tag2.tag3" )
        path (str): the path to the yaml file, default is prompt.yaml in the same directory as this script
    Returns:
        str: the prompt corresponding to the tag in the yaml file. If the tag does not exist, returns an empty string.
    """

    if path is None:
        caller_file = inspect.stack()[1].filename
        caller_dir = os.path.dirname(caller_file)
        path = os.path.join(caller_dir, "prompt.yaml")

    else:
        caller_file = inspect.stack()[1].filename
        caller_dir = os.path.dirname(caller_file)
        path = os.path.join(caller_dir, path)
        path = os.path.abspath(path)

    with open(path, "r", encoding='utr-8') as f:
        config = yaml.safe_load(f)

    keys = tag.split(".")
    current = config
    for key in keys:
        current = current.get(key, {})
    return current

    