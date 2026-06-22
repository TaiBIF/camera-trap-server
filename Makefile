DATE := $(shell date +%y%m%d)

HOST ?= ct-prod

.PHONY: db-clear db-bak db-dump delete-folder

help: ## Show this help menu
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

db-clear: ## clear pgdata
	sudo rm -fr ../ct22-volumes/pgdata
	@echo "pgdata cleared."

db-dump: ## dump production database to local initdb
	@cd initdb && sudo rm -f *.gz
	ssh ct-prod "cd camera-trap-server;docker-compose -f compose.yml exec -T postgres pg_dump -U postgres cameratrap --compress=5 --no-owner -f /bucket/dump.sql.gz"
	scp ct-prod:~/ct22-volumes/bucket/dump.sql.gz initdb/dump-cameratrap-$(DATE).sql.gz
	ssh ct-prod "sudo rm -f ct22-volumes/bucket/dump.sql.gz"
	@echo "dump-cameratrap-$(DATE).sql.gz saved."

db-bak: ## bak inindb dump file
	sudo mv ./initdb/*.sql.gz .
	@echo "dump files moved to project root."

delete-folder: ## delete upload folder on remote. Usage: make delete-folder FOLDER=name [DRY_RUN=1] [HOST=ct-prod]
	@test -n "$(FOLDER)" || { echo "ERROR: FOLDER is required, e.g. make delete-folder FOLDER=some_folder"; exit 1; }
	ssh $(HOST) "cd camera-trap-server;docker-compose -f compose.yml exec -T django python scripts/delete_upload_folder.py $(if $(DRY_RUN),--dry-run )$(FOLDER)"
