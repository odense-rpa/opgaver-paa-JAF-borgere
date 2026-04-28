import asyncio
import logging
import sys
from datetime import datetime, timedelta, timezone, date

from automation_server_client import (
    AutomationServer,
    Workqueue,
    WorkItemError,
    Credential,
    WorkItemStatus,
)
from odk_tools.tracking import Tracker
from momentum_client.manager import MomentumClientManager

tracker: Tracker
momentum: MomentumClientManager
proces_navn = "Opgaver på JAF borgere"


async def populate_queue(workqueue: Workqueue):

    # sætter filtre op til at finde 6.7 borgere, der har startet i målgruppen indenfor 1600 og 1400 dage siden
    filters = [
        {
            "customFilter": "",
            "fieldName": "targetGroupCode",
            "values": [
                "6.7",
            ],
        },
        {
            "fieldName": "targetGroupStartDate",
            "values": [
                (datetime.now(timezone.utc) - timedelta(days=1600)).strftime(
                    "%Y-%m-%d %H:%M:%SZ"
                ),
                (datetime.now(timezone.utc) - timedelta(days=1400)).strftime(
                    "%Y-%m-%d %H:%M:%SZ"
                ),
                "false",
            ],
        },
    ]
    borgere = momentum.borgere.hent_borgere(filters=filters)
    for borger in borgere["data"]:
        borger_info = momentum.borgere.hent_borger(borger["cpr"])
        borgers_opgaver = momentum.opgaver.hent_opgaver(borger_info)
        specifik_opgave = next(
            (
                opgave
                for opgave in borgers_opgaver
                if opgave["title"]
                == "Forlæggelse for sundhedskoordinator senest om 4 mdr"
            ),
            None,
        )
        if not specifik_opgave:
            workqueue.add_item(
                data={
                    "cpr": borger["cpr"],
                    "målgruppe startdato": datetime.fromisoformat(
                        borger["targetGroupStartDate"]
                    ).strftime("%d-%m-%Y"),
                },
                reference=borger["cpr"],
            )
        print("hej")


async def process_workqueue(workqueue: Workqueue):

    for item in workqueue:
        with item:
            data = item.data  # Item data deserialized from json as dict

            try:
                borger = momentum.borgere.hent_borger(data["cpr"])
                primær_aktør = next(
                    (
                        aktør
                        for aktør in borger["responsibleActors"]
                        if aktør["role"] == 1
                    ),
                    None,
                )
                if not primær_aktør:
                    raise WorkItemError("Ingen primær aktør fundet for borger")

                primær_aktør = momentum.borgere.hent_aktør(primær_aktør["actorId"])
                email_initialer = (
                    primær_aktør["email"].split("@")[0]
                    if primær_aktør.get("email")
                    else None
                )
                sagsbehandler = momentum.borgere.hent_sagsbehandler(email_initialer)

                if not sagsbehandler:
                    raise WorkItemError("Ingen sagsbehandler fundet for primær aktør")

                # Lav sagsbehandler om til passende type for opgaveoprettelse
                medarbejdere = [sagsbehandler]

                opgave = momentum.opgaver.opret_opgave(
                    borger=borger,
                    medarbejdere=medarbejdere,
                    forfaldsdato=datetime.strptime(
                        data["målgruppe startdato"], "%d-%m-%Y"
                    )
                    + timedelta(days=1160),
                    titel="Forlæggelse for sundhedskoordinator senest om 4 mdr",
                    beskrivelse="",
                )

                tracker.track_task(process_name=proces_navn)

            except Exception as e:
                item.fail(str(e))


if __name__ == "__main__":
    ats = AutomationServer.from_environment()
    workqueue = ats.workqueue()

    # Initialize external systems for automation here..
    tracking_credential = Credential.get_credential("Odense SQL Server")
    momentum_credential = Credential.get_credential("Momentum - produktion")
    # momentum_credential = Credential.get_credential("Momentum - edu")

    tracker = Tracker(
        username=tracking_credential.username, password=tracking_credential.password
    )

    momentum = MomentumClientManager(
        base_url=momentum_credential.data["base_url"],
        client_id=momentum_credential.username,
        client_secret=momentum_credential.password,
        api_key=momentum_credential.data["api_key"],
        resource=momentum_credential.data["resource"],
    )

    # Queue management
    if "--queue" in sys.argv:
        workqueue.clear_workqueue(WorkItemStatus.NEW)
        asyncio.run(populate_queue(workqueue))
        exit(0)

    # Process workqueue
    asyncio.run(process_workqueue(workqueue))
