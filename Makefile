up:
	docker compose up --build -d postgres ai-service backend

down:
	docker compose down

logs:
	docker compose logs -f postgres ai-service backend

ps:
	docker compose ps

smoke:
	python3 scripts/smoke_test_im_agent.py
