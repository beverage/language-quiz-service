import asyncio
import boto3
import logging as log
import os
import time

from functools import partial

from src.cli.utils.console import Color, Style


def __cluster_display_name(cluster_name):
    return f"{Style.BOLD}{Color.BRIGHT_BLUE}{cluster_name}{Style.RESET}"


def __service_display_name(service_name):
    return f"{Style.BOLD}{Color.BRIGHT_BLUE}{service_name}{Style.RESET}"


async def check_cluster_and_service_exists(ecs, cluster_name=None, service_name=None):
    """
    Checks if the ECS service exists in the specified cluster.
    Returns True if the service exists, False otherwise.
    """
    cluster_response = await asyncio.get_running_loop().run_in_executor(
        None, partial(ecs.describe_clusters, clusters=[cluster_name])
    )

    cluster_display_name = __cluster_display_name(cluster_name)
    service_display_name = __service_display_name(service_name)

    if not cluster_response["clusters"]:
        log.error(f"Cluster {cluster_display_name} does not exist.")
        return False

    service_response = await asyncio.get_running_loop().run_in_executor(
        None,
        partial(ecs.describe_services, cluster=cluster_name, services=[service_name]),
    )

    if not service_response["services"]:
        log.error(
            f"Service {service_display_name} does not exist in cluster {cluster_display_name}."
        )
        return False

    return True


async def wait_for_service_status(ecs, cluster_name, service_name, task_count):
    """
    Waits for the ECS service to reach the target task count.
    """

    previous_time = time.monotonic()
    minutes = 0

    while True:
        service_status = await asyncio.get_running_loop().run_in_executor(
            None,
            partial(
                ecs.describe_services, cluster=cluster_name, services=[service_name]
            ),
        )

        if (
            service_status["services"][0]["desiredCount"] == task_count
            and service_status["services"][0]["runningCount"] == task_count
        ):
            print("")
            break

        if time.monotonic() - previous_time > 60:
            minutes += 1
            print(f"{minutes}m", end="", flush=True)
            previous_time = time.monotonic()
        else:
            print(".", end="", flush=True)

        await asyncio.sleep(5)


async def down():
    """
    Takes down the service by setting the ecs tasks desired count to 0.
    This will stop all running tasks and effectively shut down the service.
    """
    ecs = boto3.client("ecs")

    cluster_name = os.getenv("LQS_CLUSTER_NAME", "lqs-cluster")
    service_name = os.getenv("LQS_SERVICE_NAME", "lqs-service")

    if not await check_cluster_and_service_exists(
        ecs, cluster_name=cluster_name, service_name=service_name
    ):
        return

    cluster_display_name = __cluster_display_name(cluster_name)
    service_display_name = __service_display_name(service_name)

    down_response = await asyncio.get_running_loop().run_in_executor(
        None,
        partial(
            ecs.update_service,
            cluster=cluster_name,
            service=service_name,
            desiredCount=0,
        ),
    )

    log.info(
        f"Service {service_display_name} in cluster {cluster_display_name} is now set to 0 desired count. All tasks will be {Style.BOLD}{Color.STRONG_RED}stopped{Style.RESET}."
    )

    await wait_for_service_status(ecs, cluster_name, service_name, 0)

    log.info(
        f"Service {service_display_name} is now fully {Style.BOLD}{Color.STRONG_RED}stopped{Style.RESET}."
    )
    return down_response


async def up(count: int = 1):
    """
    Takes up the service by setting the ecs tasks desired count to the specified count.
    """
    ecs = boto3.client("ecs")

    cluster_name = os.getenv("LQS_CLUSTER_NAME", "lqs-cluster")
    service_name = os.getenv("LQS_SERVICE_NAME", "lqs-service")

    if not await check_cluster_and_service_exists(
        ecs, cluster_name=cluster_name, service_name=service_name
    ):
        return

    cluster_display_name = __cluster_display_name(cluster_name)
    service_display_name = __service_display_name(service_name)

    up_response = await asyncio.get_running_loop().run_in_executor(
        None,
        partial(
            ecs.update_service,
            cluster=cluster_name,
            service=service_name,
            desiredCount=count,
        ),
    )

    log.info(
        f"Service {service_display_name} in cluster {cluster_display_name} is now set with desired task count of {count}. Task will be {Style.BOLD}{Color.STRONG_GREEN}started{Style.RESET}."
    )

    await wait_for_service_status(ecs, cluster_name, service_name, count)

    log.info(
        f"Service {service_display_name} is now {Style.BOLD}{Color.STRONG_GREEN}running{Style.RESET} with {count} task(s)."
    )
    return up_response
