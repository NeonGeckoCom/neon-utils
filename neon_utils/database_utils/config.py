import os

from neon_utils.configuration_utils import KlatConfig
from neon_utils.database_utils.db_controller import DatabaseController


class KlatDBConfig(KlatConfig):
    """Extended base config class with support for database connection - related methods"""

    def get_db_config_from_key(self, key: str):
        """Gets DB configuration by key"""
        return self.config_data.get('DATABASE_CONFIG', {}).get(os.environ.get('SERVER_ENV', 'LOCALHOST'), {}).get(key,
                                                                                                                  {})

    def get_db_controller(self, name: str,
                          override: bool = False,
                          override_args: dict = None) -> DatabaseController:
        """
            Returns an new instance of Database Controller for specified dialect (creates new one if not present)

            :param name: db connection name from config
            :param override: to override existing instance under :param dialect (defaults to False)
            :param override_args: dict with arguments to override (optional)

            :returns instance of Database Controller
        """
        db_controller = self.db_controllers.get(name, None)
        if not db_controller or override:
            db_config = self.get_db_config_from_key(key=name)
            # Overriding with "override args" if needed
            if not override_args:
                override_args = {}
            db_config = {**db_config, **override_args}

            dialect = db_config.pop('dialect', None)
            if dialect:
                db_controller = DatabaseController(config_data=db_config)
                db_controller.attach_connector(dialect=dialect)
                db_controller.connect()
        return db_controller
