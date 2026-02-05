import asyncio
import json
import logging
import re
import aiohttp

def parse_json_code_block(test: str): 
    """
    Finds and parses a JSON object from a string
    wrapped in a ```json ... ``` code block.json

    Args:
        text: The input string containing the code block.

    Returns:
        The parsed Python object (dict or list) if successful.
        Returns None if no matching block is found or if
        the content is not valid JSON.
    """

    pattern = re.compile(r"```json(.*?)```", re.DOTALL)

    match = pattern.search(text)

    if match:
        json_string = match.group(1)

        json_string = json_string.strip()

        if not json_string:
            return None

        try:
            return json.loads(json_string)
        except json.JSONDecodeError:
            logging.debug(
                f"Error: Found ```json block, but content was not valid JSON."
            )
            return None

    return None


async def post_single_url_async(session, url, payload):
    """
    Sends a single POST request asynchronously.
    """
    logging.debug(f"Starting to POST payload {payload=} to {url}...")
    try:
        async with session.post(url, json=payload, timeout=10) as response:
            response.raise_for_status()

            logging.debug(f"Finished data for {payload['id']=} {data=}")

            return payload, data 

    except Exception as e:
        logging.debug(f"Error posting payload id={payload['id']: {e}}")
        return payload, {"error": str(e)}


async def post_parallel_async(url, payloads):
    """
    Manages the parallel POST requests using asyncio.
    """
    async with aiohttp.ClientSession() as session:

        tasks=[]
        for payload in payloads:
            tasks.append(post_single_url_async(session, url, payload))

        results = await asyncio.gather(*tasks)
        return results

    