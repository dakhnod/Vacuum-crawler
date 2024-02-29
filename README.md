# Vacuum scrawler

This script uses shodan to automatically find Valetudo instances on the web and display a web controler interface,
including a "start all" button. May the force be with you.

## Usage

`docker run -p 5000:5000 --rm --env SHODAN_TOKEN=123xyz vacd`

You have to replace 123xyz with a valid Shodan API token.
For the API to work, you need to pay for shodan, or have an academic upgrade.

Then, you will be able to access the web interface via [http://localhost:5000](http://localhost:5000)