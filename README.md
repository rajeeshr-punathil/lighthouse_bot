# LighthouseBot

A telegram bot to find the nearest lighthouse. 
You will be asked to choose the **country** and **state** and then **your location**.
Bot will then send you the location of the lighthouse nearest to you.
Currently supported __Kerala/India__ only.

## How to setup:

* Download or pull this source code to the desired path.

* Move to the root directory of this codebase. (To Where the script `lighhouse_bot.py` is).

* Create a virtual environment and activate it, if required.

  ```shell
  $ python -m venv /DESIRED/PATH/TO/YOUR/VENV
  $ source /DESIRED/PATH/TO/YOUR/VENV/bin/activate
  ```

* Install the dependencies:

  ```shell
  $ pip install -r requirements.txt
  ```

* Create a `.env` file there with the following content:

  ```shell
  TELEGRAM_TOKEN="REPLACE_THIS_STRING_WITH_YOUR_ACTUAL_TOKEN"
  ```

* Create a `.data` directory and copy data files, `lighthouses.json` and `countries.json`, there.

* Run the script, `lighthouse_bot.py` now:

  ```shell
  $ python lighthouse_bot.py
  ```
