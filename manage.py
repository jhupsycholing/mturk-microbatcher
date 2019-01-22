from flask_script import Manager, Server
from flask_migrate import Migrate, MigrateCommand
from app import app, db

# Initializing the manager
manager = Manager(app)

# Initialize Flask Migrate
migrate = Migrate(app, db)

# Add the flask migrate
manager.add_command('db', MigrateCommand)
manager.add_command("runserver", Server())

# Run the manager
if __name__ == '__main__':
    manager.run()
