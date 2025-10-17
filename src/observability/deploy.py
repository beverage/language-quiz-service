"""Deploy dashboards to Grafana (local or cloud)."""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import requests
from grafana_foundation_sdk.cog.encoder import JSONEncoder

# Import dashboard generators
from .dashboards import service_overview


class GrafanaDeployer:
    """Deploy dashboards to Grafana."""

    def __init__(self, api_url: str, api_key: str, org_id: int = 1):
        """
        Initialize deployer.

        Args:
            api_url: Grafana API URL (e.g., http://localhost:3000 or https://yourinstance.grafana.net)
            api_key: Grafana API key
            org_id: Organization ID (default: 1 for local Grafana)
        """
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.org_id = org_id
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
        )

    def generate_dashboard_json(self, dashboard_builder: Any) -> dict:
        """
        Generate JSON from grafana-foundation-sdk dashboard builder.

        Args:
            dashboard_builder: grafana-foundation-sdk Dashboard builder

        Returns:
            Dashboard JSON dict
        """
        json_str = JSONEncoder(sort_keys=True, indent=2).encode(
            dashboard_builder.build()
        )
        dashboard_json = json.loads(json_str)

        # Fix for Grafana 10.x: Add 'definition' field to query variables
        if "templating" in dashboard_json and "list" in dashboard_json["templating"]:
            for var in dashboard_json["templating"]["list"]:
                if var.get("type") == "query" and "query" in var:
                    # Set definition to the same value as query for Grafana 10.x compatibility
                    var["definition"] = var["query"]

        return dashboard_json

    def deploy_dashboard(
        self,
        dashboard_builder: Any,
        folder_name: str = "General",
        overwrite: bool = True,
    ) -> dict:
        """
        Deploy a dashboard to Grafana.

        Args:
            dashboard_builder: grafana-foundation-sdk Dashboard builder
            folder_name: Folder to place dashboard in
            overwrite: Whether to overwrite existing dashboard

        Returns:
            API response dict
        """
        dashboard_json = self.generate_dashboard_json(dashboard_builder)

        # Prepare payload for Grafana API
        payload = {
            "dashboard": dashboard_json,
            "folderUid": None,  # Use folder_name instead
            "message": "Deployed via dashboard-as-code",
            "overwrite": overwrite,
        }

        # Get folder ID if not General
        if folder_name != "General":
            folder = self.get_or_create_folder(folder_name)
            payload["folderUid"] = folder["uid"]

        # Deploy dashboard
        response = self.session.post(
            f"{self.api_url}/api/dashboards/db",
            json=payload,
        )

        if response.status_code not in (200, 201):
            print(f"❌ Failed to deploy dashboard: {response.status_code}")
            print(f"   Response: {response.text}")
            response.raise_for_status()

        result = response.json()
        return result

    def get_or_create_folder(self, folder_name: str) -> dict:
        """
        Get or create a dashboard folder.

        Args:
            folder_name: Folder name

        Returns:
            Folder object with uid
        """
        # Search for existing folder
        response = self.session.get(
            f"{self.api_url}/api/folders",
        )

        if response.status_code == 200:
            folders = response.json()
            for folder in folders:
                if folder["title"] == folder_name:
                    return folder

        # Create folder if not exists
        payload = {"title": folder_name}
        response = self.session.post(
            f"{self.api_url}/api/folders",
            json=payload,
        )

        if response.status_code in (200, 201):
            return response.json()

        # If folder creation fails, use General folder
        print(f"⚠️  Could not create folder '{folder_name}', using General")
        return {"uid": None}

    def validate_connection(self) -> bool:
        """
        Validate connection to Grafana API.

        Returns:
            True if connection successful
        """
        try:
            response = self.session.get(f"{self.api_url}/api/health", timeout=10)
            if response.status_code == 200:
                return True
            else:
                print(f"❌ HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            print(f"   Attempted URL: {self.api_url}/api/health")
            return False


def detect_environment() -> dict[str, Any]:
    """
    Detect whether to deploy to local or cloud Grafana.

    Returns:
        Dict with api_url, api_key, environment
    """
    # Check for Grafana Cloud credentials
    cloud_instance = os.getenv("GRAFANA_CLOUD_INSTANCE_ID")
    cloud_api_key = os.getenv("GRAFANA_CLOUD_API_KEY")

    if cloud_instance and cloud_api_key:
        # Deploy to Grafana Cloud
        return {
            "environment": "cloud",
            "api_url": f"https://{cloud_instance}.grafana.net",
            "api_key": cloud_api_key,
            "org_id": 1,
        }
    else:
        # Deploy to local Grafana
        local_url = os.getenv("GRAFANA_URL", "http://localhost:3000")
        local_user = os.getenv("GRAFANA_USER", "lqs")
        local_password = os.getenv("GRAFANA_PASSWORD", "test")

        # For local, we need to get an API key or use basic auth
        # For simplicity, we'll create a service account token on first run
        # For now, use basic auth which grafanalib supports
        return {
            "environment": "local",
            "api_url": local_url,
            "api_key": "",  # Will use basic auth
            "username": local_user,
            "password": local_password,
        }


def get_local_deployer(config: dict) -> GrafanaDeployer:
    """
    Create deployer for local Grafana using basic auth.

    Args:
        config: Environment config

    Returns:
        Configured deployer
    """
    api_url = config["api_url"]
    username = config["username"]
    password = config["password"]

    # Create a special deployer that uses basic auth
    deployer = GrafanaDeployer(api_url=api_url, api_key="dummy")

    # Override session auth with basic auth
    deployer.session.auth = (username, password)
    deployer.session.headers.pop("Authorization", None)

    return deployer


def main():
    """Main deployment script."""
    parser = argparse.ArgumentParser(description="Deploy Grafana dashboards")
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Only validate dashboard JSON, don't deploy",
    )
    parser.add_argument(
        "--export",
        action="store_true",
        help="Export dashboard JSON to files",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./dashboards",
        help="Output directory for exported dashboards",
    )

    args = parser.parse_args()

    # Load dashboards
    dashboards = {
        "service_overview": service_overview.generate(),
    }

    # Validate mode
    if args.validate:
        print("🔍 Validating dashboard definitions...")
        for name, dashboard_builder in dashboards.items():
            try:
                json_str = JSONEncoder(sort_keys=True, indent=2).encode(
                    dashboard_builder.build()
                )
                json.loads(json_str)  # Validate JSON
                print(f"   ✅ {name}: Valid")
            except Exception as e:
                print(f"   ❌ {name}: Invalid - {e}")
                sys.exit(1)
        print("✅ All dashboards valid!")
        return

    # Export mode
    if args.export:
        print(f"📦 Exporting dashboards to {args.output_dir}/...")
        output_path = Path(args.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        for name, dashboard_builder in dashboards.items():
            json_data = JSONEncoder(sort_keys=True, indent=2).encode(
                dashboard_builder.build()
            )
            output_file = output_path / f"{name}.json"
            output_file.write_text(json_data)
            print(f"   ✅ Exported {name} → {output_file}")

        print("✅ Export complete!")
        return

    # Deploy mode
    print("🚀 Deploying dashboards...")

    # Detect environment
    config = detect_environment()
    print(f"   🌍 Environment: {config['environment']}")
    print(f"   🔗 API URL: {config['api_url']}")

    # Create deployer
    if config["environment"] == "local":
        deployer = get_local_deployer(config)
    else:
        deployer = GrafanaDeployer(
            api_url=config["api_url"],
            api_key=config["api_key"],
            org_id=config.get("org_id", 1),
        )

    # Validate connection
    print("   🔌 Testing connection...")
    if not deployer.validate_connection():
        print("❌ Failed to connect to Grafana API")
        sys.exit(1)

    print("   ✅ Connected!")

    # Deploy each dashboard
    folder_name = "Language Quiz Service"
    for name, dashboard_builder in dashboards.items():
        print(f"\n📊 Deploying {name}...")
        try:
            result = deployer.deploy_dashboard(
                dashboard_builder, folder_name=folder_name, overwrite=True
            )
            dashboard_url = f"{config['api_url']}{result.get('url', '')}"
            print("   ✅ Deployed successfully!")
            print(f"   🔗 URL: {dashboard_url}")
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            sys.exit(1)

    print("\n✨ All dashboards deployed successfully!")


if __name__ == "__main__":
    main()
