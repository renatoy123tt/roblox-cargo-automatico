
import os
import json
import requests

GROUP_ID = "243489775"
ROLE_NAME = "[ST] Subtenente"

API_KEY = os.environ["ROBLOX_API_KEY"]

BASE = "https://apis.roblox.com/cloud/v2"

session = requests.Session()
session.headers.update({
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
})

STATE_FILE = "seen_memberships.json"


def get_pages(endpoint, field, page_size):
    results = []
    params = {"maxPageSize": page_size}

    while True:
        response = session.get(
            f"{BASE}{endpoint}",
            params=params,
            timeout=30
        )
        response.raise_for_status()

        data = response.json()
        results.extend(data.get(field, []))

        token = data.get("nextPageToken")
        if not token:
            break

        params["pageToken"] = token

    return results


def find_role():
    roles = get_pages(
        f"/groups/{GROUP_ID}/roles",
        "groupRoles",
        20
    )

    for role in roles:
        if role.get("displayName") == ROLE_NAME:
            return role["path"]

    raise RuntimeError("Cargo não encontrado!")


def get_members():
    return get_pages(
        f"/groups/{GROUP_ID}/memberships",
        "groupMemberships",
        100
    )


def save_state(seen):
    with open(STATE_FILE, "w") as file:
        json.dump(sorted(seen), file)


def assign_role(membership, role_path):
    membership_id = membership["path"].split("/")[-1]

    url = (
        f"{BASE}/groups/{GROUP_ID}/memberships/"
        f"{membership_id}:assignRole"
    )

    response = session.post(
        url,
        json={"role": role_path},
        timeout=30
    )
    response.raise_for_status()


def main():
    role_path = find_role()
    members = get_members()

    # Primeira execução: registra os membros existentes.
    if not os.path.exists(STATE_FILE):
        seen = {m["path"] for m in members}
        save_state(seen)
        print("Lista inicial registrada!")
        return

    with open(STATE_FILE, "r") as file:
        seen = set(json.load(file))

    for member in members:
        membership_path = member["path"]

        if membership_path in seen:
            continue

        try:
            assign_role(member, role_path)

            seen.add(membership_path)
            save_state(seen)

            print("Cargo atribuído:", member["user"])

        except requests.RequestException as error:
            print("Falha ao atribuir cargo:", error)

    save_state(seen)


if __name__ == "__main__":
    main()
