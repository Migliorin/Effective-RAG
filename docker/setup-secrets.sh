#!/bin/sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
TARGET_DIR="$SCRIPT_DIR/secrets"

umask 077

mkdir -p "$TARGET_DIR"
chmod 700 "$TARGET_DIR"

write_if_missing() {
 	target_file="$1"
  	content="$2"

  	if [ -f "$target_file" ]; then
  		echo "Mantido: $target_file"
  	  	return
  	fi

  	printf '%s\n' "$content" > "$target_file"
  	chmod 600 "$target_file"
  	echo "Criado: $target_file"
}

write_redis_acl() {
	target_file="$TARGET_DIR/redis_users.acl"
	
 	if [ -f "$target_file" ]; then
		echo "Mantido: $target_file"
		return
	fi

  	cat > "$target_file" <<EOF
user default off

user troque_backend_user on >troque_backend_password \
  ~auth:* ~ai:* ~jobs:* ~bull:* \
  +@read +@write +@connection +@list +@set +@hash +@string +@sortedset +@stream \
  -@dangerous -@admin

user troque_ai_user on >troque_ai_password \
  ~ai:* ~jobs:* ~bull:* \
  +@read +@write +@connection +@list +@set +@hash +@string +@sortedset +@stream \
  -@dangerous -@admin

EOF
  	chmod 644 "$target_file"
  	echo "Criado: $target_file"
}

write_qdrant_config(){
	target_file="$TARGET_DIR/qdrant-local.yaml"
	
 	if [ -f "$target_file" ]; then
		echo "Mantido: $target_file"
		return
	fi

	cat > "$target_file" <<EOF
service:
  api_key: "api-key"
EOF

  	chmod 600 "$target_file"
  	echo "Criado: $target_file"
}

write_if_missing "$TARGET_DIR/minio_root_user.txt" "minioadmin"
write_if_missing "$TARGET_DIR/minio_root_password.txt" "troque-esta-senha-root"
write_if_missing "$TARGET_DIR/minio_backend_access_key.txt" "backend-upload-user"
write_if_missing "$TARGET_DIR/minio_backend_secret_key.txt" "troque-esta-senha-backend"
write_if_missing "$TARGET_DIR/minio_ai_access_key.txt" "ai-reader-user"
write_if_missing "$TARGET_DIR/minio_ai_secret_key.txt" "troque-esta-senha-ia"
write_if_missing "$TARGET_DIR/postgres_root_user.txt" "postgres"
write_if_missing "$TARGET_DIR/postgres_root_password.txt" "troque-esta-senha-root"

write_redis_acl
write_qdrant_config

echo
echo "Revise os arquivos em $TARGET_DIR antes de subir o compose."
