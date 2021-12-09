# Health check bot

Welcome to Health check bot 👋!! I'm a python bot for telegram which intends to implement a (very basic) healthcheck
system.

## Available commands

### list
List all polling services
```
/list
```

### add
Add new service to the polling list
```
/add <service_type> <name> <domain> <port>
```

### remove
Unsubscribe a service from the polling list by name
```
/remove <name>
```

## Environment parameters

| Key                 | example value | Description                                                                  | 
|---------------------|---------------|------------------------------------------------------------------------------|
| BOT_TOKEN           | 1234:abcde    | Bot token obtained by Bot father                                             |
| ALLOW_LIST_CHAT_IDS | 1234,5678     | A comma-separated list for allow list groups which can interact with the bot |
| POLLING_INTERVAL    | 60            | The polling interval                                                         |
| LOG_LEVEL           | INFO          | Log level of the application                                                 |
