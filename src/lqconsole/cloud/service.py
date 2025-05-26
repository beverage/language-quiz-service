import asyncio
import boto3
import logging as log
import os

from functools import partial

async def check_cluster_and_service_exists():
    """
    Checks if the ECS service exists in the specified cluster.
    Returns True if the service exists, False otherwise.
    """

    ecs = boto3.client('ecs')

    cluster_name = os.getenv("LQS_CLUSTER_NAME", "lqs-cluster")
    service_name = os.getenv("LQS_SERVICE_NAME", "lqs-service")

    loop = asyncio.get_running_loop()

    cluster_response = await loop.run_in_executor(None, partial(
        ecs.describe_clusters,
        clusters=[cluster_name]
    ))

    if not cluster_response['clusters']:
        log.error(f"Cluster {cluster_name} does not exist.")
        return False

    service_response = await loop.run_in_executor(None, partial(
        ecs.describe_services,
        cluster=cluster_name,
        services=[service_name]
    ))

    if not service_response['services']:
        log.error(f"Service {service_name} does not exist in cluster {cluster_name}.")
        return False

    return True


async def down():
    """
    Takes down the service by setting the ecs tasks desired count to 0.
    This will stop all running tasks and effectively shut down the service. 
    """

    if not await check_cluster_and_service_exists():
        return

    ecs = boto3.client('ecs')

    cluster_name = os.getenv("LQS_CLUSTER_NAME", "lqs-cluster")
    service_name = os.getenv("LQS_SERVICE_NAME", "lqs-service")

    loop = asyncio.get_running_loop()

    down_response = await loop.run_in_executor(None, partial(
        ecs.update_service,
        cluster=cluster_name,
        service=service_name,
        desiredCount=0
    ))

    log.info(f"Service {service_name} in cluster {cluster_name} is now set to 0 desired count. All tasks will be stopped.")

    while True:

        service_status = await loop.run_in_executor(None, partial(
            ecs.describe_services,
            cluster=cluster_name,
            services=[service_name]
        ))

        if service_status['services'][0]['desiredCount'] == 0 and service_status['services'][0]['runningCount'] == 0:
            break

        await asyncio.sleep(5)

    log.info(f"Service {service_name} is now fully stopped.")
    return down_response


async def up(count: int = 1):
    """
    Takes up the service by setting the ecs tasks desired count to the specified count.
    """

    if not await check_cluster_and_service_exists():
        return

    ecs = boto3.client('ecs')

    cluster_name = os.getenv("LQS_CLUSTER_NAME", "lqs-cluster")
    service_name = os.getenv("LQS_SERVICE_NAME", "lqs-service")

    loop = asyncio.get_running_loop()

    up_response = await loop.run_in_executor(None, partial(
        ecs.update_service,
        cluster=cluster_name,
        service=service_name,
        desiredCount=count
    ))

    log.info(f"Service {service_name} in cluster {cluster_name} is now set with desired task count of {count}. Task will be started.")

    while True:

        service_status = await loop.run_in_executor(None, partial(
            ecs.describe_services,
            cluster=cluster_name,
            services=[service_name]
        ))

        if service_status['services'][0]['desiredCount'] == count and service_status['services'][0]['runningCount'] == count:
            break

        await asyncio.sleep(5)

    log.info(f"Service {service_name} is now running with {count} task(s).")
    return up_response
