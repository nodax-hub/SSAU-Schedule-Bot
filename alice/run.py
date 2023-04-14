from pprint import pprint

import index

request = {
    "meta": {
        "client_id": "ru.yandex.searchplugin/7.16 (none none; android 4.4.2)",
        "interfaces": {
            "account_linking": {},
            "payments": {},
            "screen": {}
        },
        "locale": "ru-RU",
        "timezone": "UTC"
    },
    "request": {
        "original_utterance": "",
        "command": "",
        "nlu": {
            "entities": [],
            "tokens": [],
            "intents": {}
        },
        "markup": {
            "dangerous_context": False
        },
        "type": "SimpleUtterance"
    },
    "session": {
        "message_id": 0,
        "new": True,
        "session_id": "ea6be08d-9794-4ae2-89e2-e94f6734cc65",
        "skill_id": "a8f78148-8184-4010-b508-ec70badddf82",
        "user_id": "94748746704CDF263F766BC5E1F0F9D68CD6DB739F2E7CCEF975EC7FCF2A9666",
        "user": {
            "user_id": "86507D953A1790E1F26F46ED4874098F7BC2658CFC9588F9CCC3E1DD9C061A95"
        },
        "application": {
            "application_id": "94748746704CDF263F766BC5E1F0F9D68CD6DB739F2E7CCEF975EC7FCF2A9666"
        }
    },
    "state": {
        "session": {},
        "user": {},
        "application": {}
    },
    "version": "1.0"
}


class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def main():
    while True:
        response = index.handler(request, None)

        print(f'{Colors.GREEN}{Colors.BOLD}Response:{Colors.END}')
        pprint(response)
        print()

        print(f'{Colors.GREEN}{Colors.BOLD}Request:{Colors.END}')
        pprint(request)
        print()

        if response['user_state_update']:
            request['state']['user'] |= response['user_state_update']
        request["request"]["original_utterance"] = input(">")


if __name__ == '__main__':
    main()
