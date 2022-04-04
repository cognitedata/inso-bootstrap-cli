from incubator.bootstrap_cli.__main__ import BootstrapCore
from dotenv import load_dotenv
import os, json

def main():
    config_file = "tests/example/config-deploy-bootstrap.yml"
    bootstrap = BootstrapCore(config_file)

    root_account='root'

    group_name, group_capabilities = bootstrap.generate_group_name_and_capabilities(
            root_account=root_account,
        )
    print(group_name, json.dumps(sorted(group_capabilities, key=lambda x: list(x.keys())[0]), indent=2))

if __name__ == "__main__":
    # dotenv_path = "/home/arwapet/.config/cdf/equinor-dev.env"
    # load_dotenv(dotenv_path=dotenv_path)
    # wrong env-variable names

    load_dotenv()

    # print('\n'.join([f'{k}: {v}' for k,v in os.environ.items()]))

    main()

