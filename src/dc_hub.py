from facepy import GraphAPI
import re
import os


def get_hub_add():
    graph = GraphAPI(os.environ['FB_ACCESS_TOKEN'])
    query = "hhfhkgp?fields=website"
    hub_website = graph.get(query)['website']
    x = re.search(r'\d+\.\d+\.\d+\.\d+', hub_website)
    return x.group()
