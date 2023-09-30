import sys
import os
sys.path.insert(0,'/opt/envstats')

from dotenv import load_dotenv

from envstats import create_app

project_folder = os.path.expanduser('/opt/envstats')  # adjust as appropriate
load_dotenv(os.path.join(project_folder, '.env'))

application = create_app()


if __name__ == "__main__":
    app.run()
