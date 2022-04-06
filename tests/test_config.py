from incubator.bootstrap_cli.__main__ import BootstrapCore
from dotenv import load_dotenv
import json


def main():
    config_file = "tests/example/config-deploy-bootstrap.yml"
    bootstrap = BootstrapCore(config_file)
    bootstrap.load_deployed_config_from_cdf()

    print(bootstrap.deployed["datasets"])

    root_account = "root"
    group_name, group_capabilities = bootstrap.generate_group_name_and_capabilities(
        root_account=root_account,
    )
    # sort capabilities by key
    print(group_name, json.dumps(sorted(group_capabilities, key=lambda x: list(x.keys())[0]), indent=2))

    print("=" * 80)

    action = "read"
    group_ns = "src"
    group_core = "src:001:sap"
    group_name, group_capabilities = bootstrap.generate_group_name_and_capabilities(
        action=action,
        group_ns=group_ns,
        group_core=group_core,
    )

    # sort capabilities by key
    print(group_name, json.dumps(sorted(group_capabilities, key=lambda x: list(x.keys())[0]), indent=2))

    print("=" * 80)

    action = "owner"
    group_ns = "src"
    group_name, group_capabilities = bootstrap.generate_group_name_and_capabilities(
        action=action,
        group_ns=group_ns,
    )

    # sort capabilities by key
    print(group_name, json.dumps(sorted(group_capabilities, key=lambda x: list(x.keys())[0]), indent=2))


if __name__ == "__main__":
    # dotenv_path = "/home/arwapet/.config/cdf/equinor-dev.env"
    # load_dotenv(dotenv_path=dotenv_path)
    # wrong env-variable names

    load_dotenv()

    # print('\n'.join([f'{k}: {v}' for k,v in os.environ.items()]))

    main()
