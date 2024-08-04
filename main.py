import json
import http.client
import os
from pathlib import Path

import http.client
import json

# ANSI escape codes for colors
RED = "\033[31m"    # Red for errors
YELLOW = "\033[33m"  # Yellow for hints
GREEN = "\033[32m"  # Green for success
RESET = "\033[0m"   # Reset to default


def print_colored(message, color):
    print(f"{color}{message}{RESET}")

# Returns a list of all repos (json) of the user with the given token
# The token must have the repo scope
# The token must be stored in a file named "token" in the same directory as this script


def get_all_repos(token):
    conn = http.client.HTTPSConnection("api.github.com")
    headers = {
        'User-Agent': "github-archiver/1.0.0",
        'Authorization': "Bearer " + token,
    }

    repos = []
    url = "/user/repos?affiliation=owner"

    while url:
        conn.request("GET", url, headers=headers)
        res = conn.getresponse()
        data = res.read()
        text_data = data.decode("utf-8")
        repos.extend(json.loads(text_data))

        # Parse the Link header to find the next page URL
        link_header = res.getheader('Link')
        url = None
        if link_header:
            links = link_header.split(',')
            for link in links:
                if 'rel="next"' in link:
                    url = link[link.find('<') + 1:link.find('>')]
                    break

    return repos

# takes a json list of repos and clones them into specified directory


def clone_repos(json_data, directory="./cloned-repos"):
    # clone all repos into ./cloned-repos
    for repo in json_data:
        # check if repo is already cloned
        if os.path.exists(directory + "/" + repo['name']):
            print_colored("Repo " + repo['name'] + " already cloned", YELLOW)
            continue
        print("Cloning " + repo['name'])
        os.system("git clone " + repo['html_url'] +
                  " " + directory + "/" + repo['name'])
        print_colored("Cloned " + repo['name'], GREEN)

# cleanup function to remove git dir inside archived repositories


def cleanup(directory="./cloned-repos"):
    for root, dirs, files in os.walk(directory):
        for dir in dirs:
            if dir == ".git":
                # remove the .git directorys in cloned repos
                rmdir(os.path.join(root, dir))
                print_colored("Removed " + os.path.join(root, dir), GREEN)


def rmdir(directory: Path):
    print("Attempting to remove " + directory.__str__())
    directory = Path(directory)
    for item in directory.iterdir():
        try:
            if item.is_dir():
                rmdir(item)
            else:
                item.unlink()
        except Exception as e:
            print_colored("Error: " + e.__str__(), YELLOW)
            print_colored("Failed to remove " + item.__str__(), YELLOW)
            print("Trying to recover by changing permissions")
            os.chmod(item, 0o777)
            try:
                item.unlink()
                print("Recovered")
            except Exception as e:
                print_colored("Failed to recover: " + e.__str__(), RED)
                print_colored("Skipping this .git folder entirely...", RED)
                return
    directory.rmdir()


def main():
    token = ""
    directory = "./cloned-repos"
    # read token from ./token file
    with open('./token', 'r') as file:
        token = file.read().replace('\n', '')

    all_repos = get_all_repos(token)

    # print List all repos
    print_colored("List of all repos", YELLOW)
    for repo in all_repos:
        print(repo['name'] + ";" + repo['html_url'])

    # print repo count
    print_colored("Total repos: " + str(len(all_repos)), YELLOW)

    # ask user if they want to archive all repos
    print_colored("Do you want to archive all repos? (y/n)", YELLOW)
    if input() == "y":
        print_colored("Starting archiving process...", YELLOW)
        # clone all repos
        clone_repos(all_repos, directory)
        print_colored("All repos cloned; Starting cleanup", GREEN)
        # ask user for permission to delete .git directories in archived repositories
        if input("Do you want to delete .git directories in cloned repositories? (y/n)") == "y":
            cleanup(directory)
            print_colored("Cleanup done", GREEN)

        print_colored("Archiving done", GREEN)
        return


if (__name__ == "__main__"):
    main()
