#!/bin/bash
# generate_fernet_key.sh: Generate and persist a Fernet key for NetRaven containers
FERNET_KEY_FILE="$(dirname "$0")/../fernet_key/fernet.key"

if [ -f "$FERNET_KEY_FILE" ]; then
    echo "Fernet key already exists: $(cat $FERNET_KEY_FILE)"
else
    KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    echo "$KEY" > "$FERNET_KEY_FILE"
    echo "Generated new Fernet key: $KEY"
fi

# Print the key for use in compose files or env
cat "$FERNET_KEY_FILE"
