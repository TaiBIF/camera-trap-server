"""Slack Bolt entrypoint — Socket Mode (no public URL required)."""
import logging
import os
import threading

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from commands import HANDLERS

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger('slack_bot')

app = App(token=os.environ['SLACK_BOT_TOKEN'])

ALLOWED_CHANNELS = {
    c.strip() for c in os.environ.get('ALLOWED_CHANNEL_IDS', '').split(',') if c.strip()
}


def _register(cmd_name: str):
    handler = HANDLERS[cmd_name]

    @app.command(cmd_name)
    def _run(ack, respond, command):
        ack()
        channel_id = command.get('channel_id', '')
        channel_name = command.get('channel_name', '?')
        user = command.get('user_name', '?')
        text = command.get('text', '')

        if ALLOWED_CHANNELS and channel_id not in ALLOWED_CHANNELS:
            log.info('blocked cmd=%s user=%s channel=%s (%s)',
                     cmd_name, user, channel_id, channel_name)
            respond({
                'response_type': 'ephemeral',
                'text': f':no_entry: 本指令僅能在指定頻道使用。',
            })
            return

        log.info('cmd=%s user=%s channel=%s text=%r',
                 cmd_name, user, channel_name, text)

        def _work():
            try:
                reply = handler(text)
            except Exception as exc:
                log.exception('handler failed for %s', cmd_name)
                reply = f':warning: 發生錯誤：`{exc}`'
            respond({'response_type': 'ephemeral', 'text': reply})

        threading.Thread(target=_work, daemon=True).start()


for _cmd in HANDLERS:
    _register(_cmd)


if __name__ == '__main__':
    SocketModeHandler(app, os.environ['SLACK_APP_TOKEN']).start()
