import asyncio
import boto3
import logging as log
import os
import time

from functools import partial

from cli.utils.console import Color, Style

async def get_rds_instance_status(rds, db_instance_identifier):
    """
    Retrieves the current status of the RDS instance.
    """
    response = await asyncio.get_event_loop().run_in_executor(
        None, partial(rds.describe_db_instances, DBInstanceIdentifier=db_instance_identifier)
    )
    return response['DBInstances'][0]['DBInstanceStatus']


async def wait_for_rds_status(rds, db_instance_identifier, target_status, status_display_style=""):
    """
    Waits for the RDS instance to reach the target status.
    """
    log.info(f"Waiting for {db_instance_identifier} to become {status_display_style}{target_status}{Style.RESET}...")

    previous_time = time.monotonic()
    minutes = 0
    
    while True:
        current_status = await get_rds_instance_status(rds, db_instance_identifier)

        if current_status == target_status:
            print('')
            log.info(f"RDS instance {db_instance_identifier} is now {status_display_style}{target_status}{Style.RESET}.")
            break

        if time.monotonic() - previous_time > 60:
            minutes += 1
            print(f"{minutes}m", end='', flush=True)
            previous_time = time.monotonic()
        else:
            print('.', end='', flush=True)

        await asyncio.sleep(5)


async def down():

    rds = boto3.client('rds')
    db_instance_identifier = os.getenv("LQS_DB", "lqs-1")

    log.info(f"Stopping RDS instance {db_instance_identifier}")

    current_status = await get_rds_instance_status(rds, db_instance_identifier)

    if current_status == 'available':
        stop_response = await asyncio.get_event_loop().run_in_executor(
            None, partial(rds.stop_db_instance, DBInstanceIdentifier=db_instance_identifier)
        )

        await wait_for_rds_status(rds, db_instance_identifier, 'stopped', f"{Style.BOLD}{Color.STRONG_RED}")
        return stop_response
    else:
        log.error(f"RDS instance {db_instance_identifier} is not in a state that can be stopped. Current status: {current_status}")
        return None


async def up():

    rds = boto3.client('rds')
    db_instance_identifier = os.getenv("LQS_DB", "lqs-1")

    log.info(f"Starting RDS instance {db_instance_identifier}")

    current_status = await get_rds_instance_status(rds, db_instance_identifier)

    if current_status == 'stopped':
        start_response = await asyncio.get_event_loop().run_in_executor(
            None, partial(rds.start_db_instance, DBInstanceIdentifier=db_instance_identifier)
        )

        await wait_for_rds_status(rds, db_instance_identifier, 'available', f"{Style.BOLD}{Color.STRONG_GREEN}")
        return start_response
    else:
        log.error(f"RDS instance {db_instance_identifier} is not in a state that can be started. Current status: {current_status}")
        return None

async def status():
    rds = boto3.client('rds')
    db_instance_identifier = os.getenv("LQS_DB", "lqs-1")
    status = await get_rds_instance_status(rds, db_instance_identifier)
    log.info(f"RDS instance {db_instance_identifier} is currently {status}.")
